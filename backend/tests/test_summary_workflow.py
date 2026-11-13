"""Execute the real LangGraph with deterministic completion boundaries."""

import json
from unittest.mock import Mock

import pytest
from backend.services.document_processor.chunk_models import ChunkingConfig
from backend.services.document_processor.chunking import chunk_document
from backend.services.document_processor.parsed_models import ParsedDocument, ParsedPage
from backend.services.summary_service.models import SummaryError
from backend.services.summary_service.workflow import build_summary_graph, generate_summary
from backend.shared.config import Settings
from backend.tests.summary_fixtures import DOCUMENT_ID, summary_chunks, summary_draft

SETTINGS = Settings(_env_file=None)


def context_completion(system, prompt, schema):
    context = json.loads(prompt.split("\nTargeted correction", 1)[0])
    records = context["research_sections"]
    if context["mode"] == "combine":
        return json.dumps(records[0]["validated_notes"])
    record = records[0]
    page = record["pages"][0]
    source = {
        "chunk_id": record["chunk_id"],
        "page_number": page["page_number"],
        "quote": page["text"][:100],
    }
    draft = summary_draft()
    for field in draft.values():
        field["sources"] = [dict(source)]
    return json.dumps(draft)


def long_chunks():
    return summary_chunks(
        text="# Method\n\n"
        + " ".join(f"Synthetic evidence sentence {i} describes a method." for i in range(600))
    )


def test_graph_has_controlled_nodes_and_saves_only_after_validation():
    complete = Mock(side_effect=context_completion)
    save = Mock()
    result = generate_summary(summary_chunks(), SETTINGS, complete, save)
    assert result.title == "Synthetic Research"
    complete.assert_called_once()
    save.assert_called_once_with(result)
    assert set(build_summary_graph(SETTINGS, complete).get_graph().nodes) >= {
        "identify",
        "generate",
        "validate",
        "combine",
        "save",
    }


def test_invalid_schema_and_evidence_get_two_targeted_repairs():
    wrong = summary_draft()
    wrong["methodology"]["sources"][0]["page_number"] = 99
    complete = Mock(side_effect=["invalid JSON", json.dumps(wrong), json.dumps(summary_draft())])
    result = generate_summary(summary_chunks(), SETTINGS, complete)
    assert result.methodology
    assert complete.call_count == 3
    assert "Correct schema fields" in complete.call_args_list[1].args[1]
    assert "methodology.sources" in complete.call_args_list[2].args[1]


def test_repair_exhaustion_does_not_save_or_loop():
    complete, save = Mock(return_value="{}"), Mock()
    with pytest.raises(SummaryError, match="bounded targeted retries"):
        generate_summary(summary_chunks(), SETTINGS, complete, save)
    assert complete.call_count == 3
    save.assert_not_called()


def test_transport_failure_is_not_treated_as_a_validation_retry():
    complete = Mock(side_effect=SummaryError("provider unavailable"))
    with pytest.raises(SummaryError, match="provider unavailable"):
        generate_summary(summary_chunks(), SETTINGS, complete)
    complete.assert_called_once()


def test_long_paper_processes_every_chunk_and_combines_source_backed_notes():
    chunks = long_chunks()
    settings = SETTINGS.model_copy(update={"summary_context_bytes": 8000})
    complete = Mock(side_effect=context_completion)
    result = generate_summary(chunks, settings, complete)
    contexts = [json.loads(call.args[1]) for call in complete.call_args_list]
    extracts = [context for context in contexts if context["mode"] == "extract"]
    assert len(extracts) > 1
    assert any(context["mode"] == "combine" for context in contexts)
    assert {
        record["chunk_id"] for context in extracts for record in context["research_sections"]
    } == {chunk.id for chunk in chunks}
    assert all(len(call.args[1].encode()) <= 8000 for call in complete.call_args_list)
    assert result.sources[0].chunk_id in {chunk.id for chunk in chunks}


@pytest.mark.parametrize(
    "bad_input",
    [[], summary_chunks() + summary_chunks("507f1f77bcf86cd799439012"), summary_chunks() * 2],
)
def test_invalid_or_mixed_sources_stop_before_any_completion(bad_input):
    complete = Mock()
    with pytest.raises(SummaryError):
        generate_summary(bad_input, SETTINGS, complete)
    complete.assert_not_called()


def test_window_limit_checks_whole_paper_before_paid_calls():
    complete = Mock()
    settings = SETTINGS.model_copy(update={"summary_context_bytes": 8000, "summary_max_windows": 1})
    with pytest.raises(SummaryError, match="SUMMARY_MAX_WINDOWS"):
        generate_summary(long_chunks(), settings, complete)
    complete.assert_not_called()


def test_oversized_source_is_rejected_without_silent_truncation():
    chunks = chunk_document(
        ParsedDocument(
            document_id=DOCUMENT_ID,
            pages=[ParsedPage(document_id=DOCUMENT_ID, page_number=1, markdown="Evidence " * 1600)],
        ),
        "parse",
        ChunkingConfig(chunk_size=20000, chunk_overlap=0),
    )
    complete = Mock()
    with pytest.raises(SummaryError, match="byte guard"):
        generate_summary(
            chunks, SETTINGS.model_copy(update={"summary_context_bytes": 8000}), complete
        )
    complete.assert_not_called()


def test_elided_source_quote_is_repaired_without_weakening_exact_match():
    wrong = summary_draft()
    wrong["methodology"]["sources"][0]["quote"] = (
        "The study measures ... The method compares counts."
    )
    complete = Mock(side_effect=[json.dumps(wrong), json.dumps(summary_draft())])
    save = Mock()
    result = generate_summary(summary_chunks(), SETTINGS, complete, save)
    assert complete.call_count == 2
    assert "do not insert ellipses" in complete.call_args_list[1].args[1]
    assert "Never add ellipses" in complete.call_args_list[0].args[0]
    assert result.workflow_version == "grounded-summary-v2"
    assert all("..." not in source.quote for source in result.sources)
    save.assert_called_once_with(result)
