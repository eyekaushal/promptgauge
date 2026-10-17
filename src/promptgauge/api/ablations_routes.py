"""AblationsRoutes: GET /ablations/{id}: segments with verdicts, the ablation row, totals."""

import json

from fastapi import APIRouter, HTTPException

from promptgauge.api.experiments_routes import ExperimentsRoutes
from promptgauge.api.models import AblationOut, AblationRow, SegmentOut, Totals, VerdictOut
from promptgauge.config.pricing import Pricing
from promptgauge.core.errors import ProviderError
from promptgauge.db.call_repository import CallRepository
from promptgauge.db.experiment_repository import ExperimentRepository
from promptgauge.db.segment_repository import SegmentRepository
from promptgauge.db.verdict_repository import VerdictRepository
from promptgauge.stats.verdict_rule import VerdictRule

# Invariant 4: the grey wording is fixed and travels with the data so the dashboard repeats it.
LEGEND = {
    "red": "removing this hurts the score",
    "grey": "no measurable effect at this sample size",
    "green": "removing this helps the score",
}


class AblationsRoutes:
    """One ablation: the prompt painted by segment, the cut prompt and its confirmation."""

    def __init__(
        self,
        experiments: ExperimentRepository,
        segments: SegmentRepository,
        verdicts: VerdictRepository,
        calls: CallRepository,
        experiment_routes: ExperimentsRoutes,
        pricing: Pricing,
    ) -> None:
        self._experiments = experiments
        self._segments = segments
        self._verdicts = verdicts
        self._calls = calls
        self._experiment_routes = experiment_routes
        self._pricing = pricing
        self._router = APIRouter()
        self._router.add_api_route("/ablations/{experiment_id}", self.get, methods=["GET"])

    @property
    def router(self) -> APIRouter:
        """The routes, for `App` to include under /api."""
        return self._router

    def get(self, experiment_id: int) -> AblationOut:
        """Segments with their verdicts, the ablation row (None if the run never got there) and
        totals. 404 when the id is not an ablation."""
        row = self._experiment_routes.require(experiment_id)
        if row["kind"] != "ablation":
            raise HTTPException(status_code=404, detail=f"not an ablation: {experiment_id}")
        # Colours are repainted from the stored intervals with the run's own delta, so the rule
        # in stats/ stays the single source of truth (F6.5).
        rule = VerdictRule(float(json.loads(row["config_json"]).get("delta", 0.03)))
        by_segment = {v["segment_id"]: v for v in self._verdicts.list_by_experiment(experiment_id)}
        segments = [
            SegmentOut(verdict=self._verdict(by_segment.get(s["id"]), rule), **s)
            for s in self._segments.list_by_experiment(experiment_id)
        ]
        ablation = self._experiments.get_ablation(experiment_id)
        return AblationOut(
            experiment=self._experiment_routes.summary(row),
            prompt_text=row["prompt_text"],
            delta=rule.delta,
            input_usd_per_million=self._input_price(row["model"]),
            legend=LEGEND,
            segments=segments,
            ablation=None if ablation is None else AblationRow(**ablation),
            totals=Totals(**self._calls.totals(experiment_id)),
        )

    def _input_price(self, model: str) -> float | None:
        # Money saved (F6.9) needs the input price; a model that left the price table since the
        # run still gets its painted prompt, just no money figure.
        try:
            return self._pricing.input_per_million(model)
        except ProviderError:
            return None

    @staticmethod
    def _verdict(row: dict | None, rule: VerdictRule) -> VerdictOut | None:
        if row is None:
            return None
        return VerdictOut(
            mean_delta=row["mean_delta"],
            ci_low=row["ci_low"],
            ci_high=row["ci_high"],
            n_cases=row["n_cases"],
            verdict=rule.verdict(row["ci_low"], row["ci_high"]),
            stage=row["stage"],
        )
