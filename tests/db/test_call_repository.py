import pytest

from promptgauge.db.call_repository import CallRepository
from promptgauge.db.database import Database


def _insert(repo: CallRepository, experiment_id: int, *, cached: bool, cost: float) -> int:
    return repo.insert(
        hash="h1",
        model="m",
        system_hash="s",
        input_hash="i",
        temperature=0.7,
        repeat_index=0,
        output="out",
        input_tokens=100,
        output_tokens=10,
        cost_usd=cost,
        cached=cached,
        experiment_id=experiment_id,
    )


def test_find_original_returns_the_network_call_only(db: Database, experiment_id: int) -> None:
    repo = CallRepository(db)
    assert repo.find_original("h1") is None
    _insert(repo, experiment_id, cached=True, cost=0.0)
    assert repo.find_original("h1") is None
    original = _insert(repo, experiment_id, cached=False, cost=0.001)
    _insert(repo, experiment_id, cached=False, cost=0.001)
    found = repo.find_original("h1")
    assert found is not None and found["id"] == original and found["output"] == "out"


def test_totals_come_from_rows(db: Database, experiment_id: int) -> None:
    repo = CallRepository(db)
    assert repo.totals(experiment_id) == {
        "calls": 0,
        "cached": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": 0.0,
    }
    _insert(repo, experiment_id, cached=False, cost=0.002)
    _insert(repo, experiment_id, cached=True, cost=0.0)
    totals = repo.totals(experiment_id)
    assert (totals["calls"], totals["cached"]) == (2, 1)
    assert (totals["input_tokens"], totals["output_tokens"]) == (200, 20)
    assert totals["cost_usd"] == pytest.approx(0.002)
    assert len(repo.list_by_experiment(experiment_id)) == 2
