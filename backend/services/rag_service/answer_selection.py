"""Select canonical evidence by key instead of asking the model to copy source metadata."""

import json
from typing import Annotated

from backend.services.rag_service.models import AnswerDraft, RagUnavailable
from backend.services.summary_service.models import StrictModel
from pydantic import Field, ValidationError


class SelectedClaim(StrictModel):
    text: str = Field(min_length=1, max_length=1200)
    source_keys: list[Annotated[int, Field(strict=True, ge=1)]] = Field(min_length=1, max_length=3)


class SelectedAnswer(StrictModel):
    general_background: str = Field(default="", max_length=4000)
    claims: list[SelectedClaim] = Field(max_length=8)


def source_passages(text: str, first_key: int) -> list[dict]:
    """Serialize every source word in short, exact, non-overlapping quote windows.

    These windows are prompt/citation material only. Stored Markdown chunks,
    embedding inputs and retrieval rankings are unchanged.
    """
    result = []
    remaining = text.strip()
    while remaining:
        end = len(remaining)
        if end > 280:
            end = remaining.rfind(" ", 0, 280)
            if end <= 0:
                end = 280
        quote = remaining[:end].strip()
        result.append({"key": first_key + len(result), "text": quote})
        remaining = remaining[end:].lstrip()
    return result


def materialize_answer(raw: str, payload: str) -> str:
    """Build source IDs/pages/quotes exclusively from selected current passages."""
    try:
        data = json.loads(raw)
        # Existing injected completion adapters may still use the validated draft
        # contract. They retain the same strict source validation downstream.
        if isinstance(data, dict) and "is_out_of_scope" in data:
            return raw
        draft = SelectedAnswer.model_validate(data)
        sources = {
            passage["key"]: {
                "chunk_id": chunk["chunk_id"],
                "page_number": page["page_number"],
                "quote": passage["text"],
            }
            for chunk in json.loads(payload)["contexts"]
            for page in chunk["pages"]
            for passage in page["passages"]
        }
        claims = [
            {
                "text": claim.text,
                "sources": [sources[key] for key in dict.fromkeys(claim.source_keys)],
            }
            for claim in draft.claims
        ]
        return AnswerDraft(
            is_out_of_scope=not claims,
            claims=claims,
            general_background=draft.general_background,
        ).model_dump_json()
    except (ValueError, ValidationError, KeyError, TypeError):
        raise RagUnavailable("Answer selection failed validation; no answer was saved") from None
