from pathlib import Path

from fastapi.testclient import TestClient

from promptgauge.config.config import Config
from tests.api.conftest import BASE_URL


def test_defaults_without_config_or_key(client: TestClient) -> None:
    assert client.get("/api/settings").json() == {
        "config": None,
        "api_key_present": False,
        "calls_per_month": 100000,
        "inr_rate": 84.0,
    }


def test_key_is_reported_as_present_only(client: TestClient, key_state, monkeypatch) -> None:
    key_state["present"] = True
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-should-never-appear")
    response = client.get("/api/settings")
    assert response.json()["api_key_present"] is True
    assert "sk-ant" not in response.text


def test_config_is_echoed_and_sets_the_inr_default(app_factory, project: Path) -> None:
    (project / "promptgauge.yaml").write_text(
        (project / "promptgauge.yaml").read_text() + "inr_rate: 90\n"
    )
    config = Config.load(project / "promptgauge.yaml")
    with TestClient(app_factory(config=config).build(), base_url=BASE_URL) as c:
        body = c.get("/api/settings").json()
    assert body["config"]["model"] == "claude-sonnet-4-5"
    assert body["config"]["prompt"] == str(project / "system.md")
    assert body["config"]["scorers"] == [
        {"name": "contains", "arg": None},
        {"name": "rubric", "arg": "helpful"},
    ]
    assert body["inr_rate"] == 90.0


def test_put_stores_display_settings_and_keeps_the_rest(client: TestClient) -> None:
    response = client.put("/api/settings", json={"calls_per_month": 5000})
    assert response.status_code == 200
    assert response.json()["calls_per_month"] == 5000
    assert response.json()["inr_rate"] == 84.0
    client.put("/api/settings", json={"inr_rate": 91.5})
    body = client.get("/api/settings").json()
    assert body == {
        "config": None,
        "api_key_present": False,
        "calls_per_month": 5000,
        "inr_rate": 91.5,
    }


def test_put_rejects_bad_or_unknown_fields(client: TestClient) -> None:
    assert client.put("/api/settings", json={"calls_per_month": 0}).status_code == 422
    assert client.put("/api/settings", json={"inr_rate": -1}).status_code == 422
    assert client.put("/api/settings", json={"api_key": "sk-ant-x"}).status_code == 422
    assert client.put("/api/settings", json={"calls_per_month": "many"}).status_code == 422
    assert client.get("/api/settings").json()["calls_per_month"] == 100000
