"""Provider settings accept the documented names without silently ignoring them."""

import pytest
from backend.shared.config import Settings
from pydantic import ValidationError


def test_requested_names_override_legacy_environment_names(monkeypatch):
    monkeypatch.setenv("VOYAGE_EMBEDDING_MODEL", "voyage-4-lite")
    monkeypatch.setenv("VOYAGE_MODEL", "voyage-3")
    monkeypatch.setenv("EMBEDDING_DIMENSIONS", "512")
    monkeypatch.setenv("VOYAGE_DIMENSIONS", "1024")
    monkeypatch.setenv("PRIMARY_REASONING_MODEL", "openai/gpt-5.6-luna")
    monkeypatch.setenv("LLM_MODEL", "old-model")
    settings = Settings(_env_file=None)
    assert settings.voyage_model == "voyage-4-lite"
    assert settings.voyage_dimensions == 512
    assert settings.llm_model == settings.primary_reasoning_model == "openai/gpt-5.6-luna"


def test_openrouter_environment_loads_roles_and_attribution(monkeypatch):
    values = {
        "OPENROUTER_API_KEY": "test-openrouter-key",
        "OPENROUTER_APP_URL": "https://verdeai.local",
        "OPENROUTER_APP_NAME": "VerdeAI",
        "PRIMARY_REASONING_MODEL": "openai/gpt-5.6-luna",
        "CHEAP_REASONING_MODEL": "meta-llama/llama-3.3-70b-instruct",
        "VISION_MODEL": "mistralai/mistral-small-3.1-24b-instruct",
        "LLM_MAX_RETRIES": "3",
        "VOYAGE_RERANKER_MODEL": "rerank-2.5",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)
    settings = Settings(_env_file=None)
    assert settings.openrouter_api_key == values["OPENROUTER_API_KEY"]
    assert settings.openrouter_app_url == values["OPENROUTER_APP_URL"]
    assert settings.openrouter_app_name == values["OPENROUTER_APP_NAME"]
    assert settings.cheap_reasoning_model == values["CHEAP_REASONING_MODEL"]
    assert settings.vision_model == values["VISION_MODEL"]
    assert settings.llm_max_retries == 3
    assert settings.llm_provider == "openrouter"
    assert settings.voyage_reranker_model == "rerank-2.5"


def test_credential_values_are_excluded_from_settings_repr():
    settings = Settings(
        _env_file=None,
        openrouter_api_key="test-openrouter-secret",
        voyage_api_key="test-voyage-secret",
        llama_cloud_api_key="test-parser-secret",
    )
    for secret in ["test-openrouter-secret", "test-voyage-secret", "test-parser-secret"]:
        assert secret not in repr(settings)


@pytest.mark.parametrize("value", [-1, 6])
def test_completion_retry_count_is_bounded(value):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, llm_max_retries=value)


def test_completion_gateway_rejects_direct_provider_selection():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, llm_provider="openai")
