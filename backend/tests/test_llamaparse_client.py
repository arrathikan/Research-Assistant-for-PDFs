"""Provider SDK contract tests use a real SDK response model and mocked network."""

from copy import deepcopy
from unittest.mock import patch

import pytest
from backend.services.document_processor.llamaparse_client import (
    normalize_v2_result,
    parse_with_llamaparse,
)
from backend.services.document_processor.parsed_models import ParsingError
from backend.shared.config import Settings
from llama_cloud.types.parsing_get_response import ParsingGetResponse

DOCUMENT_ID = "507f1f77bcf86cd799439011"


def response():
    return {
        "job": {"id": "job-test", "project_id": "project-test", "status": "COMPLETED"},
        "markdown": {
            "pages": [{"page_number": 1, "success": True, "markdown": "# Method\n\nText"}]
        },
        "items": {
            "pages": [
                {
                    "page_number": 1,
                    "success": True,
                    "page_width": 600,
                    "page_height": 800,
                    "items": [
                        {
                            "type": "heading",
                            "level": 1,
                            "value": "Method",
                            "md": "# Method",
                            "bbox": [
                                {"x": 10, "y": 20, "w": 60, "h": 20},
                                {"x": 75, "y": 20, "w": 20, "h": 20},
                            ],
                        }
                    ],
                }
            ]
        },
    }


def test_real_sdk_response_and_request_configuration():
    settings = Settings(_env_file=None, llama_cloud_api_key="test-only-key")
    with patch("backend.services.document_processor.llamaparse_client.LlamaCloud") as constructor:
        client = constructor.return_value.__enter__.return_value
        client.parsing.parse.return_value = ParsingGetResponse.model_validate(response())
        parsed = parse_with_llamaparse(DOCUMENT_ID, b"synthetic-pdf", 1, settings)
    constructor.assert_called_once_with(api_key="test-only-key", timeout=60, max_retries=0)
    kwargs = client.parsing.parse.call_args.kwargs
    assert kwargs["upload_file"] == ("source.pdf", b"synthetic-pdf", "application/pdf")
    assert kwargs["expand"] == ["markdown", "items", "metadata"]
    assert kwargs["timeout"] == 300
    assert parsed.pages[0].elements[0].bbox.coordinate_system == "points"
    assert len(parsed.pages[0].elements[0].bounding_boxes) == 2
    assert parsed.pages[0].elements[0].attributes["level"] == 1
    constructor.return_value.__exit__.assert_called_once()


def test_missing_key_does_not_call_the_provider():
    with patch("backend.services.document_processor.llamaparse_client.LlamaCloud") as client:
        with pytest.raises(ParsingError, match="not configured"):
            parse_with_llamaparse(
                DOCUMENT_ID, b"pdf", 1, Settings(_env_file=None, llama_cloud_api_key="")
            )
        client.assert_not_called()


def test_external_failure_is_generic_and_hides_provider_details():
    with patch("backend.services.document_processor.llamaparse_client.LlamaCloud") as constructor:
        constructor.return_value.__enter__.return_value.parsing.parse.side_effect = RuntimeError(
            "secret-provider-details"
        )
        with pytest.raises(ParsingError, match="^LlamaParse request failed or timed out$"):
            parse_with_llamaparse(
                DOCUMENT_ID, b"pdf", 1, Settings(_env_file=None, llama_cloud_api_key="test")
            )


def test_nested_items_and_table_metadata_are_preserved_without_guessing_boxes():
    data = response()
    data["items"]["pages"][0]["items"] = [
        {"type": "list", "items": [{"type": "text", "value": "Nested", "md": "Nested"}]},
        {"type": "table", "md": "| A |", "rows": [["A"]]},
    ]
    parsed = normalize_v2_result(DOCUMENT_ID, data, 1)
    parent, child, table = parsed.pages[0].elements
    assert child.parent_element_id == parent.element_id
    assert table.attributes["rows"] == [["A"]]
    assert table.bbox is None


def test_absent_optional_items_keeps_page_level_fallback():
    data = response()
    data.pop("items")
    assert normalize_v2_result(DOCUMENT_ID, data, 1).pages[0].elements == []


@pytest.mark.parametrize(
    "change", ["job-failed", "page-failed", "items-failed", "missing-number", "duplicate-items"]
)
def test_failed_or_ambiguous_provider_pages_are_rejected(change):
    data = deepcopy(response())
    if change == "job-failed":
        data["job"]["status"] = "FAILED"
    if change == "page-failed":
        data["markdown"]["pages"][0]["success"] = False
    if change == "items-failed":
        data["items"]["pages"][0]["success"] = False
    if change == "missing-number":
        data["markdown"]["pages"][0].pop("page_number")
    if change == "duplicate-items":
        data["items"]["pages"].append(data["items"]["pages"][0])
    with pytest.raises(ParsingError):
        normalize_v2_result(DOCUMENT_ID, data, 1)
