"""Five real Ragas metrics with explicit applicability, missing values and failures."""

import logging
import math
import numbers
import os
from collections.abc import Callable
from importlib.metadata import version

from backend.shared.config import Settings
from evaluation.judge import RequestBudget, build_evaluator
from evaluation.models import METRIC_NAMES, CollectedCase, MetricValue
from evaluation.settings import EvaluationSettings

MetricExecutor = Callable[[dict, list[str]], dict]


def score_record(
    record: CollectedCase, execute: MetricExecutor
) -> dict[str, MetricValue]:
    if record.output is None:
        return {
            name: MetricValue(status="error", reason=record.error_code)
            for name in METRIC_NAMES
        }
    if not record.case.is_answerable:
        return {
            name: MetricValue(
                status="skipped", reason="unanswerable_case_use_guardrail_review"
            )
            for name in METRIC_NAMES
        }
    output, skipped = record.output, {}
    for name in METRIC_NAMES:
        if (
            name in ("context_precision", "context_recall", "factual_correctness")
            and not record.case.reference_answer
        ):
            skipped[name] = "reference_missing"
        elif (
            name in ("faithfulness", "context_precision", "context_recall")
            and not output.trace.retrieved_contexts
        ):
            skipped[name] = "contexts_empty"
        elif (
            name in ("faithfulness", "answer_relevancy", "factual_correctness")
            and output.response.is_out_of_scope
        ):
            skipped[name] = "abstention_has_no_factual_answer"
    selected = [name for name in METRIC_NAMES if name not in skipped]
    results = {
        name: MetricValue(status="skipped", reason=reason)
        for name, reason in skipped.items()
    }
    sample = {
        "user_input": record.case.user_question,
        "response": output.response.answer,
        "retrieved_contexts": output.trace.retrieved_contexts,
    }
    if record.case.reference_answer:
        sample["reference"] = record.case.reference_answer
    try:
        raw = execute(sample, selected) if selected else {}
    except Exception:  # noqa: BLE001 -- provider boundary: retain failure states without leaking raw evaluator output.
        return {
            **results,
            **{
                name: MetricValue(status="error", reason="evaluator_call_failed")
                for name in selected
            },
        }
    if not isinstance(raw, dict):
        return {
            **results,
            **{
                name: MetricValue(
                    status="error", reason="invalid_metric_response_shape"
                )
                for name in selected
            },
        }
    for name in selected:
        value = raw.get(name)
        minimum = -1 if name == "answer_relevancy" else 0
        if (
            isinstance(value, bool)
            or not isinstance(value, numbers.Real)
            or not math.isfinite(float(value))
            or not minimum <= float(value) <= 1
        ):
            results[name] = MetricValue(
                status="error", reason="invalid_or_missing_metric_result"
            )
        else:
            results[name] = MetricValue(status="ok", value=float(value))
    return results


class RagasRunner:
    def __init__(self, settings: Settings, config: EvaluationSettings):
        os.environ["RAGAS_DO_NOT_TRACK"] = "true"
        if version("ragas") != "0.2.15":
            raise ValueError("Install the verified optional evaluation requirements")
        self.config, self.budget = config, RequestBudget(config)
        self.llm, self.embeddings = build_evaluator(settings, config, self.budget)
        # Evaluator failures belong in score states, not private prompt/body logs.
        logging.getLogger("ragas").setLevel(logging.CRITICAL)

    def __call__(self, sample: dict, names: list[str]) -> dict:
        from ragas import EvaluationDataset, evaluate
        from ragas.metrics import (
            FactualCorrectness,
            Faithfulness,
            LLMContextPrecisionWithReference,
            LLMContextRecall,
            ResponseRelevancy,
        )
        from ragas.run_config import RunConfig

        factories = {
            "faithfulness": lambda: Faithfulness(llm=self.llm),
            "answer_relevancy": lambda: ResponseRelevancy(
                llm=self.llm,
                embeddings=self.embeddings,
                strictness=self.config.relevancy_questions,
            ),
            "context_precision": lambda: LLMContextPrecisionWithReference(
                name="context_precision", llm=self.llm
            ),
            "context_recall": lambda: LLMContextRecall(llm=self.llm),
            "factual_correctness": lambda: FactualCorrectness(llm=self.llm, mode="f1"),
        }
        metrics = [factories[name]() for name in names]
        result = evaluate(
            EvaluationDataset.from_list([sample]),
            metrics=metrics,
            llm=self.llm,
            embeddings=self.embeddings,
            run_config=RunConfig(
                timeout=self.config.metric_timeout_seconds,
                max_retries=1,
                max_wait=1,
                max_workers=self.config.max_workers,
                seed=42,
            ),
            raise_exceptions=False,
            show_progress=False,
        )
        scores = result.scores[0]
        return {
            name: scores.get(
                "factual_correctness(mode=f1)"
                if name == "factual_correctness"
                else name
            )
            for name in names
        }

    def close(self) -> None:
        self.llm.close()
