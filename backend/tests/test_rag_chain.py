"""Grounded answers, insufficient evidence and internal evaluation contracts."""

import json
from unittest.mock import Mock

import pytest
from backend.services.rag_service.chain import ABSTENTION, answer_with_trace
from backend.services.rag_service.models import (
    ChatRequest,
    RagUnavailable,
    RetrievalHit,
    RetrievalScope,
)
from backend.shared.config import Settings
from backend.tests.summary_fixtures import DOCUMENT_ID, summary_chunks
from pydantic import ValidationError

CHUNKS = summary_chunks()
SCOPE = RetrievalScope(
    document_id=DOCUMENT_ID,
    chunk_set_id=CHUNKS[0].chunk_set_id,
    parse_run_id=CHUNKS[0].parse_run_id,
    embedding_profile_id="a" * 64,
)
SETTINGS = Settings(_env_file=None)


def raw_answer():
    return {
        "is_out_of_scope": False,
        "claims": [
            {
                "text": "The synthetic result is 42.",
                "sources": [
                    {
                        "chunk_id": CHUNKS[0].id,
                        "page_number": 1,
                        "quote": "The result is a count of 42.",
                    }
                ],
            }
        ],
    }


def run(raw=None, hits=None):
    return answer_with_trace(
        "What was the result?",
        SCOPE,
        hits if hits is not None else [RetrievalHit(chunk=CHUNKS[0])],
        SETTINGS,
        "b" * 32,
        "c" * 32,
        complete=Mock(return_value=json.dumps(raw or raw_answer())),
    )


def test_answer_chain_validates_citations_and_keeps_trace_private():
    output = run()
    assert "42" in output.response.answer and "[1]" in output.response.answer
    assert output.response.citations[0].document_id == DOCUMENT_ID
    assert output.trace.retrieved_chunk_ids == [CHUNKS[0].id]
    assert output.trace.retrieved_contexts == [CHUNKS[0].content]
    assert output.trace.source_pages == [[1]]
    assert output.trace.latency_ms >= 0
    assert output.trace.configuration["chunk_overlap"] == 150
    assert "retrieved_contexts" not in output.response.model_dump()


def test_no_hits_abstains_without_calling_a_model():
    model = Mock()
    output = answer_with_trace(
        "Unknown topic", SCOPE, [], SETTINGS, "b" * 32, "c" * 32, complete=model
    )
    assert output.response.is_out_of_scope and output.response.answer == ABSTENTION
    assert not output.response.citations
    model.assert_not_called()


def test_model_insufficient_evidence_uses_fixed_polite_abstention():
    output = run({"is_out_of_scope": True, "claims": []})
    assert output.response.answer == ABSTENTION and not output.response.citations


@pytest.mark.parametrize("mutation", ["page", "quote", "id", "no_source", "bad_schema"])
def test_invalid_or_missing_citations_reject_the_answer(mutation):
    raw = raw_answer()
    source = raw["claims"][0]["sources"][0]
    if mutation == "page":
        source["page_number"] = 2
    if mutation == "quote":
        source["quote"] = "Fabricated quote"
    if mutation == "id":
        source["chunk_id"] = "b" * 64
    if mutation == "no_source":
        raw["claims"][0]["sources"] = []
    if mutation == "bad_schema":
        raw = {"answer": "unverified"}
    with pytest.raises(RagUnavailable):
        run(raw)


def test_wrong_document_context_stops_before_model_request():
    model = Mock()
    with pytest.raises(RagUnavailable):
        answer_with_trace(
            "question",
            SCOPE,
            [RetrievalHit(chunk=summary_chunks("507f1f77bcf86cd799439012")[0])],
            SETTINGS,
            "b" * 32,
            "c" * 32,
            complete=model,
        )
    model.assert_not_called()


@pytest.mark.parametrize("message", ["", "   ", "a" * 2001])
def test_invalid_question_is_rejected(message):
    with pytest.raises(ValidationError):
        ChatRequest(message=message)
