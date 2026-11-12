"""Model passage choices become canonical current source citations."""

import json
from unittest.mock import Mock

import pytest
from backend.services.rag_service.answer_selection import source_passages
from backend.services.rag_service.chain import GENERAL_HEADING, answer_with_trace
from backend.services.rag_service.models import RagUnavailable, RetrievalHit
from backend.tests.test_rag_chain import CHUNKS, SCOPE, SETTINGS


def run(raw, question="What was the result?", hits=None):
    return answer_with_trace(
        question,
        SCOPE,
        hits if hits is not None else [RetrievalHit(chunk=CHUNKS[0])],
        SETTINGS,
        "b" * 32,
        "c" * 32,
        complete=Mock(return_value=json.dumps(raw)),
    )


def test_keys_materialize_real_ids_pages_and_exact_source_quotes():
    output = run(
        {
            "claims": [{"text": "The synthetic paper studies a counter.", "source_keys": [1]}],
            "general_background": "",
        }
    )
    source = output.response.citations[0]
    assert source.chunk_id == CHUNKS[0].id and source.page_number == 1
    assert source.quote_snippet in CHUNKS[0].page_spans[0].text
    assert output.trace.configuration["citation_contract"] == "numbered_passages_v1"


@pytest.mark.parametrize("keys", [[9999], [True], [], ["1"]])
def test_unknown_missing_or_wrongly_typed_keys_are_rejected(keys):
    with pytest.raises(RagUnavailable):
        run(
            {
                "claims": [{"text": "Unverified claim.", "source_keys": keys}],
                "general_background": "",
            }
        )


def test_general_schema_needs_no_paper_scope_flag_or_source_keys():
    output = run(
        {"claims": [], "general_background": "RAG combines retrieval and generation."},
        question="In general, what is RAG?",
        hits=[],
    )
    assert GENERAL_HEADING in output.response.answer and not output.response.citations
    assert output.response.is_out_of_scope


def test_serialized_passages_preserve_every_word_and_use_bounded_exact_quotes():
    text = "A source paragraph. " * 45
    passages = source_passages(text, 7)
    assert [row["key"] for row in passages] == list(range(7, 7 + len(passages)))
    assert all(0 < len(row["text"]) <= 280 and row["text"] in text for row in passages)
    assert " ".join(" ".join(row["text"].split()) for row in passages) == " ".join(text.split())
