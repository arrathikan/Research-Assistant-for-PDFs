"""Deterministic source-attribution checks using synthetic provider responses."""

import pytest
from backend.services.document_processor.normalization import normalize_parsed_pages
from backend.services.document_processor.parsed_models import ParsingError

DOCUMENT_ID = "507f1f77bcf86cd799439011"


def response(*pages):
    return [{"job_id": "synthetic-job", "pages": list(pages)}]


def test_markdown_headings_tables_and_page_order_are_preserved():
    table = "## Results\n\n| Model | Score |\n| --- | --- |\n| A | 42 |"
    parsed = normalize_parsed_pages(
        DOCUMENT_ID, response({"page": 2, "md": table}, {"page": 1, "md": "# Paper\n\nAbstract"}), 2
    )
    assert [page.page_number for page in parsed.pages] == [1, 2]
    assert parsed.pages[1].markdown == table
    assert (
        parsed.as_markdown()
        == "--- Page 1 ---\n\n# Paper\n\nAbstract\n\n--- Page 2 ---\n\n" + table
    )
    assert parsed.provider_job_id == "synthetic-job"


def test_source_elements_keep_text_ids_and_optional_coordinates_separate():
    page = {
        "page": 1,
        "md": "# Method",
        "width": 600,
        "height": 800,
        "items": [
            {
                "id": "heading-1",
                "type": "heading",
                "md": "# Method",
                "bBox": {"x": 12, "y": 15, "w": 60, "h": 20},
            }
        ],
        "layout": [{"label": "title", "bbox": {"x": 0.1, "y": 0.1, "w": 0.5, "h": 0.1}}],
    }
    parsed = normalize_parsed_pages(DOCUMENT_ID, response(page), 1)
    item, layout = parsed.pages[0].elements
    assert item.document_id == DOCUMENT_ID and item.page_number == 1
    assert item.element_id == DOCUMENT_ID + ":p1:e0"
    assert item.provider_element_id == "heading-1"
    assert item.bbox.coordinate_system == "provider"
    assert item.bbox.width == 60
    assert layout.bbox.coordinate_system == "normalized"
    assert layout.text == "" and layout.markdown == ""
    assert parsed.pages[0].width == 600


def test_missing_coordinates_and_dimensions_are_safe():
    parsed = normalize_parsed_pages(
        DOCUMENT_ID,
        response({"page": 1, "md": "Text", "items": [{"type": "text", "text": "Text"}]}),
        1,
    )
    assert parsed.pages[0].elements[0].bbox is None
    assert parsed.pages[0].width is None


@pytest.mark.parametrize(
    "box",
    [
        None,
        {},
        {"x": -1, "y": 0, "w": 1, "h": 1},
        {"x": "bad", "y": 0, "w": 1, "h": 1},
        {"x": float("nan"), "y": 0, "w": 1, "h": 1},
    ],
)
def test_invalid_optional_boxes_fall_back_to_page_navigation(box):
    parsed = normalize_parsed_pages(
        DOCUMENT_ID,
        response({"page": 1, "md": "Text", "items": [{"text": "Text", "bBox": box}]}),
        1,
    )
    assert parsed.pages[0].elements[0].bbox is None


def test_out_of_page_normalized_box_is_not_used():
    parsed = normalize_parsed_pages(
        DOCUMENT_ID,
        response(
            {
                "page": 1,
                "md": "Text",
                "layout": [{"label": "text", "bbox": {"x": 0.9, "y": 0, "w": 0.5, "h": 0.1}}],
            }
        ),
        1,
    )
    assert parsed.pages[0].elements[0].bbox is None


def test_blank_pages_are_retained_and_text_fallback_is_explicit():
    parsed = normalize_parsed_pages(
        DOCUMENT_ID, response({"page": 1, "md": ""}, {"page": 2, "text": "plain text"}), 2
    )
    assert parsed.pages[0].markdown == ""
    assert parsed.pages[1].markdown == "plain text"


@pytest.mark.parametrize(
    "data,count",
    [
        (None, 1),
        ([], 1),
        ([{}, {}], 1),
        (response(), 1),
        (response({"page": 1, "md": ""}), 1),
        (response({"md": "Text"}), 1),
        (response({"page": 0, "md": "Text"}), 1),
        (response({"page": 2, "md": "Text"}), 1),
        (response({"page": 1, "md": "A"}, {"page": 1, "md": "B"}), 2),
        (response({"page": 1, "md": 123}), 1),
        (response({"page": 1, "md": "A", "items": "bad"}), 1),
    ],
)
def test_empty_partial_malformed_or_ambiguous_results_are_rejected(data, count):
    with pytest.raises(ParsingError):
        normalize_parsed_pages(DOCUMENT_ID, data, count)
