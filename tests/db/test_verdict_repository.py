from promptgauge.db.database import Database
from promptgauge.db.segment_repository import SegmentRepository
from promptgauge.db.verdict_repository import VerdictRepository


def test_upsert_replaces_the_verdict_for_a_segment(db: Database, experiment_id: int) -> None:
    segment = SegmentRepository(db).insert(
        experiment_id,
        parent_segment_id=None,
        level="block",
        index=0,
        start_offset=0,
        end_offset=3,
        text="abc",
        tokens=1,
    )
    repo = VerdictRepository(db)
    repo.upsert(
        experiment_id,
        segment,
        mean_delta=-0.1,
        ci_low=-0.2,
        ci_high=-0.05,
        n_cases=10,
        verdict="red",
        stage=1,
    )
    repo.upsert(
        experiment_id,
        segment,
        mean_delta=0.0,
        ci_low=-0.02,
        ci_high=0.02,
        n_cases=10,
        verdict="grey",
        stage=1,
    )
    rows = repo.list_by_experiment(experiment_id)
    assert len(rows) == 1
    assert rows[0]["verdict"] == "grey" and rows[0]["mean_delta"] == 0.0
    assert rows[0]["segment_id"] == segment
