"""Source identity/quote checks and explicit missing information."""

import json

import pytest
from backend.services.summary_service.models import (
    UNAVAILABLE,
    SummaryValidationError,
    public_summary,
    validate_draft,
)
from backend.shared.config import Settings
from backend.tests.summary_fixtures import summary_chunks, summary_draft

SETTINGS = Settings(_env_file=None)


def test_public_summary_preserves_five_sections_and_verified_sources():
    chunks = summary_chunks()
    draft = validate_draft(json.dumps(summary_draft()), chunks)
    result = public_summary(draft, chunks, SETTINGS)
    assert result.document_id == chunks[0].document_id
    assert result.chunk_set_id == chunks[0].chunk_set_id
    assert {source.field for source in result.sources} == {
        "title",
        "authors",
        "abstract",
        "problem_statement",
        "methodology",
        "key_results",
        "conclusion",
    }
    assert not result.unavailable_fields


def test_missing_information_is_explicit_and_not_filled_from_filename():
    data = summary_draft()
    data["key_results"] = {"text": None, "sources": []}
    data["authors"] = {"names": [], "sources": []}
    result = public_summary(
        validate_draft(json.dumps(data), summary_chunks()), summary_chunks(), SETTINGS
    )
    assert result.key_results == UNAVAILABLE
    assert result.authors == []
    assert set(result.unavailable_fields) == {"key_results", "authors"}


@pytest.mark.parametrize(
    "mutation", ["empty", "missing", "no_evidence", "unknown_field", "bad_json"]
)
def test_invalid_output_requests_a_safe_targeted_correction(mutation):
    data = summary_draft()
    if mutation == "empty":
        data["abstract"]["text"] = "   "
    if mutation == "missing":
        del data["methodology"]
    if mutation == "no_evidence":
        data["conclusion"]["sources"] = []
    if mutation == "unknown_field":
        data["invented"] = "private text"
    raw = "not JSON private text" if mutation == "bad_json" else json.dumps(data)
    with pytest.raises(SummaryValidationError) as error:
        validate_draft(raw, summary_chunks())
    assert "private text" not in str(error.value)


@pytest.mark.parametrize("mutation", ["other_document", "wrong_page", "fabricated_quote"])
def test_invalid_source_references_are_rejected(mutation):
    data = summary_draft()
    source = data["methodology"]["sources"][0]
    if mutation == "other_document":
        source["chunk_id"] = summary_chunks("507f1f77bcf86cd799439012")[0].id
    if mutation == "wrong_page":
        source["page_number"] = 2
    if mutation == "fabricated_quote":
        source["quote"] = "a quote that does not exist"
    with pytest.raises(SummaryValidationError, match="methodology.sources"):
        validate_draft(json.dumps(data), summary_chunks())


def test_feedback_identifies_all_invalid_quotes_without_exposing_source_text():
    data = summary_draft()
    data["methodology"]["sources"][0]["quote"] = "private wrong method quote"
    data["key_results"]["sources"][0]["page_number"] = 99
    with pytest.raises(SummaryValidationError) as failure:
        validate_draft(json.dumps(data), summary_chunks())
    message = str(failure.value)
    assert "methodology.sources[0]" in message
    assert "key_results.sources[0]" in message
    assert "private wrong method quote" not in message


@pytest.mark.parametrize(
    ("model", "legacy_profile"),
    [
        ("openai/gpt-5.6-luna", "7d4a3b207c4ca46f3dd4fbb13a7c59e63062bb0c633be5f47296c8a0c2c040a0"),
        ("nvidia/nemotron-3.5-super-vl:free", "319b051ba92be8cc60976bb6e5ccc88f07d97f985cb9a9f2e29d4ea6d058b26c"),
    ],
)
def test_reasoning_override_changes_profile_without_invalidating_unset_legacy(model, legacy_profile):
    from backend.services.summary_service.models import summary_profile_id

    original = Settings(_env_file=None, primary_reasoning_model=model)
    assert summary_profile_id(original) == legacy_profile
    disabled = original.model_copy(update={"llm_reasoning_enabled": False})
    assert summary_profile_id(disabled) != legacy_profile
