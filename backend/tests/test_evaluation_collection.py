"""Real answer composition with controlled retrieval/model boundaries, never fake reports."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from backend.services.rag_service.models import RagUnavailable, RetrievalHit
from backend.shared.config import Settings
from backend.tests.test_hybrid_retrieval import CHUNKS, DOCUMENT_ID, SCOPE
from evaluation.collect import collect
from evaluation.dataset import DatasetError, load_dataset

SETTINGS = Settings(_env_file=None)


def dataset():
    all_cases = load_dataset(Path("evaluation/datasets/rag_test_cases.json"))
    return all_cases.model_copy(
        update={"cases": all_cases.cases[:1], "reviews": all_cases.reviews[:1]}
    )


def completion(system, prompt, schema):
    source = json.loads(prompt)["contexts"][0]
    page = source["pages"][0]
    return json.dumps(
        {
            "is_out_of_scope": False,
            "claims": [
                {
                    "text": "Synthetic controlled answer.",
                    "sources": [
                        {
                            "chunk_id": source["chunk_id"],
                            "page_number": page["page_number"],
                            "quote": page["text"][:40],
                        }
                    ],
                }
            ],
        }
    )


def test_collects_both_real_chain_outputs_without_writing_conversations():
    data, db = dataset(), MagicMock()
    key = data.cases[0].document_key
    document = SimpleNamespace(sha256=data.sources[key].pdf_sha256, page_count=17)
    hits = [RetrievalHit(chunk=CHUNKS[0])]
    with (
        patch("evaluation.collect.get_document", return_value=document),
        patch("evaluation.collect.current_scope", return_value=(SCOPE, CHUNKS)),
        patch(
            "evaluation.collect.retrieve_variants",
            return_value=(SCOPE, {"hybrid": hits, "semantic": hits}),
        ),
    ):
        result = collect(
            db, data, {key: DOCUMENT_ID}, SETTINGS, "synthetic-commit", complete=completion
        )
    assert len(result.records) == 2
    assert all(record.output.response.citations for record in result.records)
    assert {record.output.trace.configuration["retrieval"] for record in result.records} == {
        "hybrid",
        "semantic",
    }
    assert result.records[0].output.trace.retrieved_chunk_ids == [CHUNKS[0].id]
    db.chat_turns.insert_one.assert_not_called()


def test_wrong_source_binding_fails_before_paid_retrieval():
    data = dataset()
    key = data.cases[0].document_key
    with (
        patch(
            "evaluation.collect.get_document",
            return_value=SimpleNamespace(sha256="f" * 64, page_count=17),
        ),
        patch("evaluation.collect.retrieve_variants") as retrieval,
    ):
        with pytest.raises(DatasetError):
            collect(MagicMock(), data, {key: DOCUMENT_ID}, SETTINGS, "synthetic")
    retrieval.assert_not_called()


def test_generation_failures_are_recorded_without_answer_or_private_error_content():
    data = dataset()
    key = data.cases[0].document_key
    with (
        patch(
            "evaluation.collect.get_document",
            return_value=SimpleNamespace(sha256=data.sources[key].pdf_sha256, page_count=17),
        ),
        patch("evaluation.collect.current_scope", return_value=(SCOPE, CHUNKS)),
        patch(
            "evaluation.collect.retrieve_variants",
            return_value=(SCOPE, {"hybrid": [RetrievalHit(chunk=CHUNKS[0])], "semantic": []}),
        ),
        patch(
            "evaluation.collect.answer_with_trace",
            side_effect=RagUnavailable("private provider detail"),
        ),
    ):
        result = collect(MagicMock(), data, {key: DOCUMENT_ID}, SETTINGS, "synthetic")
    assert all(
        record.output is None and record.error_code == "generation_failed"
        for record in result.records
    )
    assert "private provider detail" not in result.model_dump_json()


def test_retrieval_failures_never_invent_contexts_or_answers():
    data = dataset()
    key = data.cases[0].document_key
    with (
        patch(
            "evaluation.collect.get_document",
            return_value=SimpleNamespace(sha256=data.sources[key].pdf_sha256, page_count=17),
        ),
        patch("evaluation.collect.current_scope", return_value=(SCOPE, CHUNKS)),
        patch("evaluation.collect.retrieve_variants", side_effect=RagUnavailable("private")),
    ):
        result = collect(MagicMock(), data, {key: DOCUMENT_ID}, SETTINGS, "synthetic")
    assert all(record.error_code == "retrieval_failed" for record in result.records)


def test_seed_history_is_used_for_actual_retrieval_and_retained_without_chat_writes():
    data, db = dataset(), MagicMock()
    case = data.cases[0].model_copy(update={"user_question": "What about its title?"})
    data = data.model_copy(update={"cases": [case], "reviews": []})
    key = case.document_key
    history = [
        {"question": "What is the main topic of this paper?", "answer": "A controlled fixture."}
    ]
    hits = [RetrievalHit(chunk=CHUNKS[0])]
    with (
        patch(
            "evaluation.collect.get_document",
            return_value=SimpleNamespace(sha256=data.sources[key].pdf_sha256, page_count=17),
        ),
        patch("evaluation.collect.current_scope", return_value=(SCOPE, CHUNKS)),
        patch(
            "evaluation.collect.retrieve_variants",
            return_value=(SCOPE, {"hybrid": hits, "semantic": hits}),
        ) as retrieval,
    ):
        run = collect(
            db,
            data,
            {key: DOCUMENT_ID},
            SETTINGS,
            "synthetic",
            complete=completion,
            history_by_sample={case.sample_id: history},
        )
    assert "main topic" in retrieval.call_args.args[2]
    assert run.records[0].output.trace.configuration["conversation_history"] == history
    assert (
        run.records[0].output.trace.configuration["evaluation_history"]
        == "seeded_history_no_chat_storage"
    )
    db.chat_turns.insert_one.assert_not_called()


def test_summary_collection_uses_the_same_summary_context_path_as_chat():
    data, db = dataset(), MagicMock()
    case = data.cases[0].model_copy(update={"user_question": "Summarize this research paper."})
    data = data.model_copy(update={"cases": [case], "reviews": []})
    key = case.document_key
    hits = [RetrievalHit(chunk=CHUNKS[0])]
    with (
        patch(
            "evaluation.collect.get_document",
            return_value=SimpleNamespace(sha256=data.sources[key].pdf_sha256, page_count=17),
        ),
        patch("evaluation.collect.current_scope", return_value=(SCOPE, CHUNKS)),
        patch(
            "evaluation.collect.summary_context",
            return_value=(hits, None, {"context_strategy": "section_samples"}),
        ) as summary,
        patch("evaluation.collect.retrieve_variants") as retrieval,
    ):
        run = collect(db, data, {key: DOCUMENT_ID}, SETTINGS, "synthetic", complete=completion)
    summary.assert_called_once()
    retrieval.assert_not_called()
    assert all(
        item.output.trace.configuration["question_intent"] == "summary" for item in run.records
    )
