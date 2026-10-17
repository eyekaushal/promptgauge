"""SettingsRoutes: GET /settings (config echo, api_key_present, display settings), PUT /settings
(display settings only).
"""

from collections.abc import Callable

from fastapi import APIRouter

from promptgauge.api.models import SettingsIn, SettingsOut
from promptgauge.config.config import Config
from promptgauge.db.settings_repository import SettingsRepository

DEFAULT_CALLS_PER_MONTH = 100_000
DEFAULT_INR_RATE = 84.0


class SettingsRoutes:
    """What the dashboard shows in Settings. The key itself never leaves the process
    (invariant 8): `key_present` answers yes or no and nothing else."""

    def __init__(
        self,
        settings: SettingsRepository,
        config: Config | None,
        key_present: Callable[[], bool],
    ) -> None:
        self._settings = settings
        self._config = config
        self._key_present = key_present
        self._router = APIRouter()
        self._router.add_api_route("/settings", self.get, methods=["GET"])
        self._router.add_api_route("/settings", self.put, methods=["PUT"])

    @property
    def router(self) -> APIRouter:
        """The routes, for `App` to include under /api."""
        return self._router

    def get(self) -> SettingsOut:
        """Config echo (None when `promptgauge ui` found no config), key presence, settings."""
        stored = self._settings.all()
        inr_default = self._config.inr_rate if self._config else DEFAULT_INR_RATE
        return SettingsOut(
            config=None if self._config is None else self._config.model_dump(mode="json"),
            api_key_present=self._key_present(),
            calls_per_month=int(stored.get("calls_per_month", DEFAULT_CALLS_PER_MONTH)),
            inr_rate=float(stored.get("inr_rate", inr_default)),
        )

    def put(self, body: SettingsIn) -> SettingsOut:
        """Store the display settings given in the body and return the full settings."""
        for key, value in body.model_dump(exclude_none=True).items():
            self._settings.set(key, str(value))
        return self.get()
