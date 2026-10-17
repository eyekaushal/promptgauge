"""ScoreSummary: baseline means from result rows, the way EvalResult computes them from runs."""

from statistics import fmean

from promptgauge.db.database import Row


class ScoreSummary:
    """Means over the baseline rows (variant_id NULL) of one experiment.

    A run is one (case, repeat); its score is the mean of its non-null scorer values, matching
    `CaseRun.score`, so the dashboard shows the same numbers the CLI printed.
    """

    def __init__(self, results: list[Row]) -> None:
        self._rows = [r for r in results if r["variant_id"] is None]
        self._runs: dict[tuple[int, int], list[Row]] = {}
        for row in self._rows:
            self._runs.setdefault((row["case_id"], row["repeat_index"]), []).append(row)

    @property
    def scorer_keys(self) -> list[str]:
        """Every scorer that produced a row, in first-seen order."""
        return list(dict.fromkeys(r["scorer"] for r in self._rows))

    @property
    def score(self) -> float | None:
        """Mean over runs of each run's score; None when nothing was scored."""
        return _mean([self._run_score(rows) for rows in self._runs.values()])

    def scorer_means(self) -> dict[str, float | None]:
        """Mean per scorer over every row that has a value."""
        return {
            key: _mean([r["score"] for r in self._rows if r["scorer"] == key])
            for key in self.scorer_keys
        }

    def per_case(self) -> dict[int, dict]:
        """Keyed by case_id: `score`, `scorer_means` and `repeats` for that case."""
        by_case: dict[int, list[Row]] = {}
        for row in self._rows:
            by_case.setdefault(row["case_id"], []).append(row)
        summary: dict[int, dict] = {}
        for case_id, rows in by_case.items():
            repeats = {r["repeat_index"] for r in rows}
            runs = [[r for r in rows if r["repeat_index"] == i] for i in sorted(repeats)]
            summary[case_id] = {
                "score": _mean([self._run_score(run) for run in runs]),
                "scorer_means": {
                    key: _mean([r["score"] for r in rows if r["scorer"] == key])
                    for key in self.scorer_keys
                },
                "repeats": len(repeats),
            }
        return summary

    @staticmethod
    def _run_score(rows: list[Row]) -> float | None:
        return _mean([r["score"] for r in rows])


def _mean(values: list[float | None]) -> float | None:
    present = [v for v in values if v is not None]
    return fmean(present) if present else None
