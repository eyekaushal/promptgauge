import pytest
from fastapi.testclient import TestClient


def test_list_is_newest_first_with_scores_and_totals(client: TestClient, seeded) -> None:
    body = client.get("/api/experiments").json()
    assert [e["name"] for e in body] == ["cut", "second", "first"]
    first = body[-1]
    assert first["kind"] == "eval" and first["status"] == "done"
    # Run scores: case 0 → (1.0+0.5)/2 and 1.0 ; case 1 → (0.5+0.25)/2 and 0.5. Mean = 0.65625.
    assert first["score"] == pytest.approx(0.65625)
    assert first["scorer_means"] == {"contains": 0.75, "rubric:helpful": pytest.approx(0.375)}
    assert first["cases"] == 2
    assert first["totals"] == {
        "calls": 4,
        "cached": 2,
        "input_tokens": 40,
        "output_tokens": 20,
        "cost_usd": pytest.approx(0.004),
    }
    assert "prompt_text" not in first


def test_list_filters_by_kind(client: TestClient, seeded) -> None:
    assert [e["kind"] for e in client.get("/api/experiments?kind=ablation").json()] == ["ablation"]
    assert client.get("/api/experiments?kind=bogus").status_code == 422


def test_get_carries_prompt_config_and_per_case_scores(client: TestClient, seeded) -> None:
    body = client.get(f"/api/experiments/{seeded['eval_a']}").json()
    assert body["prompt_text"].startswith("# Role")
    assert body["config"] == {"delta": 0.05, "repeats": 2}
    assert body["repeats"] == 2
    assert body["cases"] == 2
    assert [c["index"] for c in body["case_scores"]] == [0, 1]
    case_0 = body["case_scores"][0]
    assert case_0["input"] == "hello"
    assert case_0["score"] == pytest.approx(0.875)
    assert case_0["scorer_means"] == {"contains": 1.0, "rubric:helpful": 0.5}


def test_get_unknown_id_is_404_and_bad_id_is_422(client: TestClient, seeded) -> None:
    assert client.get("/api/experiments/999").status_code == 404
    assert client.get("/api/experiments/abc").status_code == 422


def test_results_are_per_case_repeat_scorer_with_output(client: TestClient, seeded) -> None:
    rows = client.get(f"/api/experiments/{seeded['eval_a']}/results").json()
    assert len(rows) == 8
    row = next(
        r
        for r in rows
        if r["case_index"] == 1 and r["repeat_index"] == 1 and r["scorer"] == "rubric:helpful"
    )
    assert row["score"] is None and row["reason"] == "judge"
    assert row["variant_id"] is None
    assert row["output"] == f"out {seeded['case_1']}/1"
    assert client.get("/api/experiments/999/results").status_code == 404


def test_compare_two_runs(client: TestClient, seeded) -> None:
    body = client.get(f"/api/experiments/compare?a={seeded['eval_a']}&b={seeded['eval_b']}").json()
    assert body["a"]["name"] == "first" and body["b"]["name"] == "second"
    assert body["delta"] == pytest.approx(0.4375 - 0.65625)
    assert body["scorers"]["contains"] == {"a": 0.75, "b": 0.5, "delta": -0.25}
    assert [c["index"] for c in body["cases"]] == [0, 1]
    assert body["cases"][0] == {
        "index": 0,
        "input": "hello",
        "a": pytest.approx(0.875),
        "b": pytest.approx(0.4375),
        "delta": pytest.approx(-0.4375),
    }


def test_compare_validates_its_parameters(client: TestClient, seeded) -> None:
    assert client.get("/api/experiments/compare").status_code == 422
    assert client.get(f"/api/experiments/compare?a={seeded['eval_a']}").status_code == 422
    assert client.get(f"/api/experiments/compare?a={seeded['eval_a']}&b=999").status_code == 404
