"""Validated score artifacts, paired comparisons and readable reports without invented results."""

import argparse
import hashlib
import html
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from statistics import fmean
from typing import Literal
from uuid import uuid4

from pydantic import AwareDatetime, Field, model_validator

from backend.services.rag_service.chain import GENERAL_HEADING
from backend.services.rag_service.citations import citation_id
from evaluation.dataset import StrictModel, normalized_source
from evaluation.models import (
    METRIC_NAMES,
    CollectedCase,
    CollectionRun,
    MetricName,
    MetricValue,
    Strategy,
)

CRITERIA = (
    "answer_correct",
    "evidence_support",
    "citation_pages",
    "source_text_matching",
    "unsupported_handling",
)


def result_hash(record: CollectedCase) -> str:
    data = json.dumps(
        record.model_dump(mode="json"),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(data.encode()).hexdigest()


class ManualAssessment(StrictModel):
    result_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reviewer: str | None = None
    review_kind: Literal["assistant", "human"] | None = None
    reviewed_at: AwareDatetime | None = None
    outcomes: dict[str, Literal["pass", "fail", "not_applicable", "pending"]]
    notes: str = ""

    @model_validator(mode="after")
    def require_attribution(self) -> "ManualAssessment":
        if set(self.outcomes) != set(CRITERIA):
            raise ValueError("Manual review requires all five review criteria")
        if any(value != "pending" for value in self.outcomes.values()) and (
            not self.reviewer
            or not self.review_kind
            or not self.reviewed_at
            or not self.notes
        ):
            raise ValueError(
                "Completed checks need reviewer, provenance, time and notes"
            )
        return self


class ScoredCase(StrictModel):
    sample_id: str
    strategy: Strategy
    metrics: dict[MetricName, MetricValue]
    checks: dict[str, bool | float | None]
    manual: ManualAssessment | None = None


class EvaluationReport(StrictModel):
    schema_version: Literal[1] = 1
    evaluation_id: str = Field(
        default_factory=lambda: uuid4().hex, pattern=r"^[0-9a-f]{32}$"
    )
    created_at: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))
    collection: CollectionRun
    evaluator: dict
    request_usage: dict[str, int]
    status: Literal["complete", "partial"]
    rows: list[ScoredCase]
    metric_summary: dict = Field(default_factory=dict)
    paired_summary: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_rows(self) -> "EvaluationReport":
        records = {
            (record.case.sample_id, record.strategy): record
            for record in self.collection.records
        }
        keys = [(row.sample_id, row.strategy) for row in self.rows]
        if len(keys) != len(set(keys)) or set(keys) != set(records):
            raise ValueError("Every collected record needs exactly one score row")
        for row in self.rows:
            if set(row.metrics) != set(METRIC_NAMES):
                raise ValueError(
                    "Every metric needs an explicit score, skip or error state"
                )
            if row.manual and row.manual.result_sha256 != result_hash(
                records[row.sample_id, row.strategy]
            ):
                raise ValueError("Manual review does not match this unchanged result")
        partial = any(
            metric.status == "error"
            for row in self.rows
            for metric in row.metrics.values()
        )
        if (self.status == "partial") != partial:
            raise ValueError("Run status must reflect evaluator/collection errors")
        calculated, paired = summary(self), paired_comparison(self)
        if self.metric_summary and self.metric_summary != calculated:
            raise ValueError(
                "Stored metric summary does not match the individual scores"
            )
        if self.paired_summary and self.paired_summary != paired:
            raise ValueError("Stored paired summary does not match paired scores")
        self.metric_summary, self.paired_summary = calculated, paired
        return self


def attach_manual_reviews(
    report: EvaluationReport, reviews: dict[str, ManualAssessment]
) -> EvaluationReport:
    """Create a new report revision without rerunning collection or paid metrics."""
    data = report.model_dump(mode="json")
    keys = {row.sample_id + ":" + row.strategy for row in report.rows}
    if not reviews or set(reviews) - keys:
        raise ValueError("Reviews must identify existing sample/strategy results")
    data["evaluation_id"] = uuid4().hex
    data["created_at"] = datetime.now(UTC).isoformat()
    data["evaluator"]["manual_review_of"] = report.evaluation_id
    for row in data["rows"]:
        review = reviews.get(row["sample_id"] + ":" + row["strategy"])
        if review is not None:
            row["manual"] = review.model_dump(mode="json")
    return EvaluationReport.model_validate(data)


