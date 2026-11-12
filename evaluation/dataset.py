"""Versioned, source-grounded benchmarks with explicit manual-review provenance."""

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Annotated, Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    model_validator,
)


class DatasetError(ValueError):
    """Safe dataset error without private questions, answers or local file content."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SourceDocument(StrictModel):
    title: str = Field(min_length=1)
    authors: list[str] = Field(min_length=1)
    source_url: str = Field(pattern=r"^https://[^\s]+$")
    pdf_url: str = Field(pattern=r"^https://[^\s]+$")
    pdf_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    page_count: int = Field(ge=1, strict=True)
    license: str = Field(min_length=1)


class SourceEvidence(StrictModel):
    page_number: int = Field(ge=1, strict=True)
    section: str = Field(min_length=1)
    quote: str = Field(min_length=1, max_length=400)


class BenchmarkCase(StrictModel):
    sample_id: str = Field(pattern=r"^[a-z0-9_-]{1,80}$")
    document_key: str = Field(pattern=r"^[a-z0-9_-]{1,80}$")
    category: str = Field(min_length=1)
    user_question: str = Field(min_length=1, max_length=2000)
    reference_answer: str | None = Field(default=None, min_length=1, max_length=3000)
    is_answerable: bool = Field(strict=True)
    expected_page_numbers: list[Annotated[int, Field(strict=True, ge=1)]] = Field(
        default_factory=list
    )
    source_evidence: list[SourceEvidence] = Field(default_factory=list)
    review_note: str = ""

    @model_validator(mode="after")
    def validate_evidence(self) -> "BenchmarkCase":
        if any(
            type(page) is not int or page < 1 for page in self.expected_page_numbers
        ):
            raise ValueError("Expected pages must be positive integers")
        if len(set(self.expected_page_numbers)) != len(self.expected_page_numbers):
            raise ValueError("Expected pages must be unique")
        if self.is_answerable:
            if not self.source_evidence or not self.expected_page_numbers:
                raise ValueError(
                    "Answerable cases need source evidence and expected pages"
                )
            if {item.page_number for item in self.source_evidence} != set(
                self.expected_page_numbers
            ):
                raise ValueError("Evidence pages must match expected pages")
        elif (
            self.reference_answer is not None
            or self.source_evidence
            or self.expected_page_numbers
        ):
            raise ValueError(
                "Unanswerable cases use abstention, not invented reference facts"
            )
        return self


def case_hash(case: BenchmarkCase) -> str:
    value = json.dumps(
        case.model_dump(), sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    return hashlib.sha256(value.encode()).hexdigest()


class ManualReview(StrictModel):
    sample_id: str
    case_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_kind: Literal["human", "assistant"]
    reviewer: str = Field(min_length=1)
    reviewed_at: AwareDatetime
    decision: Literal["approved", "rejected"]
    notes: str = Field(min_length=1)


class BenchmarkDataset(StrictModel):
    schema_version: Literal[1] = 1
    dataset_id: str = Field(pattern=r"^[a-z0-9_-]{1,80}$")
    version: str = Field(min_length=1)
    sources: dict[str, SourceDocument]
    cases: list[BenchmarkCase] = Field(min_length=1, max_length=1000)
    reviews: list[ManualReview] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_links(self) -> "BenchmarkDataset":
        cases = {case.sample_id: case for case in self.cases}
        if len(cases) != len(self.cases):
            raise ValueError("Sample identifiers must be unique")
        for case in self.cases:
            source = self.sources.get(case.document_key)
            if source is None or any(
                page > source.page_count for page in case.expected_page_numbers
            ):
                raise ValueError("Unknown document or invalid source page")
        if len({review.sample_id for review in self.reviews}) != len(self.reviews):
            raise ValueError("Use one current manual review per case")
        for review in self.reviews:
            if review.sample_id not in cases or review.case_sha256 != case_hash(
                cases[review.sample_id]
            ):
                raise ValueError("Manual review is missing its unchanged source case")
            if (
                review.decision == "approved"
                and cases[review.sample_id].is_answerable
                and not cases[review.sample_id].reference_answer
            ):
                raise ValueError("Approved answerable cases require a reference answer")
        return self

    def approved(self, case: BenchmarkCase) -> bool:
        return any(
            review.sample_id == case.sample_id
            and review.decision == "approved"
            and review.case_sha256 == case_hash(case)
            for review in self.reviews
        )


def load_dataset(path: Path, require_reviewed: bool = True) -> BenchmarkDataset:
    try:
        if path.stat().st_size > 2_000_000:
            raise DatasetError("Benchmark dataset exceeds its size guard")
        dataset = BenchmarkDataset.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValidationError):
        raise DatasetError("Benchmark dataset could not be validated") from None
    if require_reviewed and not all(dataset.approved(case) for case in dataset.cases):
        raise DatasetError(
            "Benchmark still requires manual review; draft runs must be explicitly labeled"
        )
    return dataset


def normalized_source(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).replace("\u00ad", "")
    text = re.sub(r"(?<=\w)-\s+(?=\w)", "", text)
    return " ".join(text.split())


def verify_pdf(dataset: BenchmarkDataset, document_key: str, content: bytes) -> None:
    from io import BytesIO

    from pypdf import PdfReader

    source = dataset.sources[document_key]
    if hashlib.sha256(content).hexdigest() != source.pdf_sha256:
        raise DatasetError("PDF bytes do not match the benchmark source version")
    reader = PdfReader(BytesIO(content))
    if len(reader.pages) != source.page_count:
        raise DatasetError("PDF page count does not match the benchmark")
    text = [normalized_source(page.extract_text()) for page in reader.pages]
    for case in dataset.cases:
        if case.document_key == document_key:
            for item in case.source_evidence:
                if normalized_source(item.quote) not in text[item.page_number - 1]:
                    raise DatasetError(
                        f"Source anchor did not match for {case.sample_id}"
                    )


def checklist(dataset: BenchmarkDataset) -> str:
    lines = [
        "# Benchmark manual review",
        "",
        f"Approved source cases: {sum(dataset.approved(case) for case in dataset.cases)}/{len(dataset.cases)}.",
        "Review provenance is explicit: assistant review is source cross-checking by Codex; independent human review is recorded only when supplied.",
        "Review each answer against the linked PDF pages; check unsupported cases against the paper's scope.",
        "Approval records must include reviewer, timestamp, decision, notes and the unchanged case hash.",
        "",
    ]
    for case in dataset.cases:
        source = dataset.sources[case.document_key]
        review = next(
            (item for item in dataset.reviews if item.sample_id == case.sample_id), None
        )
        lines.extend(
            [
                f"## {case.sample_id}: {case.category}",
                "",
                f"Question: {case.user_question}",
                f"Reference: {case.reference_answer or 'Expected behavior: abstain; the paper does not establish this answer.'}",
                f"Case hash: `{case_hash(case)}`",
                "",
            ]
        )
        for item in case.source_evidence:
            lines.append(
                f"- [PDF page {item.page_number}, {item.section}]({source.pdf_url}#page={item.page_number}): {item.quote}"
            )
        lines.extend(
            [
                f"Reviewer note: {case.review_note}",
                "",
                f"- [{'x' if review else ' '}] Answer/reference checked against source.",
                f"- [{'x' if review else ' '}] Source pages and supporting passages checked.",
                f"- [{'x' if review else ' '}] Expected answerability checked.",
                f"- Reviewer / provenance / decision: {review.reviewer + ' / ' + review.review_kind + ' / ' + review.decision if review else 'pending'}",
                f"- Review comments: {review.notes if review else 'pending'}",
                "",
            ]
        )
    return "\n".join(lines)
