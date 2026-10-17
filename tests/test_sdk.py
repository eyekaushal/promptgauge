import shutil
from pathlib import Path

import pytest

import promptgauge
from promptgauge import scorers
from promptgauge.ablate.ablation_report import AblationReport
from promptgauge.cli import main
from promptgauge.core.errors import BudgetExceededError, ConfigError
from promptgauge.provider.fake_provider import FakeProvider

EXAMPLE = Path(__file__).parent.parent / "examples" / "support-bot"


@pytest.fixture
def example(tmp_path: Path) -> Path:
    target = tmp_path / "support-bot"
    shutil.copytree(EXAMPLE, target)
    return target


def test_evaluate_mixes_scorer_objects_and_config_entries(example: Path, monkeypatch) -> None:
    provider = FakeProvider(default='{"score": 1, "reason": "x"}')
    monkeypatch.setattr(main, "build_provider", lambda pricing, logger: provider)
    result = promptgauge.evaluate(
        dataset=example / "cases.jsonl",
        prompt=example / "system.md",
        model="claude-sonnet-4-5",
        scorers=[scorers.contains(), {"rubric": "concise"}, "exact"],
        repeats=1,
        name="from code",
    )
    assert result.name == "from code"
    assert result.scorer_keys == ["contains", "rubric:concise", "exact"]
    assert len(result.per_case()) == 10
    assert (example / ".promptgauge" / "promptgauge.db").is_file()


def test_evaluate_validates_paths_and_scorers(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="prompt: file not found"):
        promptgauge.evaluate(
            dataset=tmp_path, prompt=tmp_path / "nope.md", model="m", scorers=["contains"]
        )
    (tmp_path / "p.md").write_text("x")
    (tmp_path / "c.jsonl").write_text('{"input": "hi"}\n')
    with pytest.raises(ConfigError, match="at least one scorer"):
        promptgauge.evaluate(
            dataset=tmp_path / "c.jsonl", prompt=tmp_path / "p.md", model="m", scorers=[]
        )


def test_ablate_runs_the_example_from_code(example: Path, monkeypatch) -> None:
    provider = FakeProvider(default="ok")
    monkeypatch.setattr(main, "build_provider", lambda pricing, logger: provider)
    report = promptgauge.ablate(
        dataset=example / "cases.jsonl",
        prompt=example / "system.md",
        model="claude-sonnet-4-5",
        scorers=[scorers.contains()],
        repeats=1,
        budget_usd=2.0,
        name="from code",
    )
    assert isinstance(report, AblationReport)
    assert report.name == "from code" and report.stopped == "none"
    assert len(report.verdicts) >= 8 and report.confirmation is not None
    assert provider.calls and (example / ".promptgauge" / "promptgauge.db").is_file()


def test_ablate_refuses_over_budget_without_calling(example: Path, monkeypatch) -> None:
    provider = FakeProvider(default="ok")
    monkeypatch.setattr(main, "build_provider", lambda pricing, logger: provider)
    with pytest.raises(BudgetExceededError):
        promptgauge.ablate(
            dataset=example / "cases.jsonl",
            prompt=example / "system.md",
            model="claude-sonnet-4-5",
            scorers=["contains"],
            budget_usd=0.01,
        )
    assert provider.calls == []
