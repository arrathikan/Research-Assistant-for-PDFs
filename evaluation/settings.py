"""Optional evaluator settings, separate from serving and worker configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EvaluationSettings(BaseSettings):
    judge_model: str = Field(default="meta-llama/llama-3.3-70b-instruct", min_length=1)
    temperature: float = Field(default=0.1, ge=0, le=1)
    timeout_seconds: int = Field(default=60, ge=1, le=180)
    metric_timeout_seconds: int = Field(default=180, ge=10, le=600)
    max_output_tokens: int = Field(default=2048, ge=256, le=8192)
    max_workers: int = Field(default=2, ge=1, le=4)
    max_llm_requests: int = Field(default=1000, ge=1, le=5000)
    max_embedding_inputs: int = Field(default=200, ge=1, le=1000)
    relevancy_questions: int = Field(default=3, ge=1, le=3)
    max_samples: int = Field(default=20, ge=1, le=100)
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="EVAL_", extra="ignore"
    )
