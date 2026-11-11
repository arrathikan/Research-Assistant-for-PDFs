"""Source geometry retained independently from answer-quality evaluation."""

from typing import Literal

from pydantic import BaseModel, Field


class CitationBox(BaseModel):
    element_id: str
    x: float = Field(ge=0, allow_inf_nan=False)
    y: float = Field(ge=0, allow_inf_nan=False)
    width: float = Field(gt=0, allow_inf_nan=False)
    height: float = Field(gt=0, allow_inf_nan=False)
    coordinate_system: Literal["normalized", "points", "provider"]
    origin: Literal["top_left", "unknown"] = "unknown"
    rotation_degrees: float | None = Field(default=None, allow_inf_nan=False)
    renderable: bool = False
