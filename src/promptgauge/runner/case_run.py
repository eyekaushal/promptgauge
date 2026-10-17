"""CaseRun: one (case, repeat) with its output, scores and reasons, or its error."""

from dataclasses import dataclass, field
from statistics import fmean

from promptgauge.dataset.case import Case
from promptgauge.scorers.score_result import ScoreResult


@dataclass(frozen=True)
class CaseRun:
    """What happened to one case on one repeat. `error` set means no output and no scores."""

    case: Case
    case_id: int
    repeat_index: int
    output: str | None = None
    call_hash: str | None = None
    cached: bool = False
    scores: dict[str, ScoreResult] = field(default_factory=dict)
    error: str | None = None

    @property
    def failed(self) -> bool:
        """True when the model call (or a judge call) raised."""
        return self.error is not None

    @property
    def score(self) -> float | None:
        """Mean over scorers that returned a value (PRD F3.6); None if none did."""
        values = [r.score for r in self.scores.values() if r.score is not None]
        return fmean(values) if values else None
