"""Migrator: applies db/migrations/*.sql in name order, each exactly once."""

from pathlib import Path

from promptgauge.core.clock import utc_now_iso
from promptgauge.db.database import Database

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


class Migrator:
    """Tracks applied files in `schema_migration` so re-running is a no-op."""

    def __init__(self, database: Database, migrations_dir: Path = MIGRATIONS_DIR) -> None:
        self._db = database
        self._dir = migrations_dir

    def apply(self) -> list[str]:
        """Apply every pending migration; return the names applied this time."""
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS schema_migration "
            "(name TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        done = {row["name"] for row in self._db.query_all("SELECT name FROM schema_migration")}
        applied: list[str] = []
        for file in sorted(self._dir.glob("*.sql")):
            if file.name in done:
                continue
            # executescript issues its own COMMIT first, so the file and its bookkeeping row are
            # written back to back rather than inside one transaction.
            self._db.executescript(file.read_text(encoding="utf-8"))
            self._db.execute(
                "INSERT INTO schema_migration (name, applied_at) VALUES (?, ?)",
                (file.name, utc_now_iso()),
            )
            applied.append(file.name)
        return applied

    def applied(self) -> list[str]:
        """Names of migrations already applied, in order."""
        rows = self._db.query_all("SELECT name FROM schema_migration ORDER BY name")
        return [row["name"] for row in rows]
