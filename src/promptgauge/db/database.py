"""Database: one sqlite3 connection, WAL mode on disk, ':memory:' for tests."""

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

Row = dict[str, Any]

MEMORY = ":memory:"


class Database:
    """Thin connection wrapper: executes SQL, returns rows as dicts, serialises access."""

    def __init__(self, path: Path | str = MEMORY) -> None:
        self._path = str(path)
        if self._path != MEMORY:
            Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        # FastAPI runs sync route handlers in a thread pool, so the connection must be shareable;
        # the lock keeps statements from interleaving.
        self._conn = sqlite3.connect(self._path, check_same_thread=False, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self._conn.execute("PRAGMA foreign_keys = ON")
        if self._path != MEMORY:
            self._conn.execute("PRAGMA journal_mode = WAL")

    @property
    def path(self) -> str:
        """Where the data lives; ':memory:' in tests."""
        return self._path

    def execute(self, sql: str, params: tuple[Any, ...] | dict[str, Any] = ()) -> sqlite3.Cursor:
        """Run one statement and return its cursor (for `lastrowid`, `rowcount`)."""
        with self._lock:
            return self._conn.execute(sql, params)

    def executemany(self, sql: str, rows: list[tuple[Any, ...]]) -> None:
        """Run one statement for every parameter tuple."""
        with self._lock:
            self._conn.executemany(sql, rows)

    def executescript(self, sql: str) -> None:
        """Run several statements, e.g. a migration file."""
        with self._lock:
            self._conn.executescript(sql)

    def query_one(self, sql: str, params: tuple[Any, ...] = ()) -> Row | None:
        """First matching row as a dict, or None."""
        with self._lock:
            row = self._conn.execute(sql, params).fetchone()
        return None if row is None else dict(row)

    def query_all(self, sql: str, params: tuple[Any, ...] = ()) -> list[Row]:
        """All matching rows as dicts."""
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """Group statements; commits on success, rolls back on any exception."""
        with self._lock:
            self._conn.execute("BEGIN")
            try:
                yield
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
            self._conn.execute("COMMIT")

    def close(self) -> None:
        """Close the connection; the object is unusable afterwards."""
        with self._lock:
            self._conn.close()
