"""CaseRepository: the case table, keyed by dataset hash and row index."""

import json

from promptgauge.core.clock import utc_now_iso
from promptgauge.db.database import Database, Row


class CaseRepository:
    """Store a loaded dataset once per hash and read it back."""

    def __init__(self, database: Database) -> None:
        self._db = database

    def upsert_many(self, dataset_hash: str, cases: list[Row]) -> list[int]:
        """Insert cases (keys: index, input, expected, context, tags) that are not stored yet.

        Returns the row ids in index order, existing or new.
        """
        now = utc_now_iso()
        with self._db.transaction():
            for case in cases:
                self._db.execute(
                    """
                    INSERT OR IGNORE INTO "case"
                        (dataset_hash, "index", input, expected, context, tags_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        dataset_hash,
                        case["index"],
                        case["input"],
                        case.get("expected"),
                        case.get("context"),
                        json.dumps(case.get("tags") or []),
                        now,
                    ),
                )
        return [row["id"] for row in self.list_by_dataset(dataset_hash)]

    def list_by_dataset(self, dataset_hash: str) -> list[Row]:
        """All cases of one dataset in index order, with `tags` decoded."""
        rows = self._db.query_all(
            'SELECT * FROM "case" WHERE dataset_hash = ? ORDER BY "index"', (dataset_hash,)
        )
        for row in rows:
            row["tags"] = json.loads(row.pop("tags_json"))
        return rows

    def get(self, case_id: int) -> Row | None:
        """One case by id, with `tags` decoded."""
        row = self._db.query_one('SELECT * FROM "case" WHERE id = ?', (case_id,))
        if row is not None:
            row["tags"] = json.loads(row.pop("tags_json"))
        return row

    def datasets(self) -> list[Row]:
        """Every dataset hash with its case count and first-seen time, newest first."""
        return self._db.query_all(
            """
            SELECT dataset_hash, COUNT(*) AS case_count, MIN(created_at) AS first_seen
            FROM "case" GROUP BY dataset_hash ORDER BY first_seen DESC
            """
        )
