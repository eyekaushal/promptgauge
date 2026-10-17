"""ExactScorer: full equality under the same normalisation."""

from promptgauge.dataset.case import Case
from promptgauge.scorers.score_result import ScoreResult
from promptgauge.scorers.scorer import Scorer, normalise


class ExactScorer(Scorer):
    """1.0 if the normalised output equals the normalised expected text, else 0.0."""

    @property
    def key(self) -> str:
        return "exact"

    def applies_to(self, case: Case) -> bool:
        return case.expected is not None

    async def score(self, case: Case, output: str) -> ScoreResult:
        if normalise(output) == normalise(case.expected or ""):
            return ScoreResult(score=1.0)
        return ScoreResult(score=0.0, reason=f"output differs from expected: {case.expected!r}")
