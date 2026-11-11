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
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    ingestion_queue: str = "document_ingestion_queue"
    summary_queue: str = "document_summary_queue"
    dlq_queue: str = "document_dlq"

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
    openrouter_app_name: str = Field(default="VerdeAI", min_length=1)
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
