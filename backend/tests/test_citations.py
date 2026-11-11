"""Citation identity, source text, page/generation isolation and coordinate safety."""

from unittest.mock import MagicMock, patch

import pytest
from backend.services.document_processor.chunking import chunk_document
from backend.services.document_processor.parsed_models import (
    BoundingBox,
    ParsedDocument,
    ParsedPage,
    SourceElement,
)
from backend.services.rag_service.citations import (
    CitationSelection,
    InvalidCitation,
    StaleCitation,
    citation_id,
    make_citation,
    resolve_citation,
)
from backend.tests.summary_fixtures import DOCUMENT_ID, summary_chunks

QUOTE = "Verifiable source text."


def anchored_chunks(system="points", rotation=0, explicit=True):
    box = BoundingBox(
        x=10 if system != "normalized" else 0.1,
        y=20 if system != "normalized" else 0.2,
        width=100 if system != "normalized" else 0.4,
        height=15 if system != "normalized" else 0.1,
        coordinate_system=system,
    )
    element = SourceElement(
        element_id="element-a",
        document_id=DOCUMENT_ID,
        page_number=1,
        element_index=0,
        kind="text",
        text=QUOTE,
        source="items",
        bounding_boxes=[box],
        attributes={"bbox_origin": "top_left", "bbox_rotations": [rotation]} if explicit else {},
    )
    return chunk_document(
        ParsedDocument(
            document_id=DOCUMENT_ID,
            pages=[
                ParsedPage(
                    document_id=DOCUMENT_ID,
                    page_number=1,
                    markdown="# Method\n\n" + QUOTE,
                    width=200,
                    height=300,
                    elements=[element],
                )
            ],
        ),
        "parse-a",
    )


def selection(chunk=None, **updates):
    chunk = chunk or anchored_chunks()[0]
    data = {
        "document_id": DOCUMENT_ID,
        "chunk_id": chunk.id,
        "page_number": 1,
        "quote_snippet": QUOTE,
    }
    data.update(updates)
    data["citation_id"] = citation_id(
        data["document_id"], data["chunk_id"], data["page_number"], data["quote_snippet"]
    )
    return CitationSelection(**data)


def test_source_verified_geometry_and_identity_are_preserved():
    chunk = anchored_chunks()[0]
    result = make_citation(chunk, 1, QUOTE)
    assert result.chunk_set_id == chunk.chunk_set_id and result.parse_run_id == "parse-a"
    assert result.source_element_ids == ["element-a"]
    assert result.bounding_boxes[0].renderable and result.bounding_boxes[0].origin == "top_left"
    assert result.page_width == 200 and result.page_height == 300
    assert result.citation_id == selection(chunk).citation_id


@pytest.mark.parametrize(
    "system,rotation,explicit", [("provider", 0, True), ("points", 90, True), ("points", 0, False)]
)
def test_unknown_or_rotated_coordinates_are_retained_but_not_renderable(system, rotation, explicit):
    result = make_citation(anchored_chunks(system, rotation, explicit)[0], 1, QUOTE)
    assert result.bounding_boxes and not result.bounding_boxes[0].renderable


def test_missing_coordinates_still_has_verified_page_and_quote():
    chunk = summary_chunks()[0]
    quote = chunk.page_spans[0].text[:40]
    result = make_citation(chunk, 1, quote)
    assert result.page_number == 1 and result.quote_snippet == quote
    assert not result.bounding_boxes


@pytest.mark.parametrize("page,quote", [(2, QUOTE), (1, "Fabricated source")])
def test_wrong_pages_or_quotes_are_rejected(page, quote):
    with pytest.raises(InvalidCitation):
        make_citation(anchored_chunks()[0], page, quote)


def test_cross_document_selection_is_rejected_before_storage_read():
    db = MagicMock()
    with pytest.raises(InvalidCitation):
        resolve_citation(db, "507f1f77bcf86cd799439012", selection())
    db.documents.find_one.assert_not_called()


def test_tampered_citation_identity_is_rejected():
    selected = selection().model_copy(update={"citation_id": "f" * 64})
    with pytest.raises(InvalidCitation):
        resolve_citation(MagicMock(), DOCUMENT_ID, selected)


@pytest.mark.parametrize(
    "updates", [{"chunk_set_id": "f" * 64}, {"parse_run_id": "other-parse"}, {"chunk_id": "f" * 64}]
)
def test_stale_source_generations_are_rejected(updates):
    with patch(
        "backend.services.rag_service.citations.read_document_chunks",
        return_value=anchored_chunks(),
    ):
        with pytest.raises(StaleCitation):
            resolve_citation(MagicMock(), DOCUMENT_ID, selection(**updates))


def test_resolver_rechecks_generation_after_source_validation():
    db = MagicMock()
    db.documents.find_one.return_value = None
    with patch(
        "backend.services.rag_service.citations.read_document_chunks",
        return_value=anchored_chunks(),
    ):
        with pytest.raises(StaleCitation):
            resolve_citation(db, DOCUMENT_ID, selection())


def test_resolver_returns_canonical_geometry_not_client_coordinates():
    with patch(
        "backend.services.rag_service.citations.read_document_chunks",
        return_value=anchored_chunks(),
    ):
        result = resolve_citation(MagicMock(), DOCUMENT_ID, selection())
    assert result.bounding_boxes[0].renderable
