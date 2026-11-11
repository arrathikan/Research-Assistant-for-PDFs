"""Read processing progress or explicitly retry a failed job; never call providers."""

from backend.gateway.documents import DatabaseDependency, DocumentId
from backend.services.jobs.store import JobConflict, ProcessingView, read_status, retry_job
from backend.shared.config import get_settings
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/documents", tags=["Processing"])


@router.get("/{document_id}/processing", response_model=ProcessingView)
def processing_status(document_id: DocumentId, database: DatabaseDependency) -> ProcessingView:
    return read_status(database, document_id.lower())


@router.post("/{document_id}/processing/retry", response_model=ProcessingView)
def retry_processing(document_id: DocumentId, database: DatabaseDependency) -> ProcessingView:
    try:
        return retry_job(database, document_id.lower(), get_settings())
    except JobConflict as failure:
        raise HTTPException(409, str(failure)) from None
