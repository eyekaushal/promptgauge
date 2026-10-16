"""ScorerSpec: one normalised scorer entry from promptgauge.yaml."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

ScorerName = Literal["contains", "exact", "json_schema", "rubric", "grounded"]

# Free scorers are listed as a bare string; configured ones as a one-key mapping (PRD F1.1).
FREE_SCORERS: frozenset[str] = frozenset({"contains", "exact", "grounded"})
CONFIGURED_SCORERS: frozenset[str] = frozenset({"json_schema", "rubric"})


class ScorerSpec(BaseModel):
    """A scorer name plus its single argument (rubric name or path, schema path), if any."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: ScorerName
    arg: str | None = None

    @model_validator(mode="after")
    def _arg_matches_kind(self) -> "ScorerSpec":
        if self.name in FREE_SCORERS and self.arg is not None:
            raise ValueError(f"scorer '{self.name}' takes no argument")
        if self.name in CONFIGURED_SCORERS and not self.arg:
            raise ValueError(f"scorer '{self.name}' needs a value, e.g. '{self.name}: <value>'")
        return self

    @property
    def key(self) -> str:
        """Stable label used in the result table, e.g. `rubric:helpful`."""
        return self.name if self.arg is None else f"{self.name}:{self.arg}"

    @classmethod
    def parse(cls, entry: object) -> "ScorerSpec":
        """Build from a YAML entry: a string, or a mapping with exactly one key."""
        if isinstance(entry, str):
            return cls(name=entry)  # type: ignore[arg-type]
        if isinstance(entry, dict) and len(entry) == 1:
            (name, arg), *_ = entry.items()
            return cls(name=name, arg=None if arg is None else str(arg))
        raise ValueError("each scorer is a name or a one-key mapping like 'rubric: helpful'")
