"""Shared synthetic summary fixtures; never call a provider."""

from backend.services.document_processor.chunking import chunk_document
from backend.services.document_processor.parsed_models import ParsedDocument, ParsedPage
from backend.services.summary_service.models import TEXT_FIELDS

DOCUMENT_ID = "507f1f77bcf86cd799439011"


def summary_chunks(document_id=DOCUMENT_ID, text=None):
    text = text or (
        "# Synthetic Research\n\nAda Example\n\n"
        "The study measures a synthetic counter. The method compares counts. "
        "The result is a count of 42. No real research claim is made."
    )
    return chunk_document(
        ParsedDocument(
            document_id=document_id,
            pages=[ParsedPage(document_id=document_id, page_number=1, markdown=text)],
        ),
        "synthetic-parse",
    )


def summary_draft(chunks=None):
    chunks = chunks or summary_chunks()
    span = chunks[0].page_spans[0]
    source = {"chunk_id": chunks[0].id, "page_number": span.page_number, "quote": span.text[:200]}
    result = {
        field: {"text": "Synthetic summary content", "sources": [dict(source)]}
        for field in TEXT_FIELDS
    }
    result["title"]["text"] = "Synthetic Research"
    result["authors"] = {"names": ["Ada Example"], "sources": [dict(source)]}
    return result
