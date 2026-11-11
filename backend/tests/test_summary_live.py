"""Explicitly enabled paid summary check; only synthetic content is sent."""

import os

import pytest
from backend.services.summary_service.workflow import generate_summary
from backend.shared.config import get_settings
from backend.tests.summary_fixtures import summary_chunks


@pytest.mark.live_summary
def test_live_openrouter_summary():
    if os.environ.get("RESEARCHAI_RUN_SUMMARY_LIVE") != "1":
        pytest.skip("Set RESEARCHAI_RUN_SUMMARY_LIVE=1 to opt into a paid summary call")
    settings = get_settings()
    if not settings.openrouter_api_key.strip() or settings.openrouter_api_key.startswith("your_"):
        pytest.skip("OPENROUTER_API_KEY is not configured")
    result = generate_summary(summary_chunks(), settings)
    assert "Synthetic" in result.title
    assert "42" in result.key_results
    assert result.sources
    assert result.llm_model == settings.primary_reasoning_model
