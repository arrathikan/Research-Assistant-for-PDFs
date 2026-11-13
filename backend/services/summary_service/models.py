"""Strict model output and source-verified public summary contracts."""

import json
from datetime import datetime, timezone
from hashlib import sha256
from typing import Literal

from backend.services.document_processor.chunk_models import DocumentChunk
from backend.shared.config import Settings
from backend.shared.models import StructuredSummary
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

WORKFLOW_VERSION = "grounded-summary-v2"
UNAVAILABLE = "Not stated in the document."
SummaryField = Literal[
    "title", "authors", "abstract", "problem_statement", "methodology", "key_results", "conclusion"
]
TEXT_FIELDS = ("title", "abstract", "problem_statement", "methodology", "key_results", "conclusion")


class SummaryError(RuntimeError):
    """Safe summary error; never includes provider messages or paper text."""


class SummaryValidationError(SummaryError):
    """A model response needs a bounded targeted correction."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Evidence(StrictModel):
    chunk_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    page_number: int = Field(ge=1, strict=True)
    quote: str = Field(min_length=1, max_length=400)


class SummaryText(StrictModel):
    text: str | None = Field(max_length=2000)
    sources: list[Evidence] = Field(max_length=3)

    @model_validator(mode="after")
    def require_evidence_or_explicit_absence(self) -> "SummaryText":
        if self.text == "" or bool(self.text) != bool(self.sources):
            raise ValueError("Use nonempty text with evidence, or null with an empty source list")
        return self


class SummaryAuthors(StrictModel):
    names: list[str] = Field(max_length=40)
    sources: list[Evidence] = Field(max_length=3)

    @model_validator(mode="after")
    def require_evidence_or_explicit_absence(self) -> "SummaryAuthors":
        if any(not name or len(name) > 150 for name in self.names):
            raise ValueError("Author names must be nonempty and at most 150 characters")
        if bool(self.names) != bool(self.sources):
            raise ValueError("Author names require evidence; unavailable authors use empty lists")
        return self


class SummaryDraft(StrictModel):
    title: SummaryText
    authors: SummaryAuthors
    abstract: SummaryText
    problem_statement: SummaryText
    methodology: SummaryText
    key_results: SummaryText
    conclusion: SummaryText


class SummarySource(Evidence):
    field: SummaryField


class SummaryResult(StructuredSummary):
    model_config = ConfigDict(validate_default=True)
    chunk_set_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    summary_profile_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    llm_model: str
    workflow_version: str = WORKFLOW_VERSION
    sources: list[SummarySource]
    unavailable_fields: list[SummaryField]

    @field_validator("generated_at")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        value = value.astimezone(timezone.utc)
        return value.replace(microsecond=value.microsecond // 1000 * 1000)


def summary_profile_id(settings: Settings) -> str:
    definition = {
        "workflow": WORKFLOW_VERSION,
        "schema": SummaryDraft.model_json_schema(),
        "model": settings.primary_reasoning_model,
        "temperature": None
        if settings.primary_reasoning_model.startswith("openai/gpt-5")
        else settings.llm_temperature,
        "reasoning_effort": "low"
        if settings.primary_reasoning_model.startswith("openai/gpt-5")
        else None,
        "output_tokens": settings.llm_max_output_tokens,
        "context_bytes": settings.summary_context_bytes,
        "max_windows": settings.summary_max_windows,
        "validation_retries": settings.summary_validation_retries,
    }
    return sha256(
        json.dumps(definition, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def validate_draft(raw: str, chunks: list[DocumentChunk]) -> SummaryDraft:
    try:
        draft = SummaryDraft.model_validate_json(raw)
    except ValidationError as error:
        # Report field paths only: raw validation errors can contain source text.
        paths = sorted({".".join(map(str, item["loc"])) or "response" for item in error.errors()})
        raise SummaryValidationError("Correct schema fields: " + ", ".join(paths)) from None
    by_id = {chunk.id: chunk for chunk in chunks}
    for field in (*TEXT_FIELDS, "authors"):
        for source in getattr(draft, field).sources:
            chunk = by_id.get(source.chunk_id)
            quote = " ".join(source.quote.split())
            if chunk is None or not any(
                span.page_number == source.page_number and quote in " ".join(span.text.split())
                for span in chunk.page_spans
            ):
                raise SummaryValidationError(
                    f"Correct {field}.sources: use a supplied chunk ID, its page and an exact source quote. "
                    "Copy a short contiguous passage; do not insert ellipses, paraphrase, "
                    "or remove Markdown. Shorten the quote instead of abbreviating it."
                )
    return draft


def public_summary(
    draft: SummaryDraft, chunks: list[DocumentChunk], settings: Settings
) -> SummaryResult:
    fields = {field: getattr(draft, field).text or UNAVAILABLE for field in TEXT_FIELDS}
    missing: list[SummaryField] = [
        field for field in TEXT_FIELDS if getattr(draft, field).text is None
    ]
    if not draft.authors.names:
        missing.append("authors")
    sources = [
        SummarySource(field=field, **source.model_dump())
        for field in (*TEXT_FIELDS, "authors")
        for source in getattr(draft, field).sources
    ]
    return SummaryResult(
        document_id=chunks[0].document_id,
        chunk_set_id=chunks[0].chunk_set_id,
        summary_profile_id=summary_profile_id(settings),
        llm_model=settings.primary_reasoning_model,
        authors=draft.authors.names,
        sources=sources,
        unavailable_fields=missing,
        **fields,
    )