def deterministic_checks(record: CollectedCase) -> dict[str, bool | float | None]:
    if record.output is None:
        return {
            "answerability_correct": None,
            "citations_present_when_answered": None,
            "citation_identity_and_scope": None,
            "quote_in_context": None,
            "expected_page_coverage": None,
        }
    response, trace = record.output.response, record.output.trace
    indexed = {
        identifier: (context, pages)
        for identifier, context, pages in zip(
            trace.retrieved_chunk_ids,
            trace.retrieved_contexts,
            trace.source_pages,
            strict=True,
        )
    }
    consistent, matching = True, True
    for citation in response.citations:
        source = indexed.get(citation.chunk_id)
        consistent &= (
            citation.document_id == response.document_id
            and citation.citation_id
            == citation_id(
                citation.document_id,
                citation.chunk_id,
                citation.page_number,
                citation.quote_snippet,
            )
            and source is not None
            and citation.page_number in source[1]
        )
        matching &= source is not None and normalized_source(
            citation.quote_snippet
        ) in normalized_source(source[0])
    expected = set(record.case.expected_page_numbers)
    retrieved = {page for pages in trace.source_pages for page in pages}
    checks = {
        "answerability_correct": response.is_out_of_scope
        == (not record.case.is_answerable),
        "citations_present_when_answered": response.is_out_of_scope
        or bool(response.citations),
        "citation_identity_and_scope": consistent,
        "quote_in_context": matching,
        "expected_page_coverage": len(expected & retrieved) / len(expected)
        if expected
        else None,
    }

    if record.case.category == "general":
        checks["general_background_labeled"] = GENERAL_HEADING in response.answer
        checks["general_has_no_paper_citations"] = not response.citations
    return checks


def summary(report: EvaluationReport) -> dict:
    result = {}
    for strategy in sorted({row.strategy for row in report.rows}):
        rows = [row for row in report.rows if row.strategy == strategy]
        result[strategy] = {}
        for name in METRIC_NAMES:
            values = [
                row.metrics[name].value
                for row in rows
                if row.metrics[name].status == "ok"
            ]
            result[strategy][name] = {
                "mean": fmean(values) if values else None,
                "scored": len(values),
                "skipped": sum(row.metrics[name].status == "skipped" for row in rows),
                "errors": sum(row.metrics[name].status == "error" for row in rows),
            }
    return result


def paired_comparison(report: EvaluationReport) -> dict:
    rows = {(row.sample_id, row.strategy): row for row in report.rows}
    comparison = {}
    for name in METRIC_NAMES:
        deltas = []
        for sample in {row.sample_id for row in report.rows}:
            a, b = rows.get((sample, "hybrid")), rows.get((sample, "semantic"))
            if a and b and a.metrics[name].status == b.metrics[name].status == "ok":
                deltas.append(a.metrics[name].value - b.metrics[name].value)
        comparison[name] = {
            "paired_samples": len(deltas),
            "mean_hybrid_minus_semantic": fmean(deltas) if deltas else None,
        }
    return comparison


def safe(value: object) -> str:
    return (
        html.escape(str(value))
        .replace("|", r"\|")
        .replace("[", r"\[")
        .replace("]", r"\]")
        .replace("\n", "<br>")
    )


