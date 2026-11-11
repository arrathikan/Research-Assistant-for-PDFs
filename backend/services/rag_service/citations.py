"""Resolve citations from current canonical chunks, never client-supplied geometry."""

from hashlib import sha256
from math import isfinite

from backend.services.document_processor.chunk_models import DocumentChunk
from backend.services.document_processor.chunk_storage import read_document_chunks
from backend.services.rag_service.models import ChatCitation
from backend.services.summary_service.models import StrictModel
from backend.shared.citation_models import CitationBox
from backend.shared.database import StorageUnavailable
from pydantic import Field
from pymongo.database import Database
from pymongo.errors import PyMongoError


class InvalidCitation(ValueError):
    """Source identity, page or quote could not be verified."""


class StaleCitation(RuntimeError):
    """Citation no longer belongs to the active source generation."""


class CitationSelection(StrictModel):
    citation_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    document_id: str = Field(pattern=r"^[0-9a-f]{24}$")
    chunk_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    page_number: int = Field(ge=1, strict=True)
    quote_snippet: str = Field(min_length=1, max_length=400)
    chunk_set_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    parse_run_id: str | None = None


def citation_id(document_id: str, chunk_id: str, page: int, quote: str) -> str:
    return sha256(f"{document_id}:{chunk_id}:{page}:{quote}".encode()).hexdigest()


def _normalized(text: str) -> str:
    return " ".join(text.split())


def make_citation(chunk: DocumentChunk, page: int, quote: str) -> ChatCitation:
    spans = [
        span
        for span in chunk.page_spans
        if span.page_number == page and _normalized(quote) in _normalized(span.text)
    ]
    if not quote.strip() or not spans:
        raise InvalidCitation("Citation quote does not match the cited page")
    elements = {
        element.element_id: element
        for span in spans
        for element in span.source_elements
        if any(
            _normalized(quote) in _normalized(text)
            for text in [element.text, element.markdown]
            if text
        )
    }
    frame = spans[0]
    dimensions = (frame.page_width, frame.page_height)
    valid_frame = all(
        isinstance(value, (int, float)) and isfinite(value) and value > 0 for value in dimensions
    )
    boxes = []
    for element in elements.values():
        raw_boxes = element.bounding_boxes or ([element.bbox] if element.bbox else [])
        rotations = element.attributes.get("bbox_rotations", [])
        for index, box in enumerate(raw_boxes):
            legacy_layout = element.source == "layout" and box.coordinate_system == "normalized"
            origin = (
                "top_left"
                if legacy_layout or element.attributes.get("bbox_origin") == "top_left"
                else "unknown"
            )
            rotation = (
                0
                if legacy_layout
                else rotations[index]
                if isinstance(rotations, list) and len(rotations) == len(raw_boxes)
                else None
            )
            if (
                isinstance(rotation, bool)
                or not isinstance(rotation, (int, float))
                or not isfinite(rotation)
            ):
                rotation = None
            bounds_ok = False
            if box.coordinate_system == "normalized":
                bounds_ok = box.x + box.width <= 1.000001 and box.y + box.height <= 1.000001
            elif box.coordinate_system == "points" and valid_frame:
                bounds_ok = (
                    box.x + box.width <= dimensions[0] + 0.01
                    and box.y + box.height <= dimensions[1] + 0.01
                )
            boxes.append(
                CitationBox(
                    **box.model_dump(),
                    element_id=element.element_id,
                    origin=origin,
                    rotation_degrees=rotation,
                    renderable=len(elements) == 1
                    and origin == "top_left"
                    and rotation == 0
                    and bounds_ok,
                )
            )
    return ChatCitation(
        citation_id=citation_id(chunk.document_id, chunk.id, page, quote),
        document_id=chunk.document_id,
        chunk_id=chunk.id,
        page_number=page,
        quote_snippet=quote,
        chunk_set_id=chunk.chunk_set_id,
        parse_run_id=chunk.parse_run_id,
        page_width=frame.page_width if valid_frame else None,
        page_height=frame.page_height if valid_frame else None,
        source_element_ids=list(elements),
        bounding_boxes=boxes,
    )


def resolve_citation(
    database: Database, document_id: str, selection: CitationSelection
) -> ChatCitation:
    document_id = document_id.lower()
    if selection.document_id != document_id:
        raise InvalidCitation("Citation belongs to another document")
    if selection.citation_id != citation_id(
        document_id, selection.chunk_id, selection.page_number, selection.quote_snippet
    ):
        raise InvalidCitation("Citation identity does not match its source")
    chunks = read_document_chunks(database, document_id)
    chunk = next((item for item in chunks if item.id == selection.chunk_id), None)
    if (
        chunk is None
        or selection.chunk_set_id not in (None, chunk.chunk_set_id)
        or selection.parse_run_id not in (None, chunk.parse_run_id)
    ):
        raise StaleCitation("Citation sources changed; load a current answer")
    result = make_citation(chunk, selection.page_number, selection.quote_snippet)
    # Recheck generation after reading source data so old chunks cannot be published.
    from bson import ObjectId

    try:
        document = database.documents.find_one(
            {
                "_id": ObjectId(document_id),
                "active_chunk_set_id": chunk.chunk_set_id,
                "active_parse_run_id": chunk.parse_run_id,
            }
        )
    except PyMongoError:
        raise StorageUnavailable("Citation source retrieval unavailable") from None
    if document is None:
        raise StaleCitation("Citation sources changed while resolving")
    return result
