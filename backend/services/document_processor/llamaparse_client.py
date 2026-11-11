"""LlamaParse v2 adapter using the supported unified provider SDK."""

from typing import Any

from backend.services.document_processor.normalization import normalize_parsed_pages
from backend.services.document_processor.parsed_models import ParsedDocument, ParsingError
from backend.shared.config import Settings
from llama_cloud import LlamaCloud


def _flatten_items(
    items: object,
    parent: int | None = None,
    result: list[dict[str, Any]] | None = None,
    depth: int = 0,
) -> list[dict[str, Any]]:
    if not isinstance(items, list) or depth > 50:
        raise ParsingError("Parser returned invalid nested source elements")
    if result is None:
        result = []
    for item in items:
        if not isinstance(item, dict):
            raise ParsingError("Parser returned an invalid source element")
        index = len(result)
        value = item.get("value")
        result.append(
            {
                "id": item.get("id"),
                "type": item.get("type") or "unknown",
                "md": item.get("md") or "",
                "text": value if isinstance(value, str) else "",
                "bounding_boxes": item.get("bbox") or [],
                "bbox_units": "points",
                "parent_index": parent,
                "attributes": {
                    key: item[key]
                    for key in ("rows", "html", "csv", "level", "caption", "confidence")
                    if item.get(key) is not None
                },
            }
        )
        if item.get("items") is not None:
            _flatten_items(item["items"], index, result, depth + 1)
    return result


def normalize_v2_result(document_id: str, data: dict[str, Any], page_count: int) -> ParsedDocument:
    job = data.get("job") or {}
    if job.get("status") != "COMPLETED":
        raise ParsingError("LlamaParse did not complete successfully")
    markdown_pages = (data.get("markdown") or {}).get("pages")
    if not isinstance(markdown_pages, list):
        raise ParsingError("LlamaParse returned no page Markdown")
    item_pages = (data.get("items") or {}).get("pages") or []
    if not isinstance(item_pages, list):
        raise ParsingError("LlamaParse returned invalid item pages")
    items_by_page: dict[int, dict[str, Any]] = {}
    for page in item_pages:
        if not isinstance(page, dict) or page.get("success") is not True:
            raise ParsingError("LlamaParse could not process a source page")
        number = page.get("page_number")
        if (
            not isinstance(number, int)
            or isinstance(number, bool)
            or number in items_by_page
            or not 1 <= number <= page_count
        ):
            raise ParsingError("LlamaParse returned ambiguous source pages")
        items_by_page[number] = page
    pages = []
    for page in markdown_pages:
        if not isinstance(page, dict) or page.get("success") is not True:
            raise ParsingError("LlamaParse could not process a Markdown page")
        number = page.get("page_number")
        if not isinstance(number, int) or isinstance(number, bool):
            raise ParsingError("LlamaParse omitted a page number")
        source = items_by_page.get(number, {})
        pages.append(
            {
                "page": number,
                "md": page.get("markdown"),
                "width": source.get("page_width"),
                "height": source.get("page_height"),
                "items": _flatten_items(source.get("items", [])),
            }
        )
    return normalize_parsed_pages(
        document_id, [{"job_id": job.get("id"), "pages": pages}], page_count
    )


def parse_with_llamaparse(
    document_id: str, content: bytes, page_count: int, settings: Settings
) -> ParsedDocument:
    if not settings.llama_cloud_api_key.strip() or settings.llama_cloud_api_key.startswith("your_"):
        raise ParsingError("LLAMA_CLOUD_API_KEY is not configured")
    try:
        with LlamaCloud(
            api_key=settings.llama_cloud_api_key,
            timeout=min(settings.llama_parse_timeout_seconds, 60),
            max_retries=0,
        ) as client:
            result = client.parsing.parse(
                upload_file=("source.pdf", content, "application/pdf"),
                tier=settings.llama_parse_tier,
                version=settings.llama_parse_version,
                expand=["markdown", "items", "metadata"],
                output_options={"markdown": {"tables": {"output_tables_as_markdown": True}}},
                timeout=settings.llama_parse_timeout_seconds,
                verbose=False,
            )
    except Exception:
        # SDK error messages may include request details. Never persist or log them.
        raise ParsingError("LlamaParse request failed or timed out") from None
    return normalize_v2_result(document_id, result.model_dump(mode="json"), page_count)
