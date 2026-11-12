"""Benchmark/source/review validation with no model calls or invented scores."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from evaluation.dataset import (
    BenchmarkDataset,
    DatasetError,
    case_hash,
    checklist,
    load_dataset,
    normalized_source,
    verify_pdf,
)
from pydantic import ValidationError

PATH = Path("evaluation/datasets/rag_test_cases.json")


def payload():
    return json.loads(PATH.read_text())


def test_source_grounded_dataset_has_twenty_cases_and_explicit_review_provenance():
    dataset = load_dataset(PATH)
    assert len(dataset.cases) == 20
    assert any(not case.is_answerable for case in dataset.cases)
    assert all(dataset.approved(case) for case in dataset.cases)
    assert {review.review_kind for review in dataset.reviews} == {"assistant"}
    assert dataset.sources[dataset.cases[0].document_key].license == "CC-BY-4.0"


@pytest.mark.parametrize(
    "change",
    [
        {"expected_page_numbers": [0]},
        {"expected_page_numbers": [True]},
        {"expected_page_numbers": [100]},
        {"source_evidence": []},
        {"document_key": "unknown"},
        {"is_answerable": False},
        {"sample_id": "bad/id"},
    ],
)
def test_invalid_cases_and_source_links_are_rejected(change):
    data = payload()
    data["reviews"] = []
    data["cases"][0].update(change)
    with pytest.raises(ValidationError):
        BenchmarkDataset.model_validate(data)


def test_duplicate_cases_and_stale_review_hashes_are_rejected():
    data = payload()
    data["cases"].append(deepcopy(data["cases"][0]))
    with pytest.raises(ValidationError):
        BenchmarkDataset.model_validate(data)
    data = payload()
    data["cases"][0]["reference_answer"] = "Changed after review"
    with pytest.raises(ValidationError):
        BenchmarkDataset.model_validate(data)


def test_unreviewed_dataset_requires_an_explicit_draft_run(tmp_path):
    data = payload()
    data["reviews"] = []
    target = tmp_path / "draft.json"
    target.write_text(json.dumps(data))
    with pytest.raises(DatasetError, match="manual review"):
        load_dataset(target)
    assert load_dataset(target, require_reviewed=False).reviews == []


def test_missing_reference_cannot_be_approved_and_unanswerable_references_are_not_fabricated():
    data = payload()
    data["cases"][0]["reference_answer"] = None
    data["reviews"] = []
    dataset = BenchmarkDataset.model_validate(data)
    review = payload()["reviews"][0]
    review["case_sha256"] = case_hash(dataset.cases[0])
    data["reviews"] = [review]
    with pytest.raises(ValidationError):
        BenchmarkDataset.model_validate(data)
    data = payload()
    data["cases"][-1]["reference_answer"] = "Invented unavailable fact"
    with pytest.raises(ValidationError):
        BenchmarkDataset.model_validate(data)


def test_source_pdf_identity_is_checked_before_page_extraction():
    dataset = load_dataset(PATH)
    with pytest.raises(DatasetError, match="source version"):
        verify_pdf(dataset, dataset.cases[0].document_key, b"wrong PDF bytes")
    assert normalized_source("con-\ntext   ﬁdelity") == "context fidelity"


def test_review_checklist_includes_provenance_pages_and_case_hashes():
    dataset = load_dataset(PATH)
    text = checklist(dataset)
    assert "20/20" in text and "assistant / approved" in text
    assert case_hash(dataset.cases[0]) in text
    assert "#page=5" in text
    assert "independent human review" in text


def test_intent_dataset_covers_required_categories_and_preserves_seed_provenance():
    dataset = load_dataset(Path("evaluation/datasets/intent_test_cases.json"))
    assert {case.category for case in dataset.cases} == {
        "summary",
        "topic",
        "fact",
        "analysis",
        "comparison",
        "followup",
        "unanswerable",
        "general",
        "mixed",
    }
    assert len(dataset.cases) == 9
    assert all(dataset.approved(case) for case in dataset.cases)
    assert {review.review_kind for review in dataset.reviews} == {"assistant"}
    histories = json.loads(Path("evaluation/datasets/intent_history.json").read_text())
    followup = next(case for case in dataset.cases if case.category == "followup")
    assert set(histories) == {followup.sample_id}
    assert "encoder-decoder" in histories[followup.sample_id][0]["question"]
    assert "seed" in followup.review_note
