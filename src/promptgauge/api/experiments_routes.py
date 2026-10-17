"""ExperimentsRoutes: GET /experiments, /experiments/{id}, /experiments/{id}/results,
/experiments/compare.
"""

import json

from fastapi import APIRouter, HTTPException

from promptgauge.api.models import (
    CaseScore,
    CompareCase,
    CompareOut,
    CompareScorer,
    ExperimentDetail,
    ExperimentSummary,
    ResultOut,
    Totals,
)
from promptgauge.api.score_summary import ScoreSummary
from promptgauge.db.call_repository import CallRepository
from promptgauge.db.case_repository import CaseRepository
from promptgauge.db.database import Row
from promptgauge.db.experiment_repository import ExperimentRepository
from promptgauge.db.result_repository import ResultRepository


class ExperimentsRoutes:
    """The runs table, one run, its result rows, and two runs side by side."""

    def __init__(
        self,
        experiments: ExperimentRepository,
        cases: CaseRepository,
        results: ResultRepository,
        calls: CallRepository,
    ) -> None:
        self._experiments = experiments
        self._cases = cases
        self._results = results
        self._calls = calls
        self._router = APIRouter()
        self._router.add_api_route("/experiments", self.list_experiments, methods=["GET"])
        # `compare` is registered before `{experiment_id}` so the literal path wins.
        self._router.add_api_route("/experiments/compare", self.compare, methods=["GET"])
        self._router.add_api_route("/experiments/{experiment_id}", self.get, methods=["GET"])
        self._router.add_api_route(
            "/experiments/{experiment_id}/results", self.list_results, methods=["GET"]
        )

    @property
    def router(self) -> APIRouter:
        """The routes, for `App` to include under /api."""
        return self._router

    def list_experiments(self, kind: str | None = None) -> list[ExperimentSummary]:
        """Every run newest first, optionally only `eval` or `ablation`."""
        if kind is not None and kind not in ("eval", "ablation"):
            raise HTTPException(status_code=422, detail="kind must be 'eval' or 'ablation'")
        return [self.summary(row) for row in self._experiments.list(kind)]

    def get(self, experiment_id: int) -> ExperimentDetail:
        """One run with its prompt, config and per-case baseline scores."""
        row = self.require(experiment_id)
        summary = self._summary(experiment_id)
        per_case = summary.per_case()
        cases = []
        for case in self._cases.list_by_dataset(row["dataset_hash"]):
            scored = per_case.get(case["id"])
            if scored is None:
                continue
            cases.append(
                CaseScore(case_id=case["id"], index=case["index"], input=case["input"], **scored)
            )
        return ExperimentDetail(
            **self.summary(row, summary).model_dump(),
            prompt_text=row["prompt_text"],
            config=json.loads(row["config_json"]),
            repeats=max((c.repeats for c in cases), default=0),
            cases=cases,
        )

    def list_results(self, experiment_id: int) -> list[ResultOut]:
        """Every result row (case, repeat, variant, scorer) with the output it scored."""
        row = self.require(experiment_id)
        index_of = {c["id"]: c["index"] for c in self._cases.list_by_dataset(row["dataset_hash"])}
        output_of = {c["hash"]: c["output"] for c in self._calls.list_by_experiment(experiment_id)}
        return [
            ResultOut(
                case_index=index_of.get(r["case_id"], -1),
                output=output_of.get(r["call_hash"]),
                **r,
            )
            for r in self._results.list_by_experiment(experiment_id)
        ]

    def compare(self, a: int, b: int) -> CompareOut:
        """Baseline scores of two runs side by side, by scorer and by case index."""
        row_a, row_b = self.require(a), self.require(b)
        sum_a, sum_b = self._summary(a), self._summary(b)
        means_a, means_b = sum_a.scorer_means(), sum_b.scorer_means()
        scorers = {
            key: CompareScorer(
                a=means_a.get(key),
                b=means_b.get(key),
                delta=_delta(means_a.get(key), means_b.get(key)),
            )
            for key in dict.fromkeys([*means_a, *means_b])
        }
        cases_a = self._by_index(row_a["dataset_hash"], sum_a)
        cases_b = self._by_index(row_b["dataset_hash"], sum_b)
        cases = []
        for index in sorted(set(cases_a) | set(cases_b)):
            input_text, score_a = cases_a.get(index, (None, None))
            input_b, score_b = cases_b.get(index, (None, None))
            cases.append(
                CompareCase(
                    index=index,
                    input=input_text if input_text is not None else input_b or "",
                    a=score_a,
                    b=score_b,
                    delta=_delta(score_a, score_b),
                )
            )
        return CompareOut(
            a=self.summary(row_a, sum_a),
            b=self.summary(row_b, sum_b),
            delta=_delta(sum_a.score, sum_b.score),
            scorers=scorers,
            cases=cases,
        )

    def require(self, experiment_id: int) -> Row:
        """The experiment row, or a 404."""
        row = self._experiments.get(experiment_id)
        if row is None:
            raise HTTPException(status_code=404, detail=f"experiment not found: {experiment_id}")
        return row

    def summary(self, row: Row, summary: ScoreSummary | None = None) -> ExperimentSummary:
        """The runs-table row for one experiment; shared with the ablation route."""
        scores = summary or self._summary(row["id"])
        return ExperimentSummary(
            score=scores.score,
            scorer_means=scores.scorer_means(),
            totals=Totals(**self._calls.totals(row["id"])),
            **row,
        )

    def _summary(self, experiment_id: int) -> ScoreSummary:
        return ScoreSummary(self._results.list_by_variant(experiment_id, None))

    def _by_index(
        self, dataset_hash: str, summary: ScoreSummary
    ) -> dict[int, tuple[str, float | None]]:
        per_case = summary.per_case()
        return {
            c["index"]: (c["input"], per_case[c["id"]]["score"])
            for c in self._cases.list_by_dataset(dataset_hash)
            if c["id"] in per_case
        }


def _delta(a: float | None, b: float | None) -> float | None:
    return None if a is None or b is None else b - a
