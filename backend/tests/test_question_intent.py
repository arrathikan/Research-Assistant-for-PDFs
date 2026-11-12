"""Routing hints are deterministic and keep history separate from source facts."""

import json
from unittest.mock import Mock, patch

import pytest
from backend.services.rag_service.chain import ABSTENTION, GENERAL_HEADING, answer_with_trace
from backend.services.rag_service.document_context import section_samples, summary_context
from backend.services.rag_service.intent import plan_question
from backend.services.rag_service.models import RagNotReady, RagUnavailable, RetrievalHit
from backend.services.summary_service.models import public_summary, validate_draft
from backend.services.summary_service.storage import SummaryNotReady
from backend.tests.summary_fixtures import summary_chunks, summary_draft
from backend.tests.test_rag_chain import CHUNKS, SCOPE, SETTINGS, raw_answer


@pytest.mark.parametrize(
    ("question", "intent"),
    [
        ("Summarize this research paper.", "summary"),
        ("Give me an overview.", "summary"),
        ("What does this paper say about gender?", "topic"),
        ("How many participants were involved?", "fact"),
        ("Why did the researchers reach this conclusion?", "analysis"),
        ("How do findings differ between men and women?", "comparison"),
        ("In general, what is retrieval-augmented generation?", "general"),
        ("What does this paper find, and in general what is primacy bias?", "mixed"),
        ("What is the sample size?", "fact"),
    ],
)
def test_expected_question_categories(question, intent):
    assert plan_question(question).intent == intent


def test_follow_up_retrieval_carries_the_prior_subject_without_treating_answers_as_evidence():
    history = [
        {
            "question": "What does the paper say about gender?",
            "answer": "Untrusted prior answer: 999.",
        }
    ]
    plan = plan_question("What about limitations of those findings?", history)
    assert plan.intent == "analysis" and plan.uses_history
    assert "gender" in plan.retrieval_query and "999" not in plan.retrieval_query
    assert not plan.allow_general
    assert len(plan_question("a" * 2000, history, 2100).retrieval_query.encode()) <= 2100


def test_factual_requests_do_not_silently_allow_general_guesses():
    assert not plan_question("How many participants were involved in the study?").allow_general
    assert not plan_question("Explain these findings.").allow_general
    assert plan_question("Explain retrieval-augmented generation.").allow_general


def generate(raw, question="What was the result?", **kwargs):
    return answer_with_trace(
        question,
        SCOPE,
        kwargs.pop("hits", [RetrievalHit(chunk=CHUNKS[0])]),
        SETTINGS,
        "b" * 32,
        "c" * 32,
        complete=Mock(return_value=json.dumps(raw)),
        **kwargs,
    )


def test_general_explanation_is_labeled_and_cannot_claim_paper_citations():
    raw = {
        "is_out_of_scope": True,
        "claims": [],
        "general_background": "RAG combines retrieval with generation.",
    }
    result = generate(raw, "In general, what is RAG?", hits=[])
    assert GENERAL_HEADING in result.response.answer
    assert not result.response.citations and result.response.is_out_of_scope
    assert result.trace.configuration["question_intent"] == "general"
    raw["general_background"] += " [1]"
    with pytest.raises(RagUnavailable):
        generate(raw, "In general, what is RAG?", hits=[])


def test_mixed_answers_separate_supported_claims_from_background():
    raw = raw_answer()
    raw["general_background"] = "A count is a nonnegative integer."
    result = generate(raw, "What result does this paper report, and in general what is a count?")
    assert (
        "## From this paper" in result.response.answer and GENERAL_HEADING in result.response.answer
    )
    assert len(result.response.citations) == 1 and not result.response.is_out_of_scope
    with pytest.raises(RagUnavailable):
        generate(raw)


@pytest.mark.parametrize("text", ["Unverified [9].", "The chunk is " + CHUNKS[0].id])
def test_invented_inline_references_and_internal_ids_are_rejected(text):
    raw = raw_answer()
    raw["claims"][0]["text"] = text
    with pytest.raises(RagUnavailable):
        generate(raw)


def test_one_bounded_validation_correction_never_saves_invalid_citations():
    bad = raw_answer()
    bad["claims"][0]["sources"][0]["quote"] = "The result ... 42."
    model = Mock(side_effect=[json.dumps(bad), json.dumps(raw_answer())])
    result = answer_with_trace(
        "What was the result?",
        SCOPE,
        [RetrievalHit(chunk=CHUNKS[0])],
        SETTINGS,
        "b" * 32,
        "c" * 32,
        complete=model,
    )
    assert result.response.citations and model.call_count == 2
    assert "correction" in json.loads(model.call_args.args[1])


def test_saved_summary_reuse_does_not_generate_another_summary():
    result = public_summary(
        validate_draft(json.dumps(summary_draft(CHUNKS)), CHUNKS), CHUNKS, SETTINGS
    )
    with patch(
        "backend.services.rag_service.document_context.read_summary", return_value=result
    ) as read:
        hits, cached, info = summary_context(Mock(), SCOPE, CHUNKS, SETTINGS)
    read.assert_called_once()
    assert cached["methodology"] == result.methodology
    assert info["summary_reused"] and hits[0].chunk == CHUNKS[0]


def test_unavailable_summary_uses_current_section_sources_and_rejects_stale_generations():
    with patch(
        "backend.services.rag_service.document_context.read_summary", side_effect=SummaryNotReady
    ):
        hits, cached, info = summary_context(Mock(), SCOPE, CHUNKS, SETTINGS)
    assert not cached and not info["summary_reused"] and hits
    with pytest.raises(RagNotReady):
        summary_context(Mock(), SCOPE, summary_chunks("507f1f77bcf86cd799439012"), SETTINGS)


def test_summary_section_sampling_spans_distinct_sections_not_only_vector_hits():
    chunks = [CHUNKS[0]]
    for index, heading in enumerate(["Methods", "Results", "Limitations"], 1):
        chunk = summary_chunks(text="# " + heading + "\n\n" + "Evidence " * 25)[0]
        chunks.append(
            chunk.model_copy(update={"chunk_index": index, "heading_path": {"h1": heading}})
        )
    assert {chunk.heading_path.get("h1") for chunk in section_samples(chunks)} >= {
        "Methods",
        "Results",
        "Limitations",
    }


def test_empty_paper_evidence_still_abstains_without_general_permission():
    result = answer_with_trace(
        "What gender differences did this paper report?",
        SCOPE,
        [],
        SETTINGS,
        "b" * 32,
        "c" * 32,
        complete=Mock(),
    )
    assert result.response.answer == ABSTENTION


def test_unstructured_summary_sampling_does_not_stop_after_one_passage():
    chunks = [
        summary_chunks(text="# Paper\n\n" + str(index) + " " + "Source content " * 15)[
            0
        ].model_copy(update={"chunk_index": index, "heading_path": {"h1": "Paper"}})
        for index in range(10)
    ]
    selected = section_samples(chunks)
    assert len(selected) == len(chunks)
    assert chunks[-1] in selected


def test_table_citations_are_outside_the_final_markdown_row():
    raw = raw_answer()
    raw["claims"][0]["text"] = "| Group | Count |\n| --- | --- |\n| Synthetic | 42 |"
    output = generate(raw)
    assert output.response.answer.endswith("|\n\n[1]")
