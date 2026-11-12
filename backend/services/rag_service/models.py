"""Document-scoped retrieval and public chat contracts."""

from typing import Any

from backend.services.document_processor.chunk_models import DocumentChunk
from backend.services.summary_service.models import Evidence, StrictModel
from backend.shared.citation_models import CitationBox
from pydantic import BaseModel, Field, model_validator


class RagUnavailable(RuntimeError):
    """Safe provider/search error without credentials or research text."""


class RagNotReady(LookupError):
    """Current embeddings/search generation is not ready."""


class RagConflict(RuntimeError):
    """Conversation busy or its document generation changed."""


class ChatRequest(StrictModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{32}$")


class RetrievalScope(BaseModel):
    document_id: str
    chunk_set_id: str
    parse_run_id: str
    embedding_profile_id: str

    def filters(self) -> dict[str, str]:
        return self.model_dump(exclude={"parse_run_id"})


class RetrievalHit(BaseModel):
    chunk: DocumentChunk
    rrf_score: float = 0


class AnswerClaim(StrictModel):
    text: str = Field(min_length=1, max_length=1200)
    sources: list[Evidence] = Field(min_length=1, max_length=3)


class AnswerDraft(StrictModel):
    is_out_of_scope: bool
    general_background: str = Field(default="", max_length=4000)
    claims: list[AnswerClaim] = Field(max_length=8)

    @model_validator(mode="after")
    def require_claims_or_abstention(self) -> "AnswerDraft":
        if bool(self.claims) == self.is_out_of_scope:
            raise ValueError(
                "Supported answers need sourced claims; unsupported answers need no claims"
            )
        return self


class ChatCitation(BaseModel):
    citation_id: str
    document_id: str
    chunk_id: str
    page_number: int
    quote_snippet: str
    chunk_set_id: str | None = None
    parse_run_id: str | None = None
    page_width: float | None = None
    page_height: float | None = None
    source_element_ids: list[str] = Field(default_factory=list)
    bounding_boxes: list[CitationBox] = Field(default_factory=list)


class ChatResponse(BaseModel):
    document_id: str
    conversation_id: str
    turn_id: str
    answer: str
    citations: list[ChatCitation]
    is_out_of_scope: bool


class EvaluationTrace(BaseModel):
    question: str
    answer: str
    document_id: str
    retrieved_contexts: list[str]
    retrieved_chunk_ids: list[str]
    source_pages: list[list[int]]
    citations: list[ChatCitation]
    latency_ms: float
    configuration: dict[str, Any]


class PipelineOutput(BaseModel):
    response: ChatResponse
    trace: EvaluationTrace
