"""Segment: level (block/line), parent, index, start/end character offsets, text, tokens."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Segment(BaseModel):
    """One deletable piece of the prompt. Offsets are absolute character positions in the full
    prompt text for blocks and lines alike, so a variant is always a plain slice (PRD F5.1–F5.4).

    `index` is the 0-based position among siblings: blocks in document order, lines inside their
    block. `parent_index` is the owning block's index for a line and None for a block. Database
    ids are assigned when the ablation writes the rows, not here.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    level: Literal["block", "line"]
    index: int = Field(ge=0)
    parent_index: int | None = None
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    text: str = Field(min_length=1)
    tokens: int = Field(ge=0)

    @model_validator(mode="after")
    def _consistent(self) -> "Segment":
        if self.end - self.start != len(self.text):
            raise ValueError("end - start must equal len(text)")
        if (self.level == "block") != (self.parent_index is None):
            raise ValueError("blocks have no parent_index; lines must have one")
        return self

    def is_fenced_code(self) -> bool:
        """True when the whole segment is one fenced code block (``` or ~~~)."""
        first = self.text.split("\n", 1)[0].lstrip()
        return first.startswith("```") or first.startswith("~~~")
