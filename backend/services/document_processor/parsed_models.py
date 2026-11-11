"""Page-aware extraction contracts independent of the provider SDK."""

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class ParsingError(RuntimeError):
    """A safe extraction error; never include provider secrets or paper text."""


class BoundingBox(BaseModel):
    x: float = Field(ge=0, allow_inf_nan=False)
    y: float = Field(ge=0, allow_inf_nan=False)
    width: float = Field(gt=0, allow_inf_nan=False)
    height: float = Field(gt=0, allow_inf_nan=False)
    coordinate_system: Literal["normalized", "points", "provider"]

    @model_validator(mode="after")
    def validate_normalized_bounds(self) -> "BoundingBox":
        if self.coordinate_system == "normalized":
            if self.x + self.width > 1.000001 or self.y + self.height > 1.000001:
                raise ValueError("Normalized coordinates must fit within the page")
        return self


class SourceElement(BaseModel):
    element_id: str
    document_id: str = Field(pattern=r"^[0-9a-f]{24}$")
    page_number: int = Field(ge=1)
    element_index: int = Field(ge=0)
    kind: str
    text: str = ""
    markdown: str = ""
    source: Literal["items", "layout"]
    provider_element_id: str | None = None
    bbox: BoundingBox | None = None
    bounding_boxes: list[BoundingBox] = Field(default_factory=list)
    parent_element_id: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class ParsedPage(BaseModel):
    document_id: str = Field(pattern=r"^[0-9a-f]{24}$")
    page_number: int = Field(ge=1)
    markdown: str
    width: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    height: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    elements: list[SourceElement] = Field(default_factory=list)


class ParsedDocument(BaseModel):
    document_id: str = Field(pattern=r"^[0-9a-f]{24}$")
    pages: list[ParsedPage] = Field(min_length=1)
    provider: Literal["llamaparse"] = "llamaparse"
    provider_job_id: str | None = None

    def as_markdown(self) -> str:
        """Explicit page separators preserve attribution for later chunking."""
        return "\n\n".join(
            f"--- Page {page.page_number} ---\n\n{page.markdown}" for page in self.pages
        )