def markdown(report: EvaluationReport) -> str:
    totals = summary(report)
    selected = len({record.case.sample_id for record in report.collection.records})
    review_kinds = sorted(
        {
            record.review.review_kind
            for record in report.collection.records
            if record.review
        }
    )
    lines = [
        "# ResearchAI offline RAG evaluation",
        "",
        f"Evaluation: `{report.evaluation_id}`",
        f"Date: {report.created_at.isoformat()}",
        f"Execution status: **{report.status}**",
        f"Dataset: {report.collection.dataset_id} / {report.collection.dataset_version}",
        f"Selected cases: {selected} of {report.collection.dataset_size}; strategy records: {len(report.rows)}.",
        f"Evaluated Git commit: `{report.collection.git_commit}`",
        f"Reference review provenance: {', '.join(review_kinds) or 'unreviewed'}.",
        f"Evaluator configuration: `{json.dumps(report.evaluator, sort_keys=True)}`",
        f"Request usage: `{json.dumps(report.request_usage, sort_keys=True)}`",
        "",
        "Scores are computed metric outputs, not an overall accuracy percentage. Missing/failed values are never replaced with zero.",
        "Unanswerable questions use abstention and manual checks rather than inappropriate reference-based metrics.",
        "Retrieval time is shared between paired rankings; answer-chain latency excludes that shared retrieval time.",
        "",
        "## Metric means and coverage",
        "",
        "| Strategy | Metric | Mean | Scored | Skipped | Errors |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for strategy, metrics in totals.items():
        for name, value in metrics.items():
            mean = f"{value['mean']:.4f}" if value["mean"] is not None else "—"
            lines.append(
                f"| {strategy} | {name} | {mean} | {value['scored']} | {value['skipped']} | {value['errors']} |"
            )
    lines.extend(
        [
            "",
            "## Paired comparison",
            "",
            "Positive deltas favor hybrid for these measured pairs only. No general superiority claim follows from a small or incomplete benchmark.",
            "",
            "| Metric | Paired cases | Mean hybrid − semantic |",
            "|---|---:|---:|",
        ]
    )
    for name, value in paired_comparison(report).items():
        delta = (
            f"{value['mean_hybrid_minus_semantic']:.4f}"
            if value["mean_hybrid_minus_semantic"] is not None
            else "—"
        )
        lines.append(f"| {name} | {value['paired_samples']} | {delta} |")
    records = {
        (record.case.sample_id, record.strategy): record
        for record in report.collection.records
    }
    lines.extend(["", "## Individual results and review", ""])
    for row in report.rows:
        record = records[row.sample_id, row.strategy]
        lines.extend(
            [
                f"### {row.sample_id} / {row.strategy}",
                "",
                f"Question: {safe(record.case.user_question)}",
                f"Reference: {safe(record.case.reference_answer or ('General knowledge: expected a labeled explanation without paper citations.' if record.case.category == 'general' else 'Not applicable: unsupported question; expected abstention.'))}",
                f"Answer: {safe(record.output.response.answer) if record.output else 'Unavailable: ' + str(record.error_code)}",
            ]
        )
        if record.output:
            trace = record.output.trace
            lines.extend(
                [
                    f"Pipeline configuration: `{json.dumps(trace.configuration, sort_keys=True)}`",
                    f"Answer-chain latency: {trace.latency_ms:.1f} ms; shared retrieval: {record.shared_retrieval_ms:.1f} ms.",
                    f"Retrieved chunk IDs: {safe(', '.join(trace.retrieved_chunk_ids))}; source pages: {safe(trace.source_pages)}.",
                ]
            )
        for name, metric in row.metrics.items():
            lines.append(
                f"- {name}: {metric.value if metric.status == 'ok' else metric.status + ' (' + str(metric.reason) + ')'}"
            )
        lines.append(
            f"Deterministic checks: `{json.dumps(row.checks, sort_keys=True)}`"
        )
        if any(value is False for value in row.checks.values()) or any(
            value.status == "error" for value in row.metrics.values()
        ):
            lines.append(
                "**Flagged:** execution or deterministic source/abstention check requires attention."
            )
        if row.manual:
            lines.append(
                f"Manual review ({row.manual.review_kind}, {safe(row.manual.reviewer)}): `{json.dumps(row.manual.outcomes, sort_keys=True)}` — {safe(row.manual.notes)}"
            )
        else:
            lines.append("Manual result review: pending.")
        lines.append("")
    lines.extend(
        [
            "## Limitations",
            "",
            "This is one paper and one model/pipeline configuration. LLM judges can vary or be wrong. Page coverage is a coarse deterministic diagnostic, not Ragas context recall. Reference approval and generated-answer review are separate. Assistant reviews are not independent human validation. See the JSON artifact for complete contexts and citations; do not publish private-paper runs.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(report: EvaluationReport, directory: Path) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"evaluation-{report.evaluation_id}.json"
    md = directory / f"evaluation-{report.evaluation_id}.md"
    for target, content in (
        (
            path,
            json.dumps(
                report.model_dump(mode="json"),
                ensure_ascii=False,
                indent=2,
                allow_nan=False,
            ),
        ),
        (md, markdown(report)),
    ):
        descriptor = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            stream.write(content.rstrip() + "\n")
    return path, md


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render an existing score artifact without paid calls"
    )
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = EvaluationReport.model_validate_json(args.report.read_text())
    with args.output.open("x") as stream:
        stream.write(markdown(report))


if __name__ == "__main__":
    main()
