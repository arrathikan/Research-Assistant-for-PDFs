"""Optional installed-Ragas contract checks use local HTTP fixtures, never a paid API."""

import json

import httpx
import pytest
from backend.shared.config import Settings
from evaluation.judge import JudgeError, RequestBudget, build_evaluator
from evaluation.settings import EvaluationSettings
from langchain_core.prompt_values import StringPromptValue


def test_installed_ragas_evaluator_uses_explicit_gateway_and_bounded_completions():
    pytest.importorskip("ragas")
    config = EvaluationSettings(_env_file=None, max_llm_requests=2)
    budget = RequestBudget(config)

    def respond(request):
        assert request.url.host == "openrouter.ai"
        assert request.headers["Authorization"] == "Bearer synthetic-key"
        assert json.loads(request.content)["model"] == config.judge_model
        return httpx.Response(
            200,
            json={
                "choices": [{"finish_reason": "stop", "message": {"content": '{"statements":[]}'}}]
            },
        )

    llm, embeddings = build_evaluator(
        Settings(_env_file=None, openrouter_api_key="synthetic-key"),
        config,
        budget,
        httpx.MockTransport(respond),
    )
    try:
        output = llm.generate_text(StringPromptValue(text="Synthetic evaluation prompt"), n=2)
        assert len(output.generations[0]) == 2
        with pytest.raises(JudgeError, match="budget"):
            llm.generate_text(StringPromptValue(text="Synthetic prompt"))
        assert budget.snapshot()["llm_requests"] == 2
    finally:
        llm.close()


def test_budgets_are_checked_before_provider_calls():
    config = EvaluationSettings(_env_file=None, max_embedding_inputs=1)
    budget = RequestBudget(config)
    budget.consume("embedding")
    with pytest.raises(JudgeError):
        budget.consume("embedding")
