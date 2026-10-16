"""SegmentRepository: the segment table; blocks and the lines inside them."""

from promptgauge.db.database import Database, Row


class SegmentRepository:
    """Store the segmentation of one experiment's prompt and read it back."""

    def __init__(self, database: Database) -> None:
        self._db = database

    def insert(
        self,
        experiment_id: int,
        *,
        parent_segment_id: int | None,
        level: str,
        index: int,
        start_offset: int,
        end_offset: int,
        text: str,
        tokens: int,
    ) -> int:
        """Insert one segment and return its id."""
        cursor = self._db.execute(
            """
            INSERT INTO segment (experiment_id, parent_segment_id, level, "index", start_offset,
                                 end_offset, text, tokens)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                experiment_id,
                parent_segment_id,
                level,
                index,
                start_offset,
                end_offset,
                text,
                tokens,
            ),
        )
        return int(cursor.lastrowid or 0)

    def get(self, segment_id: int) -> Row | None:
        """One segment, or None."""
        return self._db.query_one("SELECT * FROM segment WHERE id = ?", (segment_id,))

    def list_by_experiment(self, experiment_id: int) -> list[Row]:
        """All segments of one experiment in document order (level, then index)."""
        return self._db.query_all(
            'SELECT * FROM segment WHERE experiment_id = ? ORDER BY start_offset, level, "index"',
            (experiment_id,),
        )
