"""Document-scoped chat HTTP routes; internal retrieval traces stay private."""

from collections.abc import Callable
from typing import Annotated, Any, TypeVar

from backend.gateway.documents import DatabaseDependency, DocumentId
from backend.services.document_processor.chunk_storage import ChunkingNotReady
from backend.services.rag_service.models import (
    ChatRequest,
    ChatResponse,
    RagConflict,
    RagNotReady,
    RagUnavailable,
)
from backend.services.rag_service.service import ChatHistory, chat_with_trace, read_history
from backend.shared.config import get_settings
from backend.shared.storage import DocumentNotFound
from fastapi import APIRouter, HTTPException, Path

router = APIRouter(prefix="/api/v1/documents", tags=["Chat"])
ConversationId = Annotated[str, Path(pattern=r"^[0-9a-f]{32}$")]
T = TypeVar("T")


def _invoke(function: Callable[..., T], *args: Any) -> T:
    try:
        return function(*args)
    except DocumentNotFound:
        raise HTTPException(404, "Document or conversation not found") from None
    except (RagNotReady, ChunkingNotReady):
        raise HTTPException(409, "Current document embeddings are not ready for chat") from None
    except RagConflict:
        raise HTTPException(
            409,
            "Conversation is busy or its document changed; recheck history or start a new conversation",
        ) from None
    except RagUnavailable:
        raise HTTPException(
            503, "Chat unavailable; check provider and Atlas search configuration"
        ) from None


@router.post("/{document_id}/chat", response_model=ChatResponse)
def chat(
    document_id: DocumentId, request: ChatRequest, database: DatabaseDependency
) -> ChatResponse:
    return _invoke(chat_with_trace, database, document_id, request, get_settings()).response


@router.get("/{document_id}/chat/{conversation_id}", response_model=ChatHistory)
def history(
    document_id: DocumentId, conversation_id: ConversationId, database: DatabaseDependency
) -> ChatHistory:
    return _invoke(read_history, database, document_id, conversation_id, get_settings())
