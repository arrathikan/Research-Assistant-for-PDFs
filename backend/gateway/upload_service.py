"""Upload orchestration: validate first, then persist the original bytes."""

from typing import BinaryIO

from backend.services.document_processor.upload import validate_pdf
from backend.shared.config import Settings
from backend.shared.database import connect_database, ensure_indexes
from backend.shared.storage import StoredPdfResult, store_pdf


def persist_upload(
    filename: str | None, content_type: str | None, stream: BinaryIO, settings: Settings
) -> StoredPdfResult:
    pdf = validate_pdf(filename, content_type, stream, settings.max_upload_size_bytes)
    with connect_database(settings) as database:
        # Never accept writes unless MongoDB's unique SHA-256 index is active.
        ensure_indexes(database)
        return store_pdf(database, pdf.filename, pdf.content, page_count=pdf.page_count)
