"""Single-document extraction with immutable runs and atomic publication."""

from datetime import datetime, timezone
from importlib.metadata import version
from io import BytesIO
from typing import Any
from uuid import uuid4

from backend.services.document_processor.llamaparse_client import parse_with_llamaparse
from backend.services.document_processor.parsed_models import (
    ParsedDocument,
    ParsedPage,
    ParsingError,
    SourceElement,
)
from backend.services.document_processor.upload import validate_pdf
from backend.shared.config import Settings
from backend.shared.database import StorageUnavailable
from backend.shared.models import DocumentStatus, ParsingStatus
from backend.shared.storage import DocumentNotFound, get_document, read_pdf
from bson import ObjectId
from pymongo import ASCENDING, ReturnDocument
from pymongo.database import Database
from pymongo.errors import PyMongoError


class ParsingConflict(RuntimeError):
    """Another worker owns parsing or the document is in a later pipeline stage."""


class ParsingNotReady(LookupError):
    """No complete extraction has been published for the document."""


def _now() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(microsecond=now.microsecond // 1000 * 1000)


def ensure_parse_indexes(database: Database[dict[str, Any]]) -> None:
    try:
        database.parsed_pages.create_index(
            [("document_id", ASCENDING), ("parse_run_id", ASCENDING), ("page_number", ASCENDING)],
            unique=True,
            name="parsed_run_pages",
        )
        database.source_elements.create_index(
            [("document_id", ASCENDING), ("parse_run_id", ASCENDING), ("page_number", ASCENDING)],
            name="parsed_run_sources",
        )
    except PyMongoError:
        raise StorageUnavailable("Parsing indexes unavailable") from None


def save_parsed_document(
    database: Database[dict[str, Any]], parsed: ParsedDocument, run_id: str, settings: Settings
) -> None:
    """Write a new run, then publish its pointer only if this worker still owns it.

    Partial runs are never returned by readers. They are retained for explicit
    operator reconciliation, without deleting prior successful extraction data.
    """
    identifier = ObjectId(parsed.document_id)
    pages = []
    sources = []
    for page in parsed.pages:
        if page.document_id != parsed.document_id:
            raise ParsingError("Parsed page belongs to another document")
        pages.append(
            {
                "_id": f"{run_id}:p{page.page_number}",
                "parse_run_id": run_id,
                **page.model_dump(exclude={"elements"}),
            }
        )
        for element in page.elements:
            if element.document_id != parsed.document_id or element.page_number != page.page_number:
                raise ParsingError("Parsed source belongs to another document or page")
            sources.append(
                {
                    "_id": f"{run_id}:{element.element_id}",
                    "parse_run_id": run_id,
                    **element.model_dump(),
                }
            )
    try:
        database.parsed_pages.insert_many(pages, ordered=True)
        if sources:
            database.source_elements.insert_many(sources, ordered=True)
        completed = database.documents.update_one(
            {
                "_id": identifier,
                "parsing_run_id": run_id,
                "parsing_status": ParsingStatus.RUNNING,
                "status": DocumentStatus.PARSING,
            },
            {
                "$set": {
                    "active_parse_run_id": run_id,
                    "parsing_status": ParsingStatus.COMPLETED,
                    "status": DocumentStatus.PENDING,
                    "parsed_at": _now(),
                    "updated_at": _now(),
                    "page_count": len(parsed.pages),
                    "parsing_job_id": parsed.provider_job_id,
                    "parsing_sdk_version": version("llama-cloud"),
                    "parsing_provider_version": settings.llama_parse_version,
                    "parsing_tier": settings.llama_parse_tier,
                    "error_message": None,
                },
                "$unset": {"parsing_run_id": ""},
            },
        )
        if completed.matched_count != 1:
            raise ParsingConflict("Parsing ownership changed before publication")
    except PyMongoError:
        raise StorageUnavailable("Parsed content persistence failed") from None


def read_parsed_document(database: Database[dict[str, Any]], document_id: str) -> ParsedDocument:
    if not ObjectId.is_valid(document_id):
        raise ValueError("Invalid document identifier")
    try:
        document = database.documents.find_one({"_id": ObjectId(document_id)})
        if document is None:
            raise DocumentNotFound("Document not found")
        run_id = document.get("active_parse_run_id")
        if not run_id:
            raise ParsingNotReady("Document parsing is not complete")
        query = {"document_id": str(document["_id"]), "parse_run_id": run_id}
        pages = []
        elements = list(database.source_elements.find(query).sort("element_index", ASCENDING))
        for record in database.parsed_pages.find(query).sort("page_number", ASCENDING):
            page = ParsedPage.model_validate(record)
            page.elements = [
                SourceElement.model_validate(element)
                for element in elements
                if element["page_number"] == page.page_number
            ]
            pages.append(page)
        if len(pages) != document.get("page_count") or [page.page_number for page in pages] != list(
            range(1, len(pages) + 1)
        ):
            raise StorageUnavailable("Published extraction is incomplete")
        return ParsedDocument(
            document_id=str(document["_id"]),
            pages=pages,
            provider_job_id=document.get("parsing_job_id"),
        )
    except PyMongoError:
        raise StorageUnavailable("Parsed content retrieval unavailable") from None


def parse_pdf(
    database: Database[dict[str, Any]], document_id: str, settings: Settings
) -> ParsedDocument:
    """Parse an uploaded PDF synchronously in a dedicated process, never a route.

    Completed extraction is reused. Failed attempts may be retried. A running
    claim has no automatic expiry, avoiding duplicate paid calls; interrupted
    claims require operator review before manual recovery.
    """
    document = get_document(database, document_id)
    if document is None:
        raise DocumentNotFound("Document not found")
    if document.parsing_status == ParsingStatus.COMPLETED:
        return read_parsed_document(database, document_id)
    if not settings.llama_cloud_api_key.strip() or settings.llama_cloud_api_key.startswith("your_"):
        raise ParsingError("LLAMA_CLOUD_API_KEY is not configured")
    ensure_parse_indexes(database)
    run_id = uuid4().hex
    identifier = ObjectId(document_id)
    try:
        claim = database.documents.find_one_and_update(
            {
                "_id": identifier,
                "status": {"$in": [DocumentStatus.PENDING, DocumentStatus.FAILED]},
                "parsing_status": {"$nin": [ParsingStatus.RUNNING, ParsingStatus.COMPLETED]},
            },
            {
                "$set": {
                    "status": DocumentStatus.PARSING,
                    "parsing_status": ParsingStatus.RUNNING,
                    "parsing_run_id": run_id,
                    "updated_at": _now(),
                    "error_message": None,
                }
            },
            return_document=ReturnDocument.AFTER,
        )
    except PyMongoError:
        raise StorageUnavailable("Parsing claim unavailable") from None
    if claim is None:
        raise ParsingConflict("Document is already processing or in a later stage")
    try:
        content = read_pdf(database, document_id)
        pdf = validate_pdf(
            "source.pdf", "application/pdf", BytesIO(content), settings.max_upload_size_bytes
        )
        if document.page_count is not None and pdf.page_count != document.page_count:
            raise ParsingError("Stored PDF page count does not match metadata")
        parsed = parse_with_llamaparse(document_id, content, pdf.page_count, settings)
        save_parsed_document(database, parsed, run_id, settings)
        return parsed
    except Exception:
        try:
            database.documents.update_one(
                {"_id": identifier, "parsing_run_id": run_id},
                {
                    "$set": {
                        "status": DocumentStatus.FAILED,
                        "parsing_status": ParsingStatus.FAILED,
                        "updated_at": _now(),
                        "error_message": "PDF parsing failed; check parser configuration and retry",
                    },
                    "$unset": {"parsing_run_id": ""},
                },
            )
        except PyMongoError:
            raise StorageUnavailable(
                "Parsing failed and failure status could not be saved"
            ) from None
        raise ParsingError("PDF parsing failed; check parser configuration and retry") from None
