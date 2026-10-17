from fastapi.testclient import TestClient

from promptgauge.api.host_guard import HostGuard
from tests.api.conftest import PORT


def test_allowed_hosts_are_exactly_the_two_local_names() -> None:
    guard = HostGuard(lambda scope, receive, send: None, PORT)
    assert guard.allowed == {"127.0.0.1:7331", "localhost:7331"}


def test_foreign_host_is_refused(app_factory) -> None:
    with TestClient(app_factory().build(), base_url="http://evil.example:7331") as c:
        response = c.get("/api/health")
    assert response.status_code == 403
    assert response.json() == {"detail": "forbidden host"}


def test_wrong_port_is_refused(app_factory) -> None:
    with TestClient(app_factory().build(), base_url="http://127.0.0.1:8000") as c:
        assert c.get("/api/health").status_code == 403


def test_both_local_names_pass(app_factory) -> None:
    app = app_factory().build()
    for base in ("http://127.0.0.1:7331", "http://localhost:7331", "http://LOCALHOST:7331"):
        with TestClient(app, base_url=base) as c:
            assert c.get("/api/health").status_code == 200, base


def test_missing_host_header_is_refused(app_factory) -> None:
    with TestClient(app_factory().build(), base_url="http://127.0.0.1:7331") as c:
        response = c.get("/api/health", headers={"host": ""})
    assert response.status_code == 403
