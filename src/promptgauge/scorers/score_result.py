"""ScoreResult: score in [0, 1] or None (judge failed), reason."""

from pydantic import BaseModel, ConfigDict, Field


class ScoreResult(BaseModel):
    """One scorer's verdict on one output. `score=None` means the scorer could not decide and the
    value is excluded from means (PRD F3.5); it is not a zero."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    score: float | None = Field(ge=0.0, le=1.0)
    reason: str | None = None
