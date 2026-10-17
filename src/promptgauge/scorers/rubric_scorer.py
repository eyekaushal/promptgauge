"""RubricScorer: judge reads rubric + input + output, returns {score, reason}. PRD F3.3."""

from importlib.resources import files
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from promptgauge.core.errors import ScorerError
from promptgauge.dataset.case import Case
from promptgauge.scorers.judge import Judge
from promptgauge.scorers.score_result import ScoreResult
from promptgauge.scorers.scorer import Scorer

BUILT_IN_RUBRICS = ("helpful", "concise", "on_topic", "tone_professional", "follows_instructions")


class _RubricAnswer(BaseModel):
    model_config = ConfigDict(extra="ignore")

    score: float = Field(ge=0.0, le=1.0)
    reason: str


class RubricScorer(Scorer):
    """Scores every case against one rubric: a built-in name or a path to a rubric file."""

    def __init__(self, name_or_path: str | Path) -> None:
        self._name, self._rubric = self._load(name_or_path)
        self._system = Judge.prompt("rubric")
        self._judge: Judge | None = None

    @property
    def key(self) -> str:
        return f"rubric:{self._name}"

    @property
    def rubric(self) -> str:
        """The rubric text the judge sees."""
        return self._rubric

    @property
    def uses_judge(self) -> bool:
        return True

    def bind(self, judge: Judge) -> None:
        self._judge = judge

    async def score(self, case: Case, output: str) -> ScoreResult:
        if self._judge is None:
            raise ScorerError(f"{self.key}: no judge bound; call bind() before scoring")
        user = f"Rubric:\n{self._rubric}\n\nUser input:\n{case.input}\n\nModel output:\n{output}"
        answer = await self._judge.ask(self._system, user, _RubricAnswer)
        if answer is None:
            return ScoreResult(score=None, reason="judge_failed")
        return ScoreResult(score=answer.score, reason=answer.reason)

    @staticmethod
    def _load(name_or_path: str | Path) -> tuple[str, str]:
        name = str(name_or_path)
        if name in BUILT_IN_RUBRICS:
            text = (files("promptgauge") / "rubrics" / f"{name}.md").read_text("utf-8")
            return name, text.strip()
        path = Path(name_or_path)
        if path.is_file():
            return path.stem, path.read_text(encoding="utf-8").strip()
        raise ScorerError(
            f"rubric: unknown rubric '{name}'; use one of {', '.join(BUILT_IN_RUBRICS)} "
            "or a path to a rubric file"
        )
