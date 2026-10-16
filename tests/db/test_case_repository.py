from promptgauge.db.case_repository import CaseRepository
from promptgauge.db.database import Database

CASES = [
    {"index": 0, "input": "hi", "expected": "hello", "tags": ["greet"]},
    {"index": 1, "input": "bye", "context": "ctx"},
]


def test_upsert_is_idempotent_and_decodes_tags(db: Database) -> None:
    repo = CaseRepository(db)
    ids = repo.upsert_many("d1", CASES)
    assert ids == repo.upsert_many("d1", CASES)
    rows = repo.list_by_dataset("d1")
    assert [r["input"] for r in rows] == ["hi", "bye"]
    assert rows[0]["tags"] == ["greet"] and rows[1]["tags"] == []
    assert rows[0]["expected"] == "hello" and rows[1]["context"] == "ctx"
    assert "tags_json" not in rows[0]
    got = repo.get(ids[1])
    assert got is not None and got["input"] == "bye" and got["tags"] == []
    assert repo.get(999) is None


def test_datasets_lists_hashes_with_counts(db: Database) -> None:
    repo = CaseRepository(db)
    repo.upsert_many("d1", CASES)
    repo.upsert_many("d2", CASES[:1])
    summary = {row["dataset_hash"]: row["case_count"] for row in repo.datasets()}
    assert summary == {"d1": 2, "d2": 1}
    assert all(row["first_seen"] for row in repo.datasets())
