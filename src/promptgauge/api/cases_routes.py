"""CasesRoutes: GET /datasets, GET /datasets/{hash}/cases."""

from fastapi import APIRouter, HTTPException

from promptgauge.api.models import CaseOut, DatasetSummary
from promptgauge.db.case_repository import CaseRepository


class CasesRoutes:
    """Datasets seen so far and the cases of one of them."""

    def __init__(self, cases: CaseRepository) -> None:
        self._cases = cases
        self._router = APIRouter()
        self._router.add_api_route("/datasets", self.list_datasets, methods=["GET"])
        self._router.add_api_route(
            "/datasets/{dataset_hash}/cases", self.list_cases, methods=["GET"]
        )

    @property
    def router(self) -> APIRouter:
        """The routes, for `App` to include under /api."""
        return self._router

    def list_datasets(self) -> list[DatasetSummary]:
        """Every dataset hash with its case count and first-seen time, newest first."""
        return [DatasetSummary(**row) for row in self._cases.datasets()]

    def list_cases(self, dataset_hash: str) -> list[CaseOut]:
        """The cases of one dataset in index order; 404 for a hash never stored."""
        rows = self._cases.list_by_dataset(dataset_hash)
        if not rows:
            raise HTTPException(status_code=404, detail=f"dataset not found: {dataset_hash}")
        return [CaseOut(**row) for row in rows]
