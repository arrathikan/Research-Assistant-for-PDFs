"""Voyage document/query embeddings with bounded batching and retries."""

import time
from collections.abc import Iterator
from typing import Literal

import voyageai
from backend.shared.config import Settings
from backend.shared.embedding_models import (
    EmbeddingError,
    EmbeddingInputError,
    EmbeddingProfile,
    validate_vectors,
)
from voyageai.error import (
    APIConnectionError,
    RateLimitError,
    ServerError,
    ServiceUnavailableError,
    Timeout,
)


def embedding_profile(settings: Settings) -> EmbeddingProfile:
    return EmbeddingProfile(model=settings.voyage_model, dimensions=settings.voyage_dimensions)


def document_batches(texts: list[str], settings: Settings) -> Iterator[list[str]]:
    # Validate the entire input before the first potentially paid request.
    for text in texts:
        if not isinstance(text, str) or not text.strip():
            raise EmbeddingInputError("Embedding inputs must contain nonempty text")
        if len(text.encode("utf-8")) > settings.voyage_max_input_bytes:
            raise EmbeddingInputError(
                "Embedding input exceeds the configured byte guard; reduce chunk size"
            )
    batch: list[str] = []
    size = 0
    for text in texts:
        length = len(text.encode("utf-8"))
        if batch and (
            len(batch) >= settings.voyage_batch_size
            or size + length > settings.voyage_max_batch_bytes
        ):
            yield batch
            batch, size = [], 0
        batch.append(text)
        size += length
    if batch:
        yield batch


def _request(
    client: voyageai.Client,
    texts: list[str],
    kind: Literal["document", "query"],
    settings: Settings,
) -> list[list[float]]:
    for attempt in range(settings.voyage_retry_attempts + 1):
        try:
            result = client.embed(
                texts,
                model=settings.voyage_model,
                input_type=kind,
                truncation=False,
                output_dtype="float",
                output_dimension=settings.voyage_dimensions
                if settings.voyage_model == "voyage-4"
                else None,
            )
            return validate_vectors(result.embeddings, len(texts), settings.voyage_dimensions)
        except (RateLimitError, ServiceUnavailableError, ServerError, APIConnectionError, Timeout):
            if attempt == settings.voyage_retry_attempts:
                raise EmbeddingError(
                    "Voyage embedding request failed after bounded retries"
                ) from None
            time.sleep(min(settings.voyage_retry_backoff_seconds * 2**attempt, 8))
        except EmbeddingError:
            raise
        except Exception:
            raise EmbeddingError("Voyage embedding request failed") from None
    raise EmbeddingError("Voyage embedding request failed")


def _embed(
    texts: list[str], kind: Literal["document", "query"], settings: Settings
) -> list[list[float]]:
    batches = list(document_batches(texts, settings))
    if not batches:
        return []
    if not settings.voyage_api_key.strip() or settings.voyage_api_key.startswith("your_"):
        raise EmbeddingError("VOYAGE_API_KEY is not configured")
    try:
        client = voyageai.Client(
            api_key=settings.voyage_api_key, max_retries=0, timeout=settings.voyage_timeout_seconds
        )
    except Exception:
        raise EmbeddingError("Voyage client initialization failed") from None
    return [vector for batch in batches for vector in _request(client, batch, kind, settings)]


def embed_documents(texts: list[str], settings: Settings) -> list[list[float]]:
    return _embed(texts, "document", settings)


def embed_query(question: str, settings: Settings) -> list[float]:
    return _embed([question], "query", settings)[0]
