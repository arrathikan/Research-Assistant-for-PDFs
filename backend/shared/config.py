"""Shared configuration module for ResearchAI microservices.

Loads environment variables defensively using Pydantic Settings.
Centralizes database, message broker, embedding, and LLM parameters.
"""

from functools import lru_cache
from typing import List, Literal

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    # Application Information
    app_name: str = "ResearchAI"
    app_env: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    # Gateway API Configuration
    gateway_host: str = "0.0.0.0"
    gateway_port: int = 8000
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # MongoDB Atlas & GridFS Configuration
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "research_assistant"
    mongodb_timeout_ms: int = Field(default=5000, gt=0)

    # RabbitMQ Message Broker Configuration
    rabbitmq_url: str = Field(default="amqp://guest:guest@localhost:5672/", repr=False)
    ingestion_queue: str = Field(
        default="document_ingestion_queue", pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,119}$"
    )
    summary_queue: str = Field(
        default="document_summary_queue", pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,119}$"
    )
    dlq_queue: str = Field(default="document_dlq", pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,119}$")
    rabbitmq_heartbeat_seconds: int = Field(default=60, ge=10, le=300)
    rabbitmq_connection_timeout_seconds: int = Field(default=10, ge=1, le=60)
    worker_ack_timeout_ms: int = Field(default=7200000, ge=60000)
    job_max_attempts: int = Field(default=3, ge=1, le=5)
    job_retry_base_seconds: int = Field(default=5, ge=1, le=300)
    job_retry_max_seconds: int = Field(default=300, ge=1, le=3600)
    job_poll_seconds: float = Field(default=2, ge=0.1, le=60)
    job_lease_seconds: int = Field(default=300, ge=30, le=3600)
    job_heartbeat_seconds: int = Field(default=30, ge=1, le=60)

    @model_validator(mode="after")
    def validate_job_settings(self) -> "Settings":
        names = (self.ingestion_queue, self.summary_queue, self.dlq_queue)
        if any(name.startswith("amq.") for name in names):
            raise ValueError("Job queues cannot use the reserved amq. prefix")
        if len(set(names)) != 3:
            raise ValueError("Job queue names must be distinct")
        if self.job_retry_max_seconds < self.job_retry_base_seconds:
            raise ValueError("Job retry maximum must cover the base delay")
        if self.job_lease_seconds < 3 * self.job_heartbeat_seconds:
            raise ValueError("Job lease must cover at least three heartbeat intervals")
        return self

    # PDF Extraction Configuration (LlamaParse)
    llama_cloud_api_key: str = Field(default="", repr=False)
    llama_parse_timeout_seconds: int = Field(default=300, gt=0)
    llama_parse_tier: Literal["fast", "cost_effective", "agentic", "agentic_plus"] = "agentic"
    llama_parse_version: str = Field(default="latest", min_length=1)

    # Embedding Provider Configuration (Voyage AI)
    voyage_api_key: str = Field(default="", repr=False)
    voyage_model: Literal["voyage-3", "voyage-large-2-instruct", "voyage-4", "voyage-4-lite"] = (
        Field(
            default="voyage-3",
            validation_alias=AliasChoices("VOYAGE_EMBEDDING_MODEL", "VOYAGE_MODEL"),
        )
    )
    voyage_dimensions: int = Field(
        default=1024,
        gt=0,
        validation_alias=AliasChoices("EMBEDDING_DIMENSIONS", "VOYAGE_DIMENSIONS"),
    )
    voyage_reranker_model: Literal["rerank-2.5"] = "rerank-2.5"
    voyage_batch_size: int = Field(default=16, ge=1, le=128)
    voyage_max_input_bytes: int = Field(default=12000, gt=0)
    voyage_max_batch_bytes: int = Field(default=96000, gt=0)
    voyage_timeout_seconds: float = Field(default=30, gt=0, le=120)
    voyage_retry_attempts: int = Field(default=2, ge=0, le=4)
    voyage_retry_backoff_seconds: float = Field(default=1, gt=0, le=8)
    vector_search_index_name: str = Field(
        default="chunk_embeddings_v1", pattern=r"^[A-Za-z0-9_-]+$"
    )
    keyword_search_index_name: str = Field(default="chunk_keywords_v1", pattern=r"^[A-Za-z0-9_-]+$")
    rag_candidate_k: int = Field(default=20, ge=1, le=50)
    rag_context_k: int = Field(default=6, ge=1, le=20)
    rag_rrf_constant: int = Field(default=60, ge=1, le=1000)
    rag_context_bytes: int = Field(default=32000, ge=4000, le=128000)
    rag_history_turns: int = Field(default=6, ge=0, le=20)
    semantic_top_k: int = Field(default=5, ge=1, le=20)
    vector_num_candidates: int = Field(default=100, ge=1, le=10000)

    @model_validator(mode="after")
    def validate_embedding_configuration(self) -> "Settings":
        if self.voyage_dimensions not in {256, 512, 1024, 2048}:
            raise ValueError("Voyage dimensions must be 256, 512, 1024 or 2048")
        if not self.voyage_model.startswith("voyage-4") and self.voyage_dimensions != 1024:
            raise ValueError("Configured legacy Voyage models require 1024 dimensions")
        if self.voyage_max_batch_bytes < self.voyage_max_input_bytes:
            raise ValueError("Voyage batch byte guard must cover one maximum-size input")
        return self

    # OpenRouter is the single completion gateway; model roles are explicit.
    openrouter_api_key: str = Field(default="", repr=False)
    openrouter_app_url: str = Field(default="https://verdeai.local", pattern=r"^https?://[^\s]+$")
    openrouter_app_name: str = Field(default="VerdeAI", min_length=1, pattern=r"^[^\r\n]+$")
    llm_provider: Literal["openrouter"] = "openrouter"
    primary_reasoning_model: str = Field(
        default="openai/gpt-5.6-luna",
        min_length=1,
        validation_alias=AliasChoices("PRIMARY_REASONING_MODEL", "LLM_MODEL"),
    )
    cheap_reasoning_model: str = Field(default="meta-llama/llama-3.3-70b-instruct", min_length=1)
    vision_model: str = Field(default="mistralai/mistral-small-3.1-24b-instruct", min_length=1)
    llm_max_retries: int = Field(default=3, ge=0, le=5)
    llm_temperature: float = 0.1
    llm_timeout_seconds: float = Field(default=60, gt=0, le=180)
    llm_max_output_tokens: int = Field(default=4096, ge=512, le=8192)
    summary_context_bytes: int = Field(default=48000, ge=8000, le=128000)
    summary_max_windows: int = Field(default=64, ge=1, le=128)
    summary_validation_retries: int = Field(default=2, ge=0, le=2)

    @property
    def llm_model(self) -> str:
        """Keep existing service logging aligned with the primary model."""
        return self.primary_reasoning_model

    # Ingestion & Chunking Limits
    max_upload_size_bytes: int = Field(default=25 * 1024 * 1024, gt=0)  # 25 MB
    chunk_size: int = Field(default=1200, gt=0)
    chunk_overlap: int = Field(default=150, ge=0)

    @model_validator(mode="after")
    def validate_chunk_overlap(self) -> "Settings":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache()
def get_settings() -> Settings:
    """Returns a cached singleton instance of application settings."""
    return Settings()
