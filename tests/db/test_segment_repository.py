from promptgauge.db.database import Database
from promptgauge.db.segment_repository import SegmentRepository


def test_blocks_and_lines_round_trip(db: Database, experiment_id: int) -> None:
    repo = SegmentRepository(db)
    block = repo.insert(
        experiment_id,
        parent_segment_id=None,
        level="block",
        index=0,
        start_offset=0,
        end_offset=10,
        text="Be nice.\nBe brief.",
        tokens=6,
    )
    line = repo.insert(
        experiment_id,
        parent_segment_id=block,
        level="line",
        index=0,
        start_offset=0,
        end_offset=8,
        text="Be nice.",
        tokens=3,
    )
    rows = repo.list_by_experiment(experiment_id)
    assert [r["id"] for r in rows] == [block, line]
    assert rows[1]["parent_segment_id"] == block and rows[1]["level"] == "line"
    got = repo.get(line)
    assert got is not None and got["text"] == "Be nice."
    assert repo.get(999) is None
