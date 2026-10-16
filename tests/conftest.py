"""Shared fixtures. Tests never touch the network: in-memory SQLite, FakeProvider (from B04)."""

from collections.abc import Iterator
from pathlib import Path

import pytest

from promptgauge.db.database import Database
from promptgauge.db.migrator import Migrator


@pytest.fixture
def db() -> Iterator[Database]:
    """A fresh in-memory database with every migration applied."""
    database = Database()
    Migrator(database).apply()
    yield database
    database.close()


@pytest.fixture
def experiment_id(db: Database) -> int:
    """One `running` eval experiment to hang rows off."""
    from promptgauge.db.experiment_repository import ExperimentRepository

    return ExperimentRepository(db).create(
        kind="eval",
        name="fixture",
        prompt_hash="p" * 8,
        prompt_text="Be helpful.",
        dataset_hash="d" * 8,
        model="claude-sonnet-4-5",
        judge="claude-haiku-4-5",
        config_json="{}",
    )


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A minimal project directory: promptgauge.yaml, system.md, cases.jsonl, schema.json."""
    (tmp_path / "system.md").write_text("You are a support bot.\n")
    (tmp_path / "cases.jsonl").write_text('{"input": "hi"}\n')
    (tmp_path / "schema.json").write_text('{"type": "object"}')
    (tmp_path / "promptgauge.yaml").write_text(
        "prompt: system.md\ndataset: cases.jsonl\nmodel: claude-sonnet-4-5\n"
        "scorers:\n  - contains\n  - rubric: helpful\n"
    )
    return tmp_path
