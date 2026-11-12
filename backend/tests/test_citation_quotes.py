"""Exact citation recovery for Markdown and neighboring selected chunks."""

import json
from unittest.mock import Mock

import pytest
from backend.services.rag_service.chain import answer_with_trace
from backend.services.rag_service.citations import exact_source_quote, make_citation
from backend.services.rag_service.models import RetrievalHit
from backend.tests.test_rag_chain import CHUNKS, SCOPE, SETTINGS, raw_answer


@pytest.mark.parametrize(
    "source,quote",
    [
        ("Results become *longer* than training.", "Results become longer than training."),
        ("The **main finding** is supported.", "The main finding is supported."),
        ("The _same_ words occur.", "The same words occur."),
    ],
)
def test_emphasis_is_recovered_as_actual_source_text(source, quote):
    canonical = exact_source_quote(source, quote)
    assert canonical and canonical in source


@pytest.mark.parametrize(
    "source,quote",
    [
        ("The result was 42.", "The result was 43."),
        ("The result was 42.", "The result ... 42."),
        ("Compute a*b for this task.", "Compute ab for this task."),
        ("An alpha_value is provided.", "An alphavalue is provided."),
    ],
)
def test_words_numbers_ellipses_and_literal_math_are_never_fuzzily_matched(source, quote):
    assert exact_source_quote(source, quote) is None


def test_known_neighbor_is_rebound_to_exact_selected_chunk_on_the_same_page():
    text = "The evidence is **clear** within this passage."
    original = CHUNKS[0]
    neighbor = original.model_copy(
        update={
            "id": "e" * 64,
            "content": text,
            "page_spans": [
                original.page_spans[0].model_copy(
                    update={"text": text, "chunk_start": 0, "chunk_end": len(text)}
                )
            ],
        }
    )
    raw = raw_answer()
    raw["claims"][0]["sources"][0]["quote"] = "The evidence is clear within this passage."
    output = answer_with_trace(
        "What was the result?",
        SCOPE,
        [RetrievalHit(chunk=original), RetrievalHit(chunk=neighbor)],
        SETTINGS,
        "b" * 32,
        "c" * 32,
        complete=Mock(return_value=json.dumps(raw)),
    )
    citation = output.response.citations[0]
    assert citation.chunk_id == neighbor.id and citation.page_number == 1
    assert citation.quote_snippet == text
    assert make_citation(neighbor, 1, citation.quote_snippet) == citation
