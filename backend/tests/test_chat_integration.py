"""Real Mongo conversations with deterministic retrieval/model boundaries."""

import json
from unittest.mock import Mock, patch

import pytest
from backend.services.document_processor.embedding_storage import embed_stored_document
from backend.services.rag_service.models import (
    ChatRequest,
    RagConflict,
    RagNotReady,
    RagUnavailable,
    RetrievalHit,
)
from backend.services.rag_service.retrieval import current_scope
from backend.services.rag_service.service import chat_with_trace, read_history
from backend.shared.config import Settings
from backend.shared.storage import DocumentNotFound
from backend.tests.test_chunking_integration import database as mongo_database
from backend.tests.test_embedding_integration import prepare, vectors
from bson import ObjectId

pytestmark = pytest.mark.integration
SETTINGS = Settings(_env_file=None, voyage_api_key="synthetic-key")


@pytest.fixture
def database():
    yield from mongo_database.__wrapped__()


def seed(database):
    identifier, chunks = prepare(database, SETTINGS)
    with patch(
        "backend.services.document_processor.embedding_storage.embed_documents", side_effect=vectors
    ):
        embed_stored_document(database, identifier, SETTINGS)
    scope, _ = current_scope(database, identifier, SETTINGS)
    return identifier, scope, [RetrievalHit(chunk=chunk) for chunk in chunks]


def completion(system, prompt, schema):
    record = json.loads(prompt)["contexts"][0]
    page = record["pages"][0]
    return json.dumps(
        {
            "is_out_of_scope": False,
            "claims": [
                {
                    "text": "Synthetic answer.",
                    "sources": [
                        {
                            "chunk_id": record["chunk_id"],
                            "page_number": page["page_number"],
                            "quote": page["text"][:100],
                        }
                    ],
                }
            ],
        }
    )


def test_atomic_turns_order_history_and_private_traces(database):
    identifier, scope, hits = seed(database)
    with patch("backend.services.rag_service.service.retrieve", return_value=(scope, hits)):
        first = chat_with_trace(
            database, identifier, ChatRequest(message="First question"), SETTINGS, completion
        )
        second = chat_with_trace(
            database,
            identifier,
            ChatRequest(message="Follow up", conversation_id=first.response.conversation_id),
            SETTINGS,
            completion,
        )
    history = read_history(database, identifier, first.response.conversation_id, SETTINGS)
    assert [turn.question for turn in history.turns] == ["First question", "Follow up"]
    assert history.turns[-1].response == second.response
    assert database.chat_turns.count_documents({}) == 2
    assert "trace" not in history.model_dump_json()
    assert database.chat_turns.find_one({})["trace"]["retrieved_chunk_ids"]
    assert "active_turn_id" not in database.chat_conversations.find_one({})


def test_other_document_cannot_reuse_conversation(database):
    identifier, scope, hits = seed(database)
    other, _, _ = seed(database)
    with patch("backend.services.rag_service.service.retrieve", return_value=(scope, hits)):
        first = chat_with_trace(
            database, identifier, ChatRequest(message="Question"), SETTINGS, completion
        )
    with pytest.raises(DocumentNotFound):
        chat_with_trace(
            database,
            other,
            ChatRequest(message="Question", conversation_id=first.response.conversation_id),
            SETTINGS,
            Mock(),
        )
    with pytest.raises(DocumentNotFound):
        read_history(database, other, first.response.conversation_id, SETTINGS)


def test_model_failure_leaves_no_half_turn_and_releases_claim(database):
    identifier, scope, hits = seed(database)
    with patch("backend.services.rag_service.service.retrieve", return_value=(scope, hits)):
        with pytest.raises(RagUnavailable):
            chat_with_trace(
                database,
                identifier,
                ChatRequest(message="Question"),
                SETTINGS,
                Mock(return_value="{}"),
            )
    assert database.chat_turns.count_documents({}) == 0
    assert "active_turn_id" not in database.chat_conversations.find_one({})


def test_busy_conversation_rejects_parallel_turn(database):
    identifier, scope, hits = seed(database)
    with patch("backend.services.rag_service.service.retrieve", return_value=(scope, hits)):
        first = chat_with_trace(
            database, identifier, ChatRequest(message="Question"), SETTINGS, completion
        )
    database.chat_conversations.update_one(
        {"_id": first.response.conversation_id}, {"$set": {"active_turn_id": "another-job"}}
    )
    model = Mock()
    with pytest.raises(RagConflict):
        chat_with_trace(
            database,
            identifier,
            ChatRequest(message="Question", conversation_id=first.response.conversation_id),
            SETTINGS,
            model,
        )
    model.assert_not_called()


def test_source_change_during_generation_prevents_turn_save(database):
    identifier, scope, hits = seed(database)

    def changed(*args):
        database.documents.update_one(
            {"_id": ObjectId(identifier)}, {"$set": {"active_chunk_set_id": "f" * 64}}
        )
        return completion(*args)

    with patch("backend.services.rag_service.service.retrieve", return_value=(scope, hits)):
        with pytest.raises((RagConflict, RagNotReady)):
            chat_with_trace(
                database, identifier, ChatRequest(message="Question"), SETTINGS, changed
            )
    assert database.chat_turns.count_documents({}) == 0
