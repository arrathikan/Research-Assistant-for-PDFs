"""Private collection artifacts and explicit per-metric result states."""

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import AwareDatetime, Field, model_validator

from backend.services.rag_service.models import PipelineOutput, RetrievalScope
from evaluation.dataset import BenchmarkCase, ManualReview, StrictModel, case_hash

Strategy = Literal["hybrid", "semantic"]
MetricName = Literal[
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
    "factual_correctness",
]
METRIC_NAMES = (
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
    "factual_correctness",
)


class CollectedCase(StrictModel):
    case: BenchmarkCase
    strategy: Strategy
    review: ManualReview | None = None
    output: PipelineOutput | None = None
    error_code: (
        Literal["retrieval_failed", "generation_failed", "source_changed"] | None
    ) = None
    shared_retrieval_ms: float = Field(ge=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def require_result_or_error(self) -> "CollectedCase":
        if (self.output is None) == (self.error_code is None):
            raise ValueError(
                "Collection requires either a real output or an explicit failure"
            )
        if self.review and self.review.case_sha256 != case_hash(self.case):
            raise ValueError("Source review does not match this case")
        if self.output is not None:
            trace = self.output.trace
            if len(trace.retrieved_contexts) != len(trace.retrieved_chunk_ids) or len(
                trace.source_pages
            ) != len(trace.retrieved_contexts):
                raise ValueError("Collected context identities and pages must align")
            if (
                trace.question != self.case.user_question
                or trace.answer != self.output.response.answer
                or trace.document_id != self.output.response.document_id
            ):
                raise ValueError("Collected response/trace attribution is inconsistent")
        return self


class CollectionRun(StrictModel):
    schema_version: Literal[1] = 1
    run_id: str = Field(default_factory=lambda: uuid4().hex, pattern=r"^[0-9a-f]{32}$")
    created_at: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))
    dataset_id: str
    dataset_version: str
    dataset_size: int = Field(ge=1)
    dataset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    git_commit: str
    source_scopes: dict[str, RetrievalScope]
    records: list[CollectedCase]

    @model_validator(mode="after")
    def unique_records(self) -> "CollectionRun":
        keys = [(item.case.sample_id, item.strategy) for item in self.records]
        if len(keys) != len(set(keys)):
            raise ValueError(
                "Duplicate sample/strategy results cannot be silently averaged"
            )
        case_versions = {}
        for item in self.records:
            digest = case_hash(item.case)
            if (
                item.case.sample_id in case_versions
                and case_versions[item.case.sample_id] != digest
            ):
                raise ValueError("Paired strategies must use identical benchmark cases")
            case_versions[item.case.sample_id] = digest
            if item.output is not None:
                scope = self.source_scopes.get(item.case.document_key)
                if (
                    scope is None
                    or item.output.trace.document_id != scope.document_id
                    or item.output.trace.configuration.get("chunk_set_id")
                    != scope.chunk_set_id
                ):
                    raise ValueError(
                        "Collected output belongs to a different bound source"
                    )
        return self


class MetricValue(StrictModel):
    status: Literal["ok", "skipped", "error"]
    value: float | None = Field(default=None, ge=-1, le=1, allow_inf_nan=False)
    reason: str | None = None

    @model_validator(mode="after")
    def require_real_score_or_reason(self) -> "MetricValue":
        if self.status == "ok" and (self.value is None or self.reason is not None):
            raise ValueError("Successful metrics need a finite score")
        if self.status != "ok" and (self.value is not None or not self.reason):
            raise ValueError(
                "Skipped/failed metrics need a reason and no fabricated score"
            )
        return self
