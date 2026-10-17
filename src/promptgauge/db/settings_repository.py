"""SettingsRepository: the settings table; display settings only (`calls_per_month`, `inr_rate`)."""

from promptgauge.db.database import Database


class SettingsRepository:
    """Read and write the key/value display settings the dashboard may change (PRD F7.2)."""

    def __init__(self, database: Database) -> None:
        self._db = database

    def get(self, key: str) -> str | None:
        """The stored value for a key, or None when it was never set."""
        row = self._db.query_one("SELECT value FROM settings WHERE key = ?", (key,))
        return None if row is None else str(row["value"])

    def all(self) -> dict[str, str]:
        """Every stored setting."""
        return {row["key"]: row["value"] for row in self._db.query_all("SELECT * FROM settings")}

    def set(self, key: str, value: str) -> None:
        """Insert or replace one setting."""
        self._db.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT (key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
