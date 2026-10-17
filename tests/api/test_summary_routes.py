from fastapi.testclient import TestClient


def test_empty_database_sums_to_zero(client: TestClient) -> None:
    assert client.get("/api/summary").json() == {
        "runs": 0,
        "calls": 0,
        "cached": 0,
        "cost_usd": 0.0,
    }


def test_summary_counts_every_run_and_call(client: TestClient, seeded: dict[str, int]) -> None:
    # Three runs, each with two cases × two repeats; the second repeat of every case is a hit.
    body = client.get("/api/summary").json()
    assert body["runs"] == 3
    assert body["calls"] == 12
    assert body["cached"] == 6
    assert abs(body["cost_usd"] - 0.012) < 1e-9
