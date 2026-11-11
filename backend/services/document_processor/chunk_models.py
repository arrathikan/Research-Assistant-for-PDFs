"""Chunking contracts with explicit per-page evidence and deterministic identity."""

from backend.services.document_processor.parsed_models import SourceElement
from backend.shared.models import ChunkMetadata
from pydantic import BaseModel, Field, model_validator


class ChunkingError(RuntimeError):
    """A safe chunking error without research text or storage details."""


class ChunkingConfig(BaseModel):
    chunk_size: int = Field(default=1200, gt=0, strict=True)
    chunk_overlap: int = Field(default=150, ge=0, strict=True)

    @model_validator(mode="after")
    def validate_overlap(self) -> "ChunkingConfig":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        return self


class ChunkPageSpan(BaseModel):
    page_number: int = Field(ge=1)
    chunk_start: int = Field(ge=0)
    chunk_end: int = Field(gt=0)
    text: str = Field(min_length=1)
    page_width: float | None = None
    page_height: float | None = None
    source_elements: list[SourceElement] = Field(default_factory=list)


class DocumentChunk(ChunkMetadata):
    id: str = Field(alias="_id", pattern=r"^[0-9a-f]{64}$")
    document_id: str = Field(pattern=r"^[0-9a-f]{24}$")
    chunk_index: int = Field(ge=0)
    content: str = Field(min_length=1)
    parse_run_id: str
    chunk_set_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    page_numbers: list[int] = Field(min_length=1)
    page_end: int = Field(ge=1)
    heading_path: dict[str, str] = Field(default_factory=dict)
    page_spans: list[ChunkPageSpan] = Field(min_length=1)
    chunk_size: int
    chunk_overlap: int
    splitter_version: str
    algorithm_version: str

    @model_validator(mode="after")
    def validate_source_attribution(self) -> "DocumentChunk":
        if len(self.content) > self.chunk_size:
            raise ValueError("Chunk exceeds configured character limit")
        if self.page_numbers != sorted({span.page_number for span in self.page_spans}):
            raise ValueError("Chunk pages do not match evidence spans")
        if self.page_number != self.page_numbers[0] or self.page_end != self.page_numbers[-1]:
            raise ValueError("Chunk page range does not match evidence")
        for span in self.page_spans:
            if (
                span.chunk_start >= span.chunk_end
                or self.content[span.chunk_start : span.chunk_end] != span.text
            ):
                raise ValueError("Source span does not match chunk content")
            for element in span.source_elements:
                if (
                    element.document_id != self.document_id
                    or element.page_number != span.page_number
                ):
                    raise ValueError("Source element belongs to another document/page")
        return self
