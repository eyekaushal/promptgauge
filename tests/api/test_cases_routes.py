from fastapi.testclient import TestClient

from tests.api.conftest import DATASET


def test_datasets_lists_hash_count_and_first_seen(client: TestClient, seeded) -> None:
    body = client.get("/api/datasets").json()
    assert len(body) == 1
    assert body[0]["dataset_hash"] == DATASET
    assert body[0]["case_count"] == 2
    assert body[0]["first_seen"]


def test_datasets_is_empty_on_a_fresh_database(client: TestClient) -> None:
    assert client.get("/api/datasets").json() == []


def test_cases_of_a_dataset_in_index_order(client: TestClient, seeded) -> None:
    body = client.get(f"/api/datasets/{DATASET}/cases").json()
    assert [c["index"] for c in body] == [0, 1]
    assert body[0] == {
        "id": seeded["case_0"],
        "dataset_hash": DATASET,
        "index": 0,
        "input": "hello",
        "expected": "hi",
        "context": None,
        "tags": ["greet"],
    }
    assert body[1]["context"] == "ctx" and body[1]["tags"] == []


def test_unknown_dataset_is_404(client: TestClient, seeded) -> None:
    response = client.get("/api/datasets/nope/cases")
    assert response.status_code == 404
    assert "nope" in response.json()["detail"]
