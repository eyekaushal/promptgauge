"""Case: one dataset row (input, expected?, context?, tags?). PRD F1.2."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Case(BaseModel):
    """A validated row of cases.jsonl. `index` is the 0-based position in the file."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    index: int = Field(ge=0)
    input: str = Field(min_length=1)
    expected: str | None = None
    context: str | None = None
    tags: list[str] = Field(default_factory=list)

    @field_validator("expected", "context", mode="after")
    @classmethod
    def _blank_is_absent(cls, value: str | None) -> str | None:
        # An empty string means "not provided": scorers skip the case rather than score it 0.
        return value if value else None

    def to_row(self) -> dict[str, object]:
        """The shape CaseRepository.upsert_many expects."""
        return self.model_dump()
