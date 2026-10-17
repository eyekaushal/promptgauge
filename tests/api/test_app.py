from pathlib import Path

from fastapi.testclient import TestClient

from promptgauge.db.experiment_repository import ExperimentRepository
from tests.api.conftest import BASE_URL


def test_health_reports_the_database(client: TestClient) -> None:
    assert client.get("/api/health").json() == {"status": "ok", "database": ":memory:"}


def test_unknown_api_path_is_404(client: TestClient) -> None:
    assert client.get("/api/nothing").status_code == 404


def test_pages_without_a_built_dashboard_say_so(client: TestClient) -> None:
    for path in ("/", "/experiments", "/ablations/3"):
        response = client.get(path)
        assert response.status_code == 404, path
        assert "dashboard not built" in response.text


def test_root_serves_the_built_dashboard(app_factory, tmp_path: Path) -> None:
    static = tmp_path / "built"
    static.mkdir()
    (static / "index.html").write_text("<html><body>promptgauge</body></html>")
    (static / "assets").mkdir()
    (static / "assets" / "app.js").write_text("console.log(1)")
    (static / "favicon.svg").write_text("<svg/>")
    with TestClient(app_factory(static_dir=static).build(), base_url=BASE_URL) as c:
        assert "promptgauge" in c.get("/").text
        assert c.get("/assets/app.js").text == "console.log(1)"
        assert c.get("/favicon.svg").text == "<svg/>"
        # Deep links serve the SPA shell so react-router can take over.
        for path in ("/experiments", "/ablations/3", "/settings"):
            response = c.get(path)
            assert response.status_code == 200 and "promptgauge" in response.text, path
        # The API still wins, and an unknown API path is a JSON 404, never the shell.
        assert c.get("/api/health").status_code == 200
        missing = c.get("/api/nothing")
        assert missing.status_code == 404 and missing.json()["detail"] == "not found: /api/nothing"
        # A path that escapes the static directory is answered with the shell, not the file.
        assert "promptgauge" in c.get("/../index.html").text


def test_unexpected_error_is_a_500_without_details(client: TestClient, monkeypatch) -> None:
    def boom(self, experiment_id):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr(ExperimentRepository, "get", boom)
    response = client.get("/api/experiments/1")
    assert response.status_code == 500
    assert response.json() == {"detail": "internal server error"}
    assert "secret" not in response.text
