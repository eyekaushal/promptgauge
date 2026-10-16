"""CallRepository: the call table; cache lookups and per-experiment totals."""

from promptgauge.core.clock import utc_now_iso
from promptgauge.db.database import Database, Row


class CallRepository:
    """Write every call (cached or not) and answer totals from the rows, never from memory."""

    def __init__(self, database: Database) -> None:
        self._db = database

    def insert(
        self,
        *,
        hash: str,
        model: str,
        system_hash: str,
        input_hash: str,
        temperature: float,
        repeat_index: int,
        output: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        cached: bool,
        experiment_id: int,
    ) -> int:
        """Record one call and return its row id."""
        cursor = self._db.execute(
            """
            INSERT INTO call (hash, model, system_hash, input_hash, temperature, repeat_index,
                              output, input_tokens, output_tokens, cost_usd, cached,
                              experiment_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                hash,
                model,
                system_hash,
                input_hash,
                temperature,
                repeat_index,
                output,
                input_tokens,
                output_tokens,
                cost_usd,
                int(cached),
                experiment_id,
                utc_now_iso(),
            ),
        )
        return int(cursor.lastrowid or 0)

    def find_original(self, hash: str) -> Row | None:
        """The row that actually hit the network for this hash, or None (a cache miss)."""
        return self._db.query_one(
            "SELECT * FROM call WHERE hash = ? AND cached = 0 ORDER BY id LIMIT 1", (hash,)
        )

    def list_by_experiment(self, experiment_id: int) -> list[Row]:
        """All calls of one experiment in insertion order."""
        return self._db.query_all(
            "SELECT * FROM call WHERE experiment_id = ? ORDER BY id", (experiment_id,)
        )

    def totals(self, experiment_id: int) -> Row:
        """calls, cached, input_tokens, output_tokens and cost_usd summed over one experiment."""
        row = self._db.query_one(
            """
            SELECT COUNT(*)                        AS calls,
                   COALESCE(SUM(cached), 0)        AS cached,
                   COALESCE(SUM(input_tokens), 0)  AS input_tokens,
                   COALESCE(SUM(output_tokens), 0) AS output_tokens,
                   COALESCE(SUM(cost_usd), 0.0)    AS cost_usd
            FROM call WHERE experiment_id = ?
            """,
            (experiment_id,),
        )
        assert row is not None  # an aggregate always returns one row
        return row
