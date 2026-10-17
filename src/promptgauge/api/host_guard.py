"""HostGuard: middleware; Host must be 127.0.0.1:port or localhost:port, else 403. PRD F7.3."""

import json
from collections.abc import Awaitable, Callable
from typing import Any

Scope = dict[str, Any]
Receive = Callable[[], Awaitable[dict[str, Any]]]
Send = Callable[[dict[str, Any]], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


class HostGuard:
    """Pure ASGI middleware: refuses any request whose Host header is not the local server.

    A page on another origin can be made to send requests to 127.0.0.1 through DNS rebinding;
    such requests carry the attacker's host name, so checking the header shuts them out.
    """

    def __init__(self, app: ASGIApp, port: int) -> None:
        self._app = app
        self._allowed = {f"127.0.0.1:{port}", f"localhost:{port}"}

    @property
    def allowed(self) -> frozenset[str]:
        """The exact Host values that pass."""
        return frozenset(self._allowed)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and not self._permitted(scope):
            await self._refuse(send)
            return
        await self._app(scope, receive, send)

    def _permitted(self, scope: Scope) -> bool:
        for name, value in scope.get("headers", []):
            if name == b"host":
                return value.decode("latin-1").lower() in self._allowed
        return False

    @staticmethod
    async def _refuse(send: Send) -> None:
        body = json.dumps({"detail": "forbidden host"}).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 403,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
