"""EvalResult: per-scorer means, per-case table, calls, cached, cost, duration, status."""

from dataclasses import dataclass
from statistics import fmean

from promptgauge.runner.case_run import CaseRun


@dataclass(frozen=True)
class CaseSummary:
    """One row of the per-case table: means over repeats, per scorer and overall."""

    index: int
    input: str
    scorer_means: dict[str, float | None]
    score: float | None
    repeats: int
    failures: int


@dataclass(frozen=True)
class EvalResult:
    """Everything `promptgauge eval` prints and the SDK returns. Call counts and cost come from the
    call table, never from an in-memory counter (PRD F2.6)."""

    experiment_id: int
    name: str
    status: str
    model: str
    scorer_keys: list[str]
    runs: list[CaseRun]
    calls: int
    cached: int
    cost_usd: float
    duration_s: float

    @property
    def score(self) -> float | None:
        """Mean over cases and repeats of each run's score (PRD F3.6)."""
        return _mean([run.score for run in self.runs])

    @property
    def repeats(self) -> int:
        """Repeats per case, taken from the runs."""
        return max((run.repeat_index for run in self.runs), default=-1) + 1

    @property
    def failures(self) -> int:
        """Runs whose call failed."""
        return sum(run.failed for run in self.runs)

    @property
    def cached_share(self) -> float:
        """Fraction of calls served from the cache, 0.0 when nothing was called."""
        return self.cached / self.calls if self.calls else 0.0

    def scorer_means(self) -> dict[str, float | None]:
        """Mean per scorer over every run that has a value for it."""
        return {
            key: _mean([run.scores[key].score for run in self.runs if key in run.scores])
            for key in self.scorer_keys
        }

    def per_case(self) -> list[CaseSummary]:
        """One summary per case in dataset order."""
        by_case: dict[int, list[CaseRun]] = {}
        for run in self.runs:
            by_case.setdefault(run.case.index, []).append(run)
        return [
            CaseSummary(
                index=index,
                input=runs[0].case.input,
                scorer_means={
                    key: _mean([r.scores[key].score for r in runs if key in r.scores])
                    for key in self.scorer_keys
                },
                score=_mean([r.score for r in runs]),
                repeats=len(runs),
                failures=sum(r.failed for r in runs),
            )
            for index, runs in sorted(by_case.items())
        ]


def _mean(values: list[float | None]) -> float | None:
    present = [v for v in values if v is not None]
    return fmean(present) if present else None
