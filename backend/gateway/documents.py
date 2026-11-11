"""Document HTTP contracts, separate from validation and storage logic."""

from collections.abc import Iterator
from typing import Annotated, Any
from urllib.parse import quote

from backend.gateway.body_limit import LIMIT_DETAIL
from backend.gateway.upload_service import persist_upload
from backend.services.document_processor.chunk_models import DocumentChunk
from backend.services.document_processor.chunk_storage import ChunkingNotReady, read_document_chunks
from backend.services.document_processor.extraction import ParsingNotReady, read_parsed_document
from backend.services.document_processor.parsed_models import ParsedDocument
from backend.services.summary_service.models import SummaryError, SummaryResult
from backend.services.summary_service.storage import SummaryNotReady, read_summary
from backend.shared.config import get_settings
from backend.shared.database import connect_database
from backend.shared.models import DocumentStatus
from backend.shared.storage import (
    DocumentNotFound,
    StoredDocument,
    StoredPdfResult,
    get_document,
    read_pdf,
)
from fastapi import APIRouter, Depends, HTTPException, Path, Request, Response
from pydantic import BaseModel
from pymongo.database import Database
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException as StarletteHTTPException

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])
DocumentId = Annotated[str, Path(pattern=r"^[0-9a-fA-F]{24}$")]


class UploadResponse(StoredPdfResult):
    message: str


class DocumentStatusResponse(BaseModel):
    document_id: str
    status: DocumentStatus
    error_message: str | None = None


def get_database(document_id: DocumentId) -> Iterator[Database[dict[str, Any]]]:
    with connect_database(get_settings()) as database:
        yield database


DatabaseDependency = Annotated[Database[dict[str, Any]], Depends(get_database)]


@router.post(
    "",
    response_model=UploadResponse,
    response_model_by_alias=False,
    status_code=201,
    responses={200: {"model": UploadResponse}},
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["file"],
                        "properties": {"file": {"type": "string", "format": "binary"}},
                    }
                }
            },
        }
    },
)
@router.post(
    "/upload",
    response_model=UploadResponse,
    response_model_by_alias=False,
    status_code=201,
    include_in_schema=False,
)
async def upload_document(request: Request, response: Response) -> UploadResponse:
    if (
        request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        != "multipart/form-data"
    ):
        raise HTTPException(415, "Use multipart/form-data with one PDF file")
    try:
        async with request.form(max_files=1, max_fields=0) as form:
            entries = list(form.multi_items())
            if (
                len(entries) != 1
                or entries[0][0] != "file"
                or not isinstance(entries[0][1], UploadFile)
            ):
                raise HTTPException(422, "Provide exactly one PDF in the file field")
            file = entries[0][1]
            result = await run_in_threadpool(
                persist_upload, file.filename, file.content_type, file.file, get_settings()
            )
    except StarletteHTTPException as exc:
        if exc.detail == LIMIT_DETAIL:
            raise HTTPException(413, LIMIT_DETAIL) from None
        raise
    response.status_code = 200 if result.is_duplicate else 201
    message = (
        "Identical PDF already stored" if result.is_duplicate else "PDF stored; processing pending"
    )
    return UploadResponse(
        document=result.document, is_duplicate=result.is_duplicate, message=message
    )


@router.get("/{document_id}", response_model=StoredDocument, response_model_by_alias=False)
def document_metadata(document_id: DocumentId, database: DatabaseDependency) -> StoredDocument:
    document = get_document(database, document_id)
    if document is None:
        raise HTTPException(404, "Document not found")
    return document


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
def document_status(
    document_id: DocumentId, database: DatabaseDependency
) -> DocumentStatusResponse:
    document = document_metadata(document_id, database)
    return DocumentStatusResponse(
        document_id=document.id, status=document.status, error_message=document.error_message
    )


@router.get(
    "/{document_id}/pdf",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
def original_pdf(document_id: DocumentId, database: DatabaseDependency) -> Response:
    document = document_metadata(document_id, database)
    content = read_pdf(database, document_id)
    return Response(
        content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline; filename*=UTF-8''" + quote(document.filename, safe=""),
            "Cache-Control": "no-store",
        },
    )


@router.get("/{document_id}/parsed", response_model=ParsedDocument)
def parsed_document(document_id: DocumentId, database: DatabaseDependency) -> ParsedDocument:
    """Retrieve committed extraction; never start a paid parse in an HTTP route."""
    try:
        return read_parsed_document(database, document_id)
    except ParsingNotReady:
        raise HTTPException(409, "Document parsing is not complete") from None
    except DocumentNotFound:
        raise HTTPException(404, "Document not found") from None


@router.get(
    "/{document_id}/chunks", response_model=list[DocumentChunk], response_model_by_alias=False
)
def document_chunks(document_id: DocumentId, database: DatabaseDependency) -> list[DocumentChunk]:
    """Read a complete chunk set for the current parse; never trigger processing."""
    try:
        return read_document_chunks(database, document_id)
    except ChunkingNotReady:
        raise HTTPException(
            409, "Chunking is not complete for the current parsed document"
        ) from None
    except DocumentNotFound:
        raise HTTPException(404, "Document not found") from None


@router.get("/{document_id}/summary", response_model=SummaryResult)
def document_summary(document_id: DocumentId, database: DatabaseDependency) -> SummaryResult:
    """Read a published summary; never start a paid completion in an HTTP route."""
    try:
        return read_summary(database, document_id, get_settings())
    except DocumentNotFound:
        raise HTTPException(404, "Document not found") from None
    except SummaryNotReady:
        raise HTTPException(
            409, "Summary is not complete for the current document and model"
        ) from None
    except SummaryError:
        raise HTTPException(503, "Summary generation failed; retry the summary job") from None
