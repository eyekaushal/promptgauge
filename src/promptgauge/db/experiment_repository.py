"""ExperimentRepository: the experiment table and its one-to-one ablation row."""

from promptgauge.core.clock import utc_now_iso
from promptgauge.db.database import Database, Row


class ExperimentRepository:
    """Create, finish and read experiments; store the ablation summary row."""

    def __init__(self, database: Database) -> None:
        self._db = database

    def create(
        self,
        *,
        kind: str,
        name: str | None,
        prompt_hash: str,
        prompt_text: str,
        dataset_hash: str,
        model: str,
        judge: str,
        config_json: str,
    ) -> int:
        """Insert a `running` experiment and return its id."""
        cursor = self._db.execute(
            """
            INSERT INTO experiment (kind, name, prompt_hash, prompt_text, dataset_hash, model,
                                    judge, config_json, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'running', ?)
            """,
            (
                kind,
                name,
                prompt_hash,
                prompt_text,
                dataset_hash,
                model,
                judge,
                config_json,
                utc_now_iso(),
            ),
        )
        return int(cursor.lastrowid or 0)

    def finish(self, experiment_id: int, status: str, stopped_reason: str | None = None) -> None:
        """Set the final status (`done`, `partial`, `stopped`) and the finish time."""
        self._db.execute(
            "UPDATE experiment SET status = ?, stopped_reason = ?, finished_at = ? WHERE id = ?",
            (status, stopped_reason, utc_now_iso(), experiment_id),
        )

    def get(self, experiment_id: int) -> Row | None:
        """One experiment, or None."""
        return self._db.query_one("SELECT * FROM experiment WHERE id = ?", (experiment_id,))

    def count(self) -> int:
        """How many experiments exist, whatever their kind or status."""
        row = self._db.query_one("SELECT COUNT(*) AS n FROM experiment")
        assert row is not None  # an aggregate always returns one row
        return int(row["n"])

    def list(self, kind: str | None = None) -> list[Row]:
        """Experiments newest first, optionally filtered by kind."""
        if kind is None:
            return self._db.query_all("SELECT * FROM experiment ORDER BY id DESC")
        return self._db.query_all(
            "SELECT * FROM experiment WHERE kind = ? ORDER BY id DESC", (kind,)
        )

    def save_ablation(
        self,
        experiment_id: int,
        *,
        baseline_score: float,
        cut_score: float | None,
        cut_ci_low: float | None,
        cut_ci_high: float | None,
        cut_prompt: str,
        tokens_before: int,
        tokens_after: int,
        confirmed: bool,
    ) -> None:
        """Insert or replace the ablation summary for an experiment."""
        self._db.execute(
            """
            INSERT OR REPLACE INTO ablation (experiment_id, baseline_score, cut_score, cut_ci_low,
                                             cut_ci_high, cut_prompt, tokens_before, tokens_after,
                                             confirmed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                experiment_id,
                baseline_score,
                cut_score,
                cut_ci_low,
                cut_ci_high,
                cut_prompt,
                tokens_before,
                tokens_after,
                int(confirmed),
            ),
        )

    def get_ablation(self, experiment_id: int) -> Row | None:
        """The ablation summary row, or None if the run never got that far."""
        return self._db.query_one(
            "SELECT * FROM ablation WHERE experiment_id = ?", (experiment_id,)
        )
