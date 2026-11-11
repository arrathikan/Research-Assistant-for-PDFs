"""OpenRouter-only JSON completion client with bounded transport retries."""

import time
from typing import Any

import httpx
from backend.services.summary_service.models import SummaryError
from backend.shared.config import Settings

COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"
TRANSIENT_STATUS = {408, 429, 500, 502, 503, 504}


class OpenRouterClient:
    def __init__(self, settings: Settings):
        if not settings.openrouter_api_key.strip() or settings.openrouter_api_key.startswith(
            "your_"
        ):
            raise SummaryError("OPENROUTER_API_KEY is not configured")
        self.settings = settings
        self.client = httpx.Client(
            timeout=settings.llm_timeout_seconds,
            follow_redirects=False,
            headers={
                "Authorization": "Bearer " + settings.openrouter_api_key,
                "HTTP-Referer": settings.openrouter_app_url,
                "X-Title": settings.openrouter_app_name,
            },
        )

    def __enter__(self) -> "OpenRouterClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.client.close()

    def complete(self, system: str, prompt: str, schema: dict[str, Any]) -> str:
        settings = self.settings
        body: dict[str, Any] = {
            "model": settings.primary_reasoning_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "research_summary", "strict": True, "schema": schema},
            },
            "provider": {"require_parameters": True},
            "max_completion_tokens": settings.llm_max_output_tokens,
            "stream": False,
        }
        if settings.primary_reasoning_model.startswith("openai/gpt-5"):
            body["reasoning"] = {"effort": "low"}
        else:
            body["temperature"] = settings.llm_temperature
        for attempt in range(settings.llm_max_retries + 1):
            try:
                response = self.client.post(COMPLETIONS_URL, json=body)
            except httpx.RequestError:
                response = None
            if response is None or response.status_code in TRANSIENT_STATUS:
                if attempt < settings.llm_max_retries:
                    time.sleep(min(2**attempt, 8))
                    continue
                raise SummaryError("OpenRouter request failed after bounded retries") from None
            if response.status_code != 200:
                raise SummaryError(
                    "OpenRouter rejected the request; check model access, credits and configuration"
                )
            try:
                data = response.json()
                choice = data["choices"][0]
                content = choice["message"]["content"]
                if (
                    data.get("error")
                    or choice.get("error")
                    or choice.get("finish_reason") != "stop"
                    or not isinstance(content, str)
                    or not content.strip()
                ):
                    raise ValueError("Invalid completion")
            except (ValueError, KeyError, IndexError, TypeError):
                raise SummaryError(
                    "OpenRouter returned an incomplete or invalid completion"
                ) from None
            return content
        raise SummaryError("OpenRouter request unavailable")
