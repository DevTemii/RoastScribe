"""Pydantic schemas for requests, persona plugins and roast output."""
from typing import Literal

from pydantic import BaseModel, Field, field_validator

InputType = Literal["idea", "github", "url", "image"]


class RoastRequest(BaseModel):
    input_type: InputType
    content: str = Field(..., min_length=1, max_length=8_000_000)
    # Persona ids are plugin-defined, so validated at runtime against the
    # loaded plugins instead of a hard-coded Literal.
    persona: str = "cynical_vc"
    spice_level: Literal[1, 2, 3] = 2

    @field_validator("content")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("content must not be empty")
        return v


class CringeMetrics(BaseModel):
    buzzword_score: str = Field(..., examples=["8/10"])
    buzzwords_found: list[str] = []
    uniqueness_rating: str
    survival_probability: str = Field(..., examples=["14%"])


class TheRescue(BaseModel):
    fatal_flaw: str
    who_might_actually_pay: str
    the_pivot: str


class RoastResponse(BaseModel):
    product_name: str
    one_line_summary: str
    roast_title: str
    the_burn: list[str] = Field(..., min_length=1, max_length=6)
    cringe_metrics: CringeMetrics
    the_rescue: TheRescue
    # Extra metadata (not produced by the model): which engine answered.
    engine: Literal["gemma", "mock"] = "gemma"
    persona: str | None = None


class ParsedInput(BaseModel):
    """Normalised output shared by every parser."""

    source: InputType
    title: str | None = None
    text: str
    image_b64: str | None = None
    meta: dict[str, str] = {}


class Persona(BaseModel):
    id: str
    name: str
    emoji: str = "🔥"
    tagline: str
    voice_traits: list[str]
    catchphrases: list[str]
    pet_peeves: list[str]
    # Used by the offline mock engine to open the roast in character.
    mock_openers: list[str] = []
