from promptgauge.db.database import Database
from promptgauge.db.settings_repository import SettingsRepository


def test_get_returns_none_when_unset(db: Database) -> None:
    assert SettingsRepository(db).get("calls_per_month") is None


def test_set_then_get_and_all(db: Database) -> None:
    repo = SettingsRepository(db)
    repo.set("calls_per_month", "5000")
    repo.set("inr_rate", "84.0")
    assert repo.get("calls_per_month") == "5000"
    assert repo.all() == {"calls_per_month": "5000", "inr_rate": "84.0"}


def test_set_replaces_an_existing_value(db: Database) -> None:
    repo = SettingsRepository(db)
    repo.set("inr_rate", "84.0")
    repo.set("inr_rate", "90.5")
    assert repo.get("inr_rate") == "90.5"
