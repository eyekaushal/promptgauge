from promptgauge.db.database import Database
from promptgauge.db.experiment_repository import ExperimentRepository


def test_create_get_list_finish(db: Database) -> None:
    repo = ExperimentRepository(db)
    first = repo.create(
        kind="eval",
        name="a",
        prompt_hash="p1",
        prompt_text="P",
        dataset_hash="d",
        model="m",
        judge="j",
        config_json="{}",
    )
    second = repo.create(
        kind="ablation",
        name=None,
        prompt_hash="p2",
        prompt_text="P",
        dataset_hash="d",
        model="m",
        judge="j",
        config_json="{}",
    )
    row = repo.get(first)
    assert row is not None
    assert row["status"] == "running" and row["finished_at"] is None and row["name"] == "a"
    assert [r["id"] for r in repo.list()] == [second, first]
    assert [r["id"] for r in repo.list(kind="ablation")] == [second]

    repo.finish(second, "stopped", stopped_reason="budget")
    row = repo.get(second)
    assert row is not None
    assert (row["status"], row["stopped_reason"]) == ("stopped", "budget")
    assert row["finished_at"] is not None
    assert repo.get(999) is None


def test_ablation_row_round_trip(db: Database, experiment_id: int) -> None:
    repo = ExperimentRepository(db)
    assert repo.get_ablation(experiment_id) is None
    repo.save_ablation(
        experiment_id,
        baseline_score=0.8,
        cut_score=None,
        cut_ci_low=None,
        cut_ci_high=None,
        cut_prompt="A",
        tokens_before=10,
        tokens_after=4,
        confirmed=False,
    )
    repo.save_ablation(
        experiment_id,
        baseline_score=0.8,
        cut_score=0.79,
        cut_ci_low=-0.02,
        cut_ci_high=0.01,
        cut_prompt="A",
        tokens_before=10,
        tokens_after=4,
        confirmed=True,
    )
    row = repo.get_ablation(experiment_id)
    assert row is not None
    assert row["cut_score"] == 0.79 and row["confirmed"] == 1 and row["tokens_after"] == 4
