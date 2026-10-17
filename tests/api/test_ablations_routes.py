import pytest
from fastapi.testclient import TestClient

from promptgauge.db.experiment_repository import ExperimentRepository


def test_ablation_carries_segments_verdicts_row_and_totals(client: TestClient, seeded) -> None:
    body = client.get(f"/api/ablations/{seeded['ablation']}").json()
    assert body["experiment"]["kind"] == "ablation"
    assert body["prompt_text"].startswith("# Role")
    assert body["delta"] == 0.05
    assert body["legend"]["grey"] == "no measurable effect at this sample size"
    assert [s["id"] for s in body["segments"]] == [
        seeded["block"],
        seeded["body"],
        seeded["line"],
        seeded["unmeasured"],
    ]
    by_id = {s["id"]: s for s in body["segments"]}
    assert by_id[seeded["block"]]["verdict"]["verdict"] == "grey"
    assert by_id[seeded["body"]]["verdict"] == {
        "mean_delta": -0.3,
        "ci_low": -0.4,
        "ci_high": -0.2,
        "n_cases": 2,
        "verdict": "red",
        "stage": 1,
    }
    assert by_id[seeded["line"]]["parent_segment_id"] == seeded["body"]
    assert by_id[seeded["unmeasured"]]["verdict"] is None
    assert body["ablation"] == {
        "baseline_score": 1.0,
        "cut_score": 0.98,
        "cut_ci_low": 0.9,
        "cut_ci_high": 1.0,
        "cut_prompt": "Be brief.\nBe kind.\n",
        "tokens_before": 8,
        "tokens_after": 6,
        "confirmed": True,
    }
    assert body["totals"]["calls"] == 4
    assert body["experiment"]["score"] == pytest.approx(0.875)


def test_verdicts_are_repainted_from_the_interval_with_the_runs_delta(
    client: TestClient, seeded
) -> None:
    # Stored as grey; ci_low 0.1 > delta 0.05, so the rule says green.
    body = client.get(f"/api/ablations/{seeded['ablation']}").json()
    line = next(s for s in body["segments"] if s["id"] == seeded["line"])
    assert line["verdict"]["verdict"] == "green"


def test_ablation_row_is_null_for_a_run_that_stopped_early(client: TestClient, db, seeded) -> None:
    stopped = ExperimentRepository(db).create(
        kind="ablation",
        name="stopped",
        prompt_hash="p",
        prompt_text="x",
        dataset_hash="d" * 8,
        model="m",
        judge="j",
        config_json="{}",
    )
    ExperimentRepository(db).finish(stopped, "stopped", "budget")
    body = client.get(f"/api/ablations/{stopped}").json()
    assert body["ablation"] is None
    assert body["segments"] == []
    assert body["experiment"]["stopped_reason"] == "budget"
    assert body["delta"] == 0.03  # the rule's default when config_json carries none


def test_eval_and_unknown_ids_are_404(client: TestClient, seeded) -> None:
    assert client.get(f"/api/ablations/{seeded['eval_a']}").status_code == 404
    assert client.get("/api/ablations/999").status_code == 404
