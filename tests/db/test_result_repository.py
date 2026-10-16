from promptgauge.db.case_repository import CaseRepository
from promptgauge.db.database import Database
from promptgauge.db.result_repository import ResultRepository


def test_insert_many_and_read_back_by_variant(db: Database, experiment_id: int) -> None:
    case_ids = CaseRepository(db).upsert_many("d", [{"index": 0, "input": "a"}])
    repo = ResultRepository(db)
    repo.insert_many(
        experiment_id,
        [
            {
                "case_id": case_ids[0],
                "repeat_index": 0,
                "scorer": "contains",
                "score": 1.0,
                "call_hash": "h",
            },
            {
                "case_id": case_ids[0],
                "repeat_index": 0,
                "variant_id": 7,
                "scorer": "contains",
                "score": None,
                "reason": "judge_failed",
                "call_hash": "h2",
            },
        ],
    )
    rows = repo.list_by_experiment(experiment_id)
    assert len(rows) == 2
    baseline = repo.list_by_variant(experiment_id, None)
    assert len(baseline) == 1 and baseline[0]["variant_id"] is None and baseline[0]["score"] == 1.0
    variant = repo.list_by_variant(experiment_id, 7)
    assert len(variant) == 1 and variant[0]["score"] is None
    assert variant[0]["reason"] == "judge_failed"
    assert repo.list_by_variant(experiment_id, 8) == []
