"""App: FastAPI factory; routes under /api; static dashboard mounted last. PRD F7.1."""

from collections.abc import Callable
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from promptgauge.api.ablations_routes import AblationsRoutes
from promptgauge.api.cases_routes import CasesRoutes
from promptgauge.api.experiments_routes import ExperimentsRoutes
from promptgauge.api.host_guard import HostGuard
from promptgauge.api.models import HealthOut
from promptgauge.api.settings_routes import SettingsRoutes
from promptgauge.config.config import Config
from promptgauge.core.logger import Logger
from promptgauge.db.call_repository import CallRepository
from promptgauge.db.case_repository import CaseRepository
from promptgauge.db.database import Database
from promptgauge.db.experiment_repository import ExperimentRepository
from promptgauge.db.result_repository import ResultRepository
from promptgauge.db.segment_repository import SegmentRepository
from promptgauge.db.settings_repository import SettingsRepository
from promptgauge.db.verdict_repository import VerdictRepository

STATIC_DIR = Path(__file__).parent / "static"


class App:
    """Builds the FastAPI application over one database. Reads SQLite only; never imports
    provider, runner or ablate (invariant 6)."""

    def __init__(
        self,
        database: Database,
        config: Config | None,
        key_present: Callable[[], bool],
        logger: Logger,
        *,
        port: int = 7331,
        static_dir: Path = STATIC_DIR,
    ) -> None:
        self._db = database
        self._config = config
        self._key_present = key_present
        self._log = logger
        self._port = port
        self._static_dir = static_dir

    def build(self) -> FastAPI:
        """The application with every route, the host guard and the static mount."""
        app = FastAPI(title="promptgauge", docs_url=None, redoc_url=None)
        experiments = ExperimentRepository(self._db)
        cases = CaseRepository(self._db)
        calls = CallRepository(self._db)
        experiment_routes = ExperimentsRoutes(experiments, cases, ResultRepository(self._db), calls)
        ablation_routes = AblationsRoutes(
            experiments,
            SegmentRepository(self._db),
            VerdictRepository(self._db),
            calls,
            experiment_routes,
        )
        settings_routes = SettingsRoutes(
            SettingsRepository(self._db), self._config, self._key_present
        )
        app.add_api_route("/api/health", self.health, methods=["GET"])
        for routes in (CasesRoutes(cases), experiment_routes, ablation_routes, settings_routes):
            app.include_router(routes.router, prefix="/api")
        app.add_exception_handler(Exception, self._internal_error)
        self._mount_static(app)
        app.add_middleware(HostGuard, port=self._port)
        return app

    def health(self) -> HealthOut:
        """Liveness plus which database file is being read."""
        return HealthOut(status="ok", database=self._db.path)

    def _mount_static(self, app: FastAPI) -> None:
        # The built dashboard is optional in a dev checkout; without it `/` says so instead of
        # failing at startup.
        if (self._static_dir / "index.html").is_file():
            app.mount("/", StaticFiles(directory=self._static_dir, html=True), name="dashboard")
            return

        async def missing() -> PlainTextResponse:
            return PlainTextResponse(
                "dashboard not built: run `cd dashboard && npm install && npm run build`",
                status_code=404,
            )

        app.add_api_route("/", missing, methods=["GET"], include_in_schema=False)

    async def _internal_error(self, request: Request, exc: Exception) -> JSONResponse:
        # F7.4: details go to the server log, the client sees only that something failed.
        self._log.error(
            "request failed", method=request.method, path=request.url.path, error=repr(exc)
        )
        return JSONResponse(status_code=500, content={"detail": "internal server error"})
