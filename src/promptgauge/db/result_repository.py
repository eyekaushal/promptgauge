"""ResultRepository: the result table; one row per case, repeat, variant and scorer."""

from promptgauge.db.database import Database, Row


class ResultRepository:
    """Store scores and read them back per experiment."""

    def __init__(self, database: Database) -> None:
        self._db = database

    def insert_many(self, experiment_id: int, results: list[Row]) -> None:
        """Insert rows keyed case_id, repeat_index, variant_id, scorer, score, reason, call_hash."""
        self._db.executemany(
            """
            INSERT INTO result (experiment_id, case_id, repeat_index, variant_id, scorer, score,
                                reason, call_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    experiment_id,
                    r["case_id"],
                    r["repeat_index"],
                    r.get("variant_id"),
                    r["scorer"],
                    r.get("score"),
                    r.get("reason"),
                    r["call_hash"],
                )
                for r in results
            ],
        )

    def list_by_experiment(self, experiment_id: int) -> list[Row]:
        """All results of one experiment ordered by case, repeat, scorer."""
        return self._db.query_all(
            """
            SELECT * FROM result WHERE experiment_id = ?
            ORDER BY variant_id, case_id, repeat_index, scorer
            """,
            (experiment_id,),
        )

    def list_by_variant(self, experiment_id: int, variant_id: int | None) -> list[Row]:
        """Results for the baseline (variant_id None) or one variant."""
        if variant_id is None:
            return self._db.query_all(
                "SELECT * FROM result WHERE experiment_id = ? AND variant_id IS NULL "
                "ORDER BY case_id, repeat_index, scorer",
                (experiment_id,),
            )
        return self._db.query_all(
            "SELECT * FROM result WHERE experiment_id = ? AND variant_id = ? "
            "ORDER BY case_id, repeat_index, scorer",
            (experiment_id, variant_id),
        )
