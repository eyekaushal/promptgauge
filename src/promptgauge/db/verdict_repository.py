"""VerdictRepository: the verdict table; one row per measured segment."""

from promptgauge.db.database import Database, Row


class VerdictRepository:
    """Store the bootstrap result and colour for each segment."""

    def __init__(self, database: Database) -> None:
        self._db = database

    def upsert(
        self,
        experiment_id: int,
        segment_id: int,
        *,
        mean_delta: float,
        ci_low: float,
        ci_high: float,
        n_cases: int,
        verdict: str,
        stage: int,
    ) -> None:
        """Insert the verdict for a segment, replacing an earlier one for the same segment."""
        self._db.execute(
            """
            INSERT INTO verdict (experiment_id, segment_id, mean_delta, ci_low, ci_high, n_cases,
                                 verdict, stage)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (segment_id) DO UPDATE SET
                mean_delta = excluded.mean_delta, ci_low = excluded.ci_low,
                ci_high = excluded.ci_high, n_cases = excluded.n_cases,
                verdict = excluded.verdict, stage = excluded.stage
            """,
            (experiment_id, segment_id, mean_delta, ci_low, ci_high, n_cases, verdict, stage),
        )

    def list_by_experiment(self, experiment_id: int) -> list[Row]:
        """All verdicts of one experiment ordered by segment id."""
        return self._db.query_all(
            "SELECT * FROM verdict WHERE experiment_id = ? ORDER BY segment_id", (experiment_id,)
        )
