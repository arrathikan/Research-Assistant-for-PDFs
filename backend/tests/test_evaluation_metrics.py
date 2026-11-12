"""Deterministic metric failure/applicability checks; fixture scores are not benchmark results."""

from pathlib import Path
from unittest.mock import Mock

import pytest
from backend.services.rag_service.chain import answer_with_trace
from backend.services.rag_service.models import RetrievalHit
from backend.shared.config import Settings
from backend.tests.test_evaluation_collection import completion
from backend.tests.test_hybrid_retrieval import CHUNKS, SCOPE
from evaluation.dataset import load_dataset
from evaluation.metrics import score_record
from evaluation.models import METRIC_NAMES, CollectedCase, MetricValue
from pydantic import ValidationError


def record():
    dataset = load_dataset(Path("evaluation/datasets/rag_test_cases.json"))
    case = dataset.cases[0]
    output = answer_with_trace(
        case.user_question,
        SCOPE,
        [RetrievalHit(chunk=CHUNKS[0])],
        Settings(_env_file=None),
        "a" * 32,
        "b" * 32,
        complete=completion,
    )
    return CollectedCase(case=case, strategy="hybrid", output=output, shared_retrieval_ms=1)


def test_real_zero_scores_are_retained_and_not_treated_as_missing():
    scored = score_record(record(), lambda *_: {name: 0.0 for name in METRIC_NAMES})
    assert all(metric.status == "ok" and metric.value == 0 for metric in scored.values())


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -2, 1.1, True, "0.9", None])
def test_invalid_results_never_become_valid_scores(bad):
    scored = score_record(record(), lambda *_: {name: bad for name in METRIC_NAMES})
    assert all(metric.status == "error" and metric.value is None for metric in scored.values())


def test_failed_evaluator_calls_are_recorded_without_raw_errors():
    scored = score_record(record(), Mock(side_effect=RuntimeError("private prompt response")))
    assert all(metric.status == "error" for metric in scored.values())
    assert "private prompt" not in str(scored)


def test_reference_metrics_are_skipped_without_reference_answer():
    item = record()
    item.case = item.case.model_copy(update={"reference_answer": None})
    execute = Mock(return_value={"faithfulness": 0.5, "answer_relevancy": 0.5})
    scored = score_record(item, execute)
    assert execute.call_args.args[1] == ["faithfulness", "answer_relevancy"]
    assert scored["context_recall"].reason == "reference_missing"


def test_empty_contexts_abstention_and_unanswerable_cases_do_not_invent_metrics():
    item = record()
    item.output.trace.retrieved_contexts = []
    item.output.response.is_out_of_scope = True
    assert score_record(item, Mock())["faithfulness"].reason == "contexts_empty"
    item.case = load_dataset(Path("evaluation/datasets/rag_test_cases.json")).cases[-1]
    execute = Mock()
    scored = score_record(item, execute)
    execute.assert_not_called()
    assert all(metric.status == "skipped" and metric.value is None for metric in scored.values())


def test_collection_failure_has_no_evaluation_score():
    item = record().model_copy(update={"output": None, "error_code": "retrieval_failed"})
    execute = Mock()
    scored = score_record(item, execute)
    assert all(metric.status == "error" for metric in scored.values())
    execute.assert_not_called()


def test_metric_state_cannot_hide_a_failed_or_uncomputed_score():
    with pytest.raises(ValidationError):
        MetricValue(status="error", value=0.5, reason="failed")
    with pytest.raises(ValidationError):
        MetricValue(status="ok", value=None)


@pytest.mark.parametrize("result", [None, [], 42])
def test_invalid_response_shapes_are_explicit_errors(result):
    scores = score_record(record(), lambda *_: result)
    assert all(value.status == "error" and value.value is None for value in scores.values())
