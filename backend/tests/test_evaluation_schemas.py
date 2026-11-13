"""Deterministic unit tests for evaluation schemas and benchmark dataset."""

import json
from pathlib import Path

from evaluation.schemas import EvaluationReportSummary, EvaluationSample


def test_evaluation_sample_schema():
    """Verify EvaluationSample validation and serialization."""
    sample = EvaluationSample(
        sample_id="test_001",
        user_question="What is the architecture?",
        retrieved_contexts=["Context text 1", "Context text 2"],
        generated_answer="It is a transformer.",
        reference_answer="The architecture is the Transformer.",
        retrieved_chunk_ids=["chunk_1", "chunk_2"],
        source_page_numbers=[1, 2],
        model_configuration={"model": "gpt-4o", "k": 5},
        is_answerable=True,
    )
    assert sample.sample_id == "test_001"
    assert len(sample.retrieved_contexts) == 2
    assert sample.source_page_numbers == [1, 2]
    assert sample.is_answerable is True


def test_evaluation_report_summary():
    """Verify EvaluationReportSummary creation."""
    summary = EvaluationReportSummary(
        run_id="run_2026_11_10",
        total_samples=10,
        retrieval_strategy="hybrid_rrf",
        faithfulness_score=0.95,
        answer_relevancy_score=0.92,
        context_precision_score=0.88,
        context_recall_score=0.90,
    )
    assert summary.run_id == "run_2026_11_10"
    assert summary.faithfulness_score == 0.95
    assert summary.retrieval_strategy == "hybrid_rrf"


def test_benchmark_dataset_integrity():
    """Verify the curated benchmark dataset is valid JSON and contains required keys."""
    dataset_path = Path("evaluation/benchmark_dataset.json")
    assert dataset_path.exists()

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) >= 5

    # Ensure both answerable and unanswerable samples exist (Rule 14)
    has_answerable = any(item.get("is_answerable") is True for item in data)
    has_unanswerable = any(item.get("is_answerable") is False for item in data)
    assert has_answerable, "Benchmark dataset must contain answerable questions"
    assert has_unanswerable, "Benchmark dataset must contain unanswerable questions"

    for item in data:
        assert "sample_id" in item
        assert "user_question" in item
        assert "reference_answer" in item
        assert "is_answerable" in item
