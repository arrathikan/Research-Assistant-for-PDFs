"""Embedding identity and validation without provider/database dependencies."""

import json
from hashlib import sha256
from math import isfinite
from typing import Literal

from pydantic import BaseModel


class EmbeddingError(RuntimeError):
    """Safe provider/vector error; never include API keys or research text."""


class EmbeddingInputError(ValueError):
    """Input is empty or exceeds the configured conservative request guard."""


class EmbeddingProfile(BaseModel):
    provider: Literal["voyageai"] = "voyageai"
    model: str
    dimensions: int
    input_type: Literal["document"] = "document"
    output_dtype: Literal["float"] = "float"
    algorithm_version: Literal["voyage-text-v1"] = "voyage-text-v1"

    @property
    def id(self) -> str:
        data = json.dumps(self.model_dump(), sort_keys=True, separators=(",", ":"))
        return sha256(data.encode()).hexdigest()


def validate_vectors(raw: object, count: int, dimensions: int) -> list[list[float]]:
    if not isinstance(raw, list) or len(raw) != count:
        raise EmbeddingError("Voyage returned an invalid embedding count")
    vectors = []
    for row in raw:
        if not isinstance(row, list) or len(row) != dimensions:
            raise EmbeddingError("Embedding vector dimensions do not match configuration")
        if any(
            not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value)
            for value in row
        ):
            raise EmbeddingError("Embedding vector contains invalid numeric values")
        vector = [float(value) for value in row]
        if not any(vector):
            raise EmbeddingError("Embedding vector cannot be zero for cosine search")
        vectors.append(vector)
    return vectors
