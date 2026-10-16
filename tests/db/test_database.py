from pathlib import Path

import pytest

from promptgauge.db.database import Database


def test_memory_database_round_trips() -> None:
    db = Database()
    db.execute("CREATE TABLE t (a INTEGER, b TEXT)")
    db.executemany("INSERT INTO t VALUES (?, ?)", [(1, "x"), (2, "y")])
    assert db.query_all("SELECT * FROM t ORDER BY a") == [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]
    assert db.query_one("SELECT b FROM t WHERE a = ?", (2,)) == {"b": "y"}
    assert db.query_one("SELECT b FROM t WHERE a = ?", (3,)) is None
    assert db.path == ":memory:"


def test_file_database_uses_wal_and_creates_parents(tmp_path: Path) -> None:
    path = tmp_path / ".promptgauge" / "promptgauge.db"
    db = Database(path)
    assert path.is_file()
    assert db.query_one("PRAGMA journal_mode") == {"journal_mode": "wal"}
    assert db.query_one("PRAGMA foreign_keys") == {"foreign_keys": 1}
    db.close()


def test_transaction_rolls_back_on_error() -> None:
    db = Database()
    db.execute("CREATE TABLE t (a INTEGER)")
    with pytest.raises(RuntimeError):
        with db.transaction():
            db.execute("INSERT INTO t VALUES (1)")
            raise RuntimeError("abort")
    assert db.query_all("SELECT * FROM t") == []
    with db.transaction():
        db.execute("INSERT INTO t VALUES (2)")
    assert db.query_all("SELECT * FROM t") == [{"a": 2}]
