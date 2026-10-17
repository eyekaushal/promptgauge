"""GroundedScorer: judge lists claims and marks each supported by context; score = supported /
total. PRD F3.4.
"""

from pydantic import BaseModel, ConfigDict

from promptgauge.core.errors import ScorerError
from promptgauge.dataset.case import Case
from promptgauge.scorers.judge import Judge
from promptgauge.scorers.score_result import ScoreResult
from promptgauge.scorers.scorer import Scorer


class _Claim(BaseModel):
    model_config = ConfigDict(extra="ignore")

    text: str
    supported: bool


class _GroundedAnswer(BaseModel):
    model_config = ConfigDict(extra="ignore")

    claims: list[_Claim]


class GroundedScorer(Scorer):
    """Share of the output's factual claims that the case context supports. Skips cases without
    context. An output with no claims is fully grounded."""

    def __init__(self) -> None:
        self._system = Judge.prompt("grounded")
        self._judge: Judge | None = None

    @property
    def key(self) -> str:
        return "grounded"

    def applies_to(self, case: Case) -> bool:
        return case.context is not None

    def bind(self, judge: Judge) -> None:
        self._judge = judge

    async def score(self, case: Case, output: str) -> ScoreResult:
        if self._judge is None:
            raise ScorerError(f"{self.key}: no judge bound; call bind() before scoring")
        user = f"Context:\n{case.context}\n\nModel output:\n{output}"
        answer = await self._judge.ask(self._system, user, _GroundedAnswer)
        if answer is None:
            return ScoreResult(score=None, reason="judge_failed")
        if not answer.claims:
            return ScoreResult(score=1.0, reason="no factual claims")
        unsupported = [claim.text for claim in answer.claims if not claim.supported]
        score = 1.0 - len(unsupported) / len(answer.claims)
        reason = "unsupported: " + "; ".join(unsupported) if unsupported else None
        return ScoreResult(score=score, reason=reason)
