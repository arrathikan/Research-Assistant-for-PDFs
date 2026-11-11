"""Completion request contracts and provider failures without network calls."""

from unittest.mock import patch

import httpx
import pytest
from backend.services.summary_service.models import SummaryDraft, SummaryError
from backend.shared.config import Settings
from backend.shared.openrouter import COMPLETIONS_URL, OpenRouterClient

SETTINGS = Settings(_env_file=None, openrouter_api_key="synthetic-secret")


def response(content="{}", finish="stop"):
    return httpx.Response(
        200, json={"choices": [{"message": {"content": content}, "finish_reason": finish}]}
    )


def test_single_gateway_model_schema_headers_and_client_cleanup():
    schema = SummaryDraft.model_json_schema()
    with patch("backend.shared.openrouter.httpx.Client") as constructor:
        client = constructor.return_value
        client.post.return_value = response()
        with OpenRouterClient(SETTINGS) as gateway:
            assert gateway.complete("system", "evidence", schema) == "{}"
        args, kwargs = client.post.call_args
        assert args == (COMPLETIONS_URL,)
        assert kwargs["json"]["model"] == "openai/gpt-5.6-luna"
        assert kwargs["json"]["response_format"]["json_schema"]["schema"] == schema
        assert kwargs["json"]["provider"] == {"require_parameters": True}
        assert kwargs["json"]["reasoning"] == {"effort": "low"}
        assert "temperature" not in kwargs["json"]
        assert constructor.call_args.kwargs["follow_redirects"] is False
        headers = constructor.call_args.kwargs["headers"]
        assert headers["Authorization"] == "Bearer synthetic-secret"
        assert headers["HTTP-Referer"] == "https://verdeai.local"
        assert headers["X-Title"] == "VerdeAI"
        client.close.assert_called_once()


def test_missing_key_never_creates_a_client():
    with patch("backend.shared.openrouter.httpx.Client") as constructor:
        with pytest.raises(SummaryError, match="not configured"):
            OpenRouterClient(Settings(_env_file=None, openrouter_api_key=""))
        constructor.assert_not_called()


def test_transient_status_and_network_errors_retry_with_bounded_backoff():
    with (
        patch("backend.shared.openrouter.httpx.Client") as constructor,
        patch("backend.shared.openrouter.time.sleep") as sleep,
    ):
        constructor.return_value.post.side_effect = [
            httpx.ConnectError("private network detail"),
            httpx.Response(429),
            response(),
        ]
        with OpenRouterClient(SETTINGS) as gateway:
            assert gateway.complete("system", "prompt", {}) == "{}"
        assert [call.args[0] for call in sleep.call_args_list] == [1, 2]
        assert constructor.return_value.post.call_count == 3


def test_retry_exhaustion_is_safe_and_finite():
    with (
        patch("backend.shared.openrouter.httpx.Client") as constructor,
        patch("backend.shared.openrouter.time.sleep"),
    ):
        constructor.return_value.post.return_value = httpx.Response(
            503, text="private provider detail"
        )
        with OpenRouterClient(SETTINGS) as gateway:
            with pytest.raises(
                SummaryError, match="^OpenRouter request failed after bounded retries$"
            ):
                gateway.complete("system", "prompt", {})
        assert constructor.return_value.post.call_count == 4


@pytest.mark.parametrize("status", [302, 400, 401, 402, 403, 404])
def test_permanent_errors_are_not_retried_or_leaked(status):
    with patch("backend.shared.openrouter.httpx.Client") as constructor:
        constructor.return_value.post.return_value = httpx.Response(status, text="synthetic-secret")
        with OpenRouterClient(SETTINGS) as gateway:
            with pytest.raises(SummaryError) as error:
                gateway.complete("system", "prompt", {})
        assert "synthetic-secret" not in str(error.value)
        assert constructor.return_value.post.call_count == 1


@pytest.mark.parametrize(
    "result",
    [
        response(finish="length"),
        response(content=None),
        httpx.Response(200, json={}),
        httpx.Response(200, text="not JSON"),
    ],
)
def test_incomplete_or_invalid_response_is_not_published(result):
    with patch("backend.shared.openrouter.httpx.Client") as constructor:
        constructor.return_value.post.return_value = result
        with OpenRouterClient(SETTINGS) as gateway:
            with pytest.raises(SummaryError, match="incomplete or invalid"):
                gateway.complete("system", "prompt", {})
        constructor.return_value.close.assert_called_once()
