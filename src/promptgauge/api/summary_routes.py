"""SummaryRoutes: GET /summary, the totals behind the sidebar's spend card."""

from fastapi import APIRouter

from promptgauge.api.models import SummaryOut
from promptgauge.db.call_repository import CallRepository
from promptgauge.db.experiment_repository import ExperimentRepository


class SummaryRoutes:
    """Runs, calls, cached calls and spend over the whole database. Read-only, two aggregates."""

    def __init__(self, experiments: ExperimentRepository, calls: CallRepository) -> None:
        self._experiments = experiments
        self._calls = calls
        self._router = APIRouter()
        self._router.add_api_route("/summary", self.get, methods=["GET"])

    @property
    def router(self) -> APIRouter:
        """The route, for `App` to include under /api."""
        return self._router

    def get(self) -> SummaryOut:
        """Every run and every call row, cached or not, summed."""
        totals = self._calls.grand_totals()
        return SummaryOut(
            runs=self._experiments.count(),
            calls=int(totals["calls"]),
            cached=int(totals["cached"]),
            cost_usd=float(totals["cost_usd"]),
        )
