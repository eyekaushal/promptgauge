"""MeanInterval: mean difference, its percentile interval and the number of cases behind it."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MeanInterval(BaseModel):
    """What one bootstrap produces and what the verdict row stores (PRD F6.4, F6.5). Storing the
    interval rather than the colour lets the dashboard repaint for any `delta` without recomputing.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    mean: float
    ci_low: float
    ci_high: float
    n_cases: int = Field(ge=1)

    @model_validator(mode="after")
    def _ordered(self) -> "MeanInterval":
        if not self.ci_low <= self.mean <= self.ci_high:
            raise ValueError("expected ci_low <= mean <= ci_high")
        return self
