"""ContainsScorer: expected appears in output after lower-casing and whitespace normalisation. PRD
F3.1.
"""

from promptgauge.dataset.case import Case
from promptgauge.scorers.score_result import ScoreResult
from promptgauge.scorers.scorer import Scorer, normalise


class ContainsScorer(Scorer):
    """1.0 if the normalised expected text is a substring of the normalised output, else 0.0."""

    @property
    def key(self) -> str:
        return "contains"

    def applies_to(self, case: Case) -> bool:
        return case.expected is not None

    async def score(self, case: Case, output: str) -> ScoreResult:
        expected = normalise(case.expected or "")
        if expected in normalise(output):
            return ScoreResult(score=1.0)
        return ScoreResult(score=0.0, reason=f"expected text not found: {case.expected!r}")
