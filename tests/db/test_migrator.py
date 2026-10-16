from pathlib import Path

from promptgauge.db.database import Database
from promptgauge.db.migrator import Migrator

EXPECTED_TABLES = {
    "experiment",
    "case",
    "call",
    "result",
    "segment",
    "verdict",
    "ablation",
    "settings",
}


def _tables(db: Database) -> set[str]:
    rows = db.query_all("SELECT name FROM sqlite_master WHERE type = 'table'")
    return {row["name"] for row in rows}


def test_apply_creates_every_table_once() -> None:
    db = Database()
    migrator = Migrator(db)
    assert migrator.apply() == ["001_init.sql"]
    assert EXPECTED_TABLES <= _tables(db)
    assert migrator.apply() == []
    assert migrator.applied() == ["001_init.sql"]


def test_apply_runs_pending_files_in_name_order(tmp_path: Path) -> None:
    (tmp_path / "002_b.sql").write_text("CREATE TABLE b (x);")
    (tmp_path / "001_a.sql").write_text("CREATE TABLE a (x);")
    db = Database()
    assert Migrator(db, tmp_path).apply() == ["001_a.sql", "002_b.sql"]
    (tmp_path / "003_c.sql").write_text("CREATE TABLE c (x);")
    assert Migrator(db, tmp_path).apply() == ["003_c.sql"]
    assert {"a", "b", "c"} <= _tables(db)
