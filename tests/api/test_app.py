from pathlib import Path

from fastapi.testclient import TestClient

from promptgauge.db.experiment_repository import ExperimentRepository
from tests.api.conftest import BASE_URL


def test_health_reports_the_database(client: TestClient) -> None:
    assert client.get("/api/health").json() == {"status": "ok", "database": ":memory:"}


def test_unknown_api_path_is_404(client: TestClient) -> None:
    assert client.get("/api/nothing").status_code == 404


def test_root_without_a_built_dashboard_says_so(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 404
    assert "dashboard not built" in response.text


def test_root_serves_the_built_dashboard(app_factory, tmp_path: Path) -> None:
    static = tmp_path / "built"
    static.mkdir()
    (static / "index.html").write_text("<html><body>promptgauge</body></html>")
    (static / "app.js").write_text("console.log(1)")
    with TestClient(app_factory(static_dir=static).build(), base_url=BASE_URL) as c:
        assert "promptgauge" in c.get("/").text
        assert c.get("/app.js").text == "console.log(1)"
        # The API still wins over the static mount.
        assert c.get("/api/health").status_code == 200


def test_unexpected_error_is_a_500_without_details(client: TestClient, monkeypatch) -> None:
    def boom(self, experiment_id):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr(ExperimentRepository, "get", boom)
    response = client.get("/api/experiments/1")
    assert response.status_code == 500
    assert response.json() == {"detail": "internal server error"}
    assert "secret" not in response.text
