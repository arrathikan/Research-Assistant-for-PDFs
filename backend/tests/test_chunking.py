"""Markdown/page/source invariants with the actual LangChain splitters."""

import pytest
from backend.services.document_processor.chunk_models import ChunkingConfig, ChunkingError
from backend.services.document_processor.chunking import chunk_document
from backend.services.document_processor.parsed_models import (
    BoundingBox,
    ParsedDocument,
    ParsedPage,
    SourceElement,
)
from backend.shared.config import Settings
from pydantic import ValidationError

ID = "507f1f77bcf86cd799439011"


def parsed(*texts):
    return ParsedDocument(
        document_id=ID,
        pages=[
            ParsedPage(document_id=ID, page_number=index + 1, markdown=text)
            for index, text in enumerate(texts)
        ],
    )


def test_small_section_and_heading_metadata():
    chunks = chunk_document(parsed("# Paper\n\n## Method\n\nShort method text."), "parse-a")
    assert chunks[-1].heading_path == {"h1": "Paper", "h2": "Method"}
    assert chunks[-1].section_title == "Method"
    assert "Short method text." in chunks[-1].content
    assert all(chunk.page_numbers == [1] for chunk in chunks)


def test_large_sections_are_bounded_and_overlap_is_real():
    text = "# Method\n\n" + "".join(chr(0x400 + i) for i in range(200))
    chunks = chunk_document(
        parsed(text), "parse-a", ChunkingConfig(chunk_size=50, chunk_overlap=10)
    )
    assert len(chunks) > 3
    assert all(0 < len(chunk.content) <= 50 for chunk in chunks)
    long_chunks = [chunk for chunk in chunks if len(chunk.content) == 50]
    assert long_chunks[0].content[-10:] == long_chunks[1].content[:10]


def test_different_sections_never_share_a_chunk():
    chunks = chunk_document(
        parsed("## Method\n\nMethod only.\n\n## Results\n\nResults only."), "parse-a"
    )
    assert len(chunks) == 2
    assert all(
        not ("Method only" in chunk.content and "Results only" in chunk.content) for chunk in chunks
    )


def test_section_continuation_spans_pages_with_exact_chunk_offsets():
    chunks = chunk_document(
        parsed("## Method\n\nPage one method.", "Page two continuation."), "parse-a"
    )
    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.page_numbers == [1, 2] and chunk.page_end == 2
    assert chunk.section_title == "Method"
    assert [span.page_number for span in chunk.page_spans] == [1, 1, 2]
    assert all(
        chunk.content[span.chunk_start : span.chunk_end] == span.text for span in chunk.page_spans
    )
    assert "RESEARCHAI_PAGE" not in chunk.content


def test_tables_and_code_headings_stay_in_their_section():
    table = "| A | B |\n| --- | --- |\n| 1 | 2 |"
    chunks = chunk_document(
        parsed("## Results\n\n" + table + "\n\n```python\n# not a research section\nprint(1)\n```"),
        "parse-a",
    )
    assert len(chunks) == 1
    assert table in chunks[0].content
    assert chunks[0].section_title == "Results"


def test_source_references_and_all_coordinates_are_preserved():
    document = parsed("## Method\n\nUnique evidence sentence.")
    element = SourceElement(
        element_id="element-1",
        document_id=ID,
        page_number=1,
        element_index=0,
        kind="text",
        text="Unique evidence sentence.",
        source="items",
        bounding_boxes=[BoundingBox(x=10, y=20, width=100, height=15, coordinate_system="points")],
    )
    document.pages[0].elements = [element]
    chunks = chunk_document(document, "parse-a", ChunkingConfig(chunk_size=25, chunk_overlap=5))
    references = [
        ref for chunk in chunks for span in chunk.page_spans for ref in span.source_elements
    ]
    assert references and all(ref.element_id == "element-1" for ref in references)
    assert references[0].bounding_boxes == element.bounding_boxes


def test_ambiguous_repeated_text_uses_page_fallback():
    document = parsed("Repeated sentence.\n\nRepeated sentence.")
    document.pages[0].elements = [
        SourceElement(
            element_id="repeated",
            document_id=ID,
            page_number=1,
            element_index=0,
            kind="text",
            source="items",
            text="Repeated sentence.",
        )
    ]
    chunks = chunk_document(document, "parse-a")
    assert all(not span.source_elements for chunk in chunks for span in chunk.page_spans)
    assert chunks[0].page_numbers == [1]


def test_stable_ids_and_configuration_or_parse_changes():
    document = parsed("## Method\n\nEvidence.")
    first = chunk_document(document, "parse-a")
    second = chunk_document(document, "parse-a")
    assert [chunk.id for chunk in first] == [chunk.id for chunk in second]
    assert first[0].id != chunk_document(document, "parse-b")[0].id
    assert first[0].id != chunk_document(document, "parse-a", ChunkingConfig(chunk_size=1300))[0].id


def test_blank_pages_do_not_get_cited_as_evidence():
    chunks = chunk_document(parsed("## Method\n\nFirst", "", "Third"), "parse-a")
    assert chunks[0].page_numbers == [1, 3]


@pytest.mark.parametrize("size,overlap", [(0, 0), (10, -1), (10, 10), (10, 11)])
def test_invalid_chunk_configuration_is_rejected(size, overlap):
    with pytest.raises(ValidationError):
        ChunkingConfig(chunk_size=size, chunk_overlap=overlap)
    with pytest.raises(ValidationError):
        Settings(_env_file=None, chunk_size=size, chunk_overlap=overlap)


def test_empty_markdown_and_foreign_pages_are_rejected():
    with pytest.raises(ChunkingError):
        chunk_document(parsed(""), "parse-a")
    document = parsed("Text")
    document.pages[0].document_id = "507f1f77bcf86cd799439012"
    with pytest.raises(ChunkingError):
        chunk_document(document, "parse-a")
