"""Shared configuration module for ResearchAI microservices.

Loads environment variables defensively using Pydantic Settings.
Centralizes database, message broker, embedding, and LLM parameters.
"""

from functools import lru_cache
from typing import List

from pydantic import Field
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
    llama_cloud_api_key: str = ""

    # Embedding Provider Configuration (Voyage AI)
    voyage_api_key: str = ""
    voyage_model: str = "voyage-3"

    # LLM Provider Configuration
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    llm_provider: str = "openai"  # openai | anthropic | google
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.1

    # Ingestion & Chunking Limits
    max_upload_size_bytes: int = 25 * 1024 * 1024  # 25 MB
    chunk_size: int = 1000
    chunk_overlap: int = 200

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Returns a cached singleton instance of application settings."""
    return Settings()
