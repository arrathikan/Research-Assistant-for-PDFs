"""Deterministic reporting tests: controlled fixture scores are not benchmark claims."""

import json

import pytest
from backend.tests.test_evaluation_metrics import record
from backend.tests.test_hybrid_retrieval import SCOPE
from evaluation.models import METRIC_NAMES, CollectionRun, MetricValue
from evaluation.report import (
    CRITERIA,
    EvaluationReport,
    ManualAssessment,
    ScoredCase,
    deterministic_checks,
    markdown,
    paired_comparison,
    summary,
    write_report,
)
from pydantic import ValidationError


def report():
    hybrid = record()
    semantic = hybrid.model_copy(deep=True, update={"strategy": "semantic"})
    run = CollectionRun(
        dataset_id="unit-fixture",
        dataset_version="test",
        dataset_size=1,
        dataset_sha256="a" * 64,
        git_commit="unit-fixture",
        source_scopes={hybrid.case.document_key: SCOPE},
        records=[hybrid, semantic],
    )
    rows = [
        ScoredCase(
            sample_id=item.case.sample_id,
            strategy=item.strategy,
            metrics={
                name: MetricValue(status="ok", value=0 if item.strategy == "hybrid" else 0.5)
                for name in METRIC_NAMES
            },
            checks=deterministic_checks(item),
        )
        for item in run.records
    ]
    return EvaluationReport(
        collection=run,
        evaluator={"source": "unit-test fixtures, no provider run"},
        request_usage={"llm_requests": 0},
        status="complete",
        rows=rows,
    )


def test_means_preserve_real_zero_and_comparison_uses_paired_cases():
    result = report()
    assert summary(result)["hybrid"]["faithfulness"] == {
        "mean": 0,
        "scored": 1,
        "skipped": 0,
        "errors": 0,
    }
    assert paired_comparison(result)["faithfulness"] == {
        "paired_samples": 1,
        "mean_hybrid_minus_semantic": -0.5,
    }


def test_failed_metrics_are_excluded_with_visible_coverage_not_imputed():
    result = report()
    result.rows[0].metrics["faithfulness"] = MetricValue(status="error", reason="failed_evaluator")
    result.status = "partial"
    assert summary(result)["hybrid"]["faithfulness"]["mean"] is None
    assert paired_comparison(result)["faithfulness"]["paired_samples"] == 0
    text = markdown(result)
    assert "failed_evaluator" in text and "Flagged" in text
    assert "not an overall accuracy percentage" in text


def test_missing_citations_and_changed_quotes_fail_deterministic_checks():
    item = record()
    item.output.response.citations = []
    assert deterministic_checks(item)["citations_present_when_answered"] is False
    item = record()
    item.output.response.citations[0].quote_snippet = "Fabricated quote absent from context"
    checks = deterministic_checks(item)
    assert checks["quote_in_context"] is False and checks["citation_identity_and_scope"] is False


def test_json_and_markdown_export_is_valid_private_and_never_overwrites(tmp_path):
    result = report()
    path, md = write_report(result, tmp_path)
    assert EvaluationReport.model_validate_json(path.read_text()) == result
    assert path.stat().st_mode & 0o777 == 0o600
    assert "Metric means and coverage" in md.read_text()
    assert json.loads(path.read_text())["status"] == "complete"
    assert json.loads(path.read_text())["metric_summary"]["hybrid"]["faithfulness"]["mean"] == 0
    with pytest.raises(FileExistsError):
        write_report(result, tmp_path)


def test_manual_reviews_need_provenance_and_are_bound_to_actual_result():
    with pytest.raises(ValidationError):
        ManualAssessment(result_sha256="a" * 64, outcomes={key: "pass" for key in CRITERIA})
    result = report()
    data = result.model_dump(mode="json")
    data["rows"][0]["manual"] = {
        "result_sha256": "f" * 64,
        "outcomes": {key: "pending" for key in CRITERIA},
    }
    with pytest.raises(ValidationError):
        EvaluationReport.model_validate(data)


def test_markdown_treats_model_text_as_data():
    result = report()
    result.collection.records[
        0
    ].output.response.answer = "<script>alert(1)</script> [link](https://example.com)"
    text = markdown(result)
    assert "<script>" not in text and "&lt;script&gt;" in text


def test_paired_comparison_rejects_different_case_content():
    data = report().model_dump(mode="json")
    data["collection"]["records"][1]["case"]["user_question"] = "Different question"
    with pytest.raises(ValidationError):
        EvaluationReport.model_validate(data)
