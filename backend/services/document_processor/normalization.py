"""Normalize the installed LlamaParse v1 JSON contract without guessing pages."""

from math import isfinite
from typing import Any

from backend.services.document_processor.parsed_models import (
    BoundingBox,
    ParsedDocument,
    ParsedPage,
    ParsingError,
    SourceElement,
)
from pydantic import ValidationError


def _dimension(value: object) -> float | None:
    if (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and isfinite(value)
        and value > 0
    ):
        return float(value)
    return None


def _bbox(value: object, normalized: bool) -> BoundingBox | None:
    if not isinstance(value, dict):
        return None
    try:
        return BoundingBox(
            x=value["x"],
            y=value["y"],
            width=value["w"],
            height=value["h"],
            coordinate_system="normalized" if normalized else "provider",
        )
    except (KeyError, ValidationError):
        # Optional bad coordinates do not destroy otherwise useful page text.
        return None


def _elements(document_id: str, page_number: int, page: dict[str, Any]) -> list[SourceElement]:
    elements: list[SourceElement] = []
    for source in ("items", "layout"):
        items = page.get(source) or []
        if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
            raise ParsingError("Parser returned invalid source elements")
        for item in items:
            index = len(elements)
            text = item.get("text", "")
            markdown = item.get("md", "")
            kind = item.get("type", item.get("label", "unknown"))
            if not all(isinstance(value, str) for value in (text, markdown, kind)):
                raise ParsingError("Parser returned invalid source text")
            provider_id = item.get("id")
            elements.append(
                SourceElement(
                    element_id=f"{document_id}:p{page_number}:e{index}",
                    document_id=document_id,
                    page_number=page_number,
                    element_index=index,
                    kind=kind,
                    text=text,
                    markdown=markdown,
                    source=source,
                    provider_element_id=str(provider_id)
                    if isinstance(provider_id, (str, int))
                    else None,
                    bbox=_bbox(
                        item.get("bbox") if source == "layout" else item.get("bBox"),
                        source == "layout",
                    ),
                )
            )
    return elements


def normalize_parsed_pages(
    document_id: str, response: object, expected_page_count: int
) -> ParsedDocument:
    """Require exactly one full PDF result with explicit 1-based page references.

    Item bBox units remain provider-defined. Only layout bbox uses the documented
    normalized-page convention. Never attach a layout box to unrelated item text.
    """
    if not isinstance(response, list) or len(response) != 1 or not isinstance(response[0], dict):
        raise ParsingError("Parser must return exactly one document")
    result = response[0]
    pages = result.get("pages")
    if not isinstance(pages, list) or len(pages) != expected_page_count or not pages:
        raise ParsingError("Parser page count does not match the original PDF")
    normalized: list[ParsedPage] = []
    seen: set[int] = set()
    for page in pages:
        if not isinstance(page, dict):
            raise ParsingError("Parser returned an invalid page")
        number = page.get("page")
        if not isinstance(number, int) or isinstance(number, bool) or number < 1 or number in seen:
            raise ParsingError("Parser returned invalid or duplicate page numbers")
        seen.add(number)
        markdown = page.get("md", "")
        text = page.get("text", "")
        if not isinstance(markdown, str) or not isinstance(text, str):
            raise ParsingError("Parser returned invalid page text")
        normalized.append(
            ParsedPage(
                document_id=document_id,
                page_number=number,
                markdown=markdown if markdown.strip() else text,
                width=_dimension(page.get("width")),
                height=_dimension(page.get("height")),
                elements=_elements(document_id, number, page),
            )
        )
    if seen != set(range(1, expected_page_count + 1)):
        raise ParsingError("Parser omitted or misnumbered original pages")
    normalized.sort(key=lambda page: page.page_number)
    if not any(page.markdown.strip() for page in normalized):
        raise ParsingError("The PDF produced no extractable text")
    job_id = result.get("job_id")
    return ParsedDocument(
        document_id=document_id,
        pages=normalized,
        provider_job_id=job_id if isinstance(job_id, str) else None,
    )
