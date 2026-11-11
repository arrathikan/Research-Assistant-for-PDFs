"""Deterministic citation resolution; never calls a model or starts parsing."""

from backend.gateway.documents import DatabaseDependency, DocumentId
from backend.services.document_processor.chunk_storage import ChunkingNotReady
from backend.services.rag_service.citations import (
    CitationSelection,
    InvalidCitation,
    StaleCitation,
    resolve_citation,
)
from backend.services.rag_service.models import ChatCitation
from backend.shared.storage import DocumentNotFound
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/documents", tags=["Citations"])


@router.post("/{document_id}/citations/resolve", response_model=ChatCitation)
def citation_source(
    document_id: DocumentId, selection: CitationSelection, database: DatabaseDependency
) -> ChatCitation:
    try:
        return resolve_citation(database, document_id, selection)
    except InvalidCitation:
        raise HTTPException(422, "Citation identity, page or quote is invalid") from None
    except (StaleCitation, ChunkingNotReady):
        raise HTTPException(
            409, "Citation sources changed or are not ready; load a current answer"
        ) from None
    except DocumentNotFound:
        raise HTTPException(404, "Document not found") from None
