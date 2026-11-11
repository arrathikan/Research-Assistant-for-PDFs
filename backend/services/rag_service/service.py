"""Conversation isolation, atomic turn records and the evaluation entrypoint."""

from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

from backend.services.rag_service.chain import answer_with_trace
from backend.services.rag_service.models import (
    ChatRequest,
    ChatResponse,
    PipelineOutput,
    RagConflict,
    RetrievalScope,
)
from backend.services.rag_service.retrieval import current_scope, retrieve
from backend.services.summary_service.workflow import Completion
from backend.shared.config import Settings
from backend.shared.database import StorageUnavailable
from backend.shared.storage import DocumentNotFound
from pydantic import BaseModel
from pymongo import ReturnDocument
from pymongo.database import Database
from pymongo.errors import PyMongoError


class SavedTurn(BaseModel):
    question: str
    response: ChatResponse
    created_at: datetime


class ChatHistory(BaseModel):
    document_id: str
    conversation_id: str
    turns: list[SavedTurn]


def _now() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(microsecond=now.microsecond // 1000 * 1000)


def _conversation(database: Database, scope: RetrievalScope, conversation_id: str) -> dict:
    record = database.chat_conversations.find_one(
        {"_id": conversation_id, "document_id": scope.document_id}
    )
    if record is None:
        raise DocumentNotFound("Conversation not found for this document")
    if record.get("scope") != scope.model_dump():
        raise RagConflict("Document generation changed; start a new conversation")
    return record


def _turns(
    database: Database, scope: RetrievalScope, conversation_id: str, limit: int
) -> list[SavedTurn]:
    records = list(
        database.chat_turns.find({**scope.model_dump(), "conversation_id": conversation_id})
        .sort("sequence", -1)
        .limit(limit)
    )
    turns = []
    for record in reversed(records):
        turn = SavedTurn.model_validate(record)
        if (
            turn.response.document_id != scope.document_id
            or turn.response.conversation_id != conversation_id
        ):
            raise StorageUnavailable("Stored conversation attribution is invalid")
        turns.append(turn)
    return turns


def read_history(
    database: Database, document_id: str, conversation_id: str, settings: Settings
) -> ChatHistory:
    try:
        scope, _ = current_scope(database, document_id, settings)
        _conversation(database, scope, conversation_id)
        result = ChatHistory(
            document_id=scope.document_id,
            conversation_id=conversation_id,
            turns=_turns(database, scope, conversation_id, 100),
        )
        after, _ = current_scope(database, document_id, settings)
        if after != scope:
            raise RagConflict("Document changed while reading conversation history")
        return result
    except PyMongoError:
        raise StorageUnavailable("Chat history unavailable") from None


def chat_with_trace(
    database: Database,
    document_id: str,
    request: ChatRequest,
    settings: Settings,
    complete: Completion | None = None,
) -> PipelineOutput:
    """The real request path, also used by offline evaluation; no Ragas here."""
    started = perf_counter()
    try:
        scope, _ = current_scope(database, document_id, settings)
        database.chat_turns.create_index(
            [("document_id", 1), ("conversation_id", 1), ("sequence", -1)],
            name="document_conversation_turns",
        )
        conversation_id = request.conversation_id or uuid4().hex
        turn_id = uuid4().hex
        if request.conversation_id:
            _conversation(database, scope, conversation_id)
        else:
            database.chat_conversations.insert_one(
                {
                    "_id": conversation_id,
                    "document_id": scope.document_id,
                    "scope": scope.model_dump(),
                    "created_at": _now(),
                }
            )
        claim = database.chat_conversations.find_one_and_update(
            {
                "_id": conversation_id,
                "document_id": scope.document_id,
                "active_turn_id": {"$exists": False},
            },
            {"$set": {"active_turn_id": turn_id}, "$inc": {"sequence": 1}},
            return_document=ReturnDocument.AFTER,
        )
        if claim is None:
            raise RagConflict("A response is already being generated for this conversation")
        try:
            history = (
                _turns(database, scope, conversation_id, settings.rag_history_turns)
                if settings.rag_history_turns
                else []
            )
            retrieved_scope, hits = retrieve(database, document_id, request.message, settings)
            if retrieved_scope != scope:
                raise RagConflict("Document changed before answer generation")
            output = answer_with_trace(
                request.message,
                scope,
                hits,
                settings,
                conversation_id,
                turn_id,
                history=[
                    {"question": turn.question, "answer": turn.response.answer} for turn in history
                ],
                complete=complete,
            )
            after, _ = current_scope(database, document_id, settings)
            if after != scope:
                raise RagConflict("Document changed during answer generation")
            output.trace.latency_ms = (perf_counter() - started) * 1000
            database.chat_turns.insert_one(
                {
                    "_id": turn_id,
                    **scope.model_dump(),
                    "conversation_id": conversation_id,
                    "sequence": claim["sequence"],
                    "question": request.message,
                    "response": output.response.model_dump(),
                    "trace": output.trace.model_dump(),
                    "created_at": _now(),
                }
            )
            after, _ = current_scope(database, document_id, settings)
            if after != scope:
                raise RagConflict("Document changed before returning the answer")
            return output
        finally:
            database.chat_conversations.update_one(
                {"_id": conversation_id, "active_turn_id": turn_id},
                {"$unset": {"active_turn_id": ""}},
            )
    except PyMongoError:
        raise StorageUnavailable("Chat processing/storage unavailable") from None
