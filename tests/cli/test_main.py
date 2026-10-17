import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from promptgauge.cli import main
from promptgauge.config.config import Config
from promptgauge.config.scorer_spec import ScorerSpec
from promptgauge.core.errors import ConfigError
from promptgauge.provider.fake_provider import FakeProvider
from promptgauge.scorers import contains
from promptgauge.scorers.contains_scorer import ContainsScorer
from promptgauge.scorers.exact_scorer import ExactScorer
from promptgauge.scorers.grounded_scorer import GroundedScorer
from promptgauge.scorers.json_schema_scorer import JsonSchemaScorer
from promptgauge.scorers.rubric_scorer import RubricScorer

EXAMPLE = Path(__file__).parents[2] / "examples" / "support-bot"
JUDGE_OK = '{"score": 0.9, "reason": "fine"}'
FREE_PRICING = main.Pricing({m: (0.0, 0.0) for m in main.Pricing().models()})


@pytest.fixture
def example(tmp_path: Path) -> Path:
    """A copy of examples/support-bot so the test never writes a database into the repo."""
    target = tmp_path / "support-bot"
    shutil.copytree(EXAMPLE, target)
    return target


def test_build_scorers_covers_every_kind(tmp_path: Path) -> None:
    schema = tmp_path / "s.json"
    schema.write_text('{"type": "object"}')
    specs = [
        ScorerSpec(name="contains"),
        ScorerSpec(name="exact"),
        ScorerSpec(name="grounded"),
        ScorerSpec(name="json_schema", arg=str(schema)),
        ScorerSpec(name="rubric", arg="concise"),
    ]
    kinds = [type(s) for s in main.build_scorers(specs)]
    assert kinds == [ContainsScorer, ExactScorer, GroundedScorer, JsonSchemaScorer, RubricScorer]


def test_build_provider_requires_the_env_key(monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY"):
        main.build_provider(main.Pricing(), main.Logger("test"))


def test_run_evaluation_on_the_example_with_a_fake_provider(example: Path) -> None:
    config = Config.load(example / "promptgauge.yaml")
    provider = FakeProvider(
        {"How do I list my restaurant on Swiggle?": "See the website."}, default=JUDGE_OK
    )
    result = main.run_evaluation(
        config, example, main.build_scorers(config.scorers), provider=provider
    )

    assert result.status == "done"
    assert len(result.per_case()) == 10 and result.repeats == 3
    assert result.scorer_keys == ["contains", "rubric:helpful"]
    assert (example / ".promptgauge" / "promptgauge.db").is_file()

    again = main.run_evaluation(
        config, example, main.build_scorers(config.scorers), provider=provider
    )
    assert (again.cached_share, again.cost_usd) == (1.0, 0.0)


def test_eval_command_prints_table_and_exits_zero(example: Path, monkeypatch) -> None:
    provider = FakeProvider(default=JUDGE_OK)
    monkeypatch.setattr(main, "build_provider", lambda pricing, logger: provider)
    runner = CliRunner(env={"COLUMNS": "160"})
    result = runner.invoke(main.app, ["eval", "--config", str(example / "promptgauge.yaml")])
    assert result.exit_code == 0, result.output
    assert "cases 10 · repeats 3" in result.output
    assert "rubric:helpful" in result.output


def test_eval_command_exits_one_on_partial_run(example: Path, monkeypatch) -> None:
    provider = FakeProvider(default=JUDGE_OK, errors={"Is Swiggle better than Zomato?": "boom"})
    monkeypatch.setattr(main, "build_provider", lambda pricing, logger: provider)
    result = CliRunner().invoke(main.app, ["eval", "--config", str(example / "promptgauge.yaml")])
    assert result.exit_code == 1
    assert "partial" in result.output and "boom" in result.output


def test_eval_command_reports_config_errors_in_one_line(tmp_path: Path) -> None:
    result = CliRunner().invoke(main.app, ["eval", "--config", str(tmp_path / "missing.yaml")])
    assert result.exit_code == 1
    assert "error: config file not found" in result.output


def test_eval_command_without_api_key(example: Path, monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = CliRunner().invoke(main.app, ["eval", "--config", str(example / "promptgauge.yaml")])
    assert result.exit_code == 1
    assert "ANTHROPIC_API_KEY" in result.output


def test_config_resolves_custom_rubric_file_next_to_it(tmp_path: Path) -> None:
    (tmp_path / "system.md").write_text("x")
    (tmp_path / "cases.jsonl").write_text('{"input": "hi"}\n')
    (tmp_path / "voice.md").write_text("Score the brand voice.")
    (tmp_path / "promptgauge.yaml").write_text(
        "prompt: system.md\ndataset: cases.jsonl\nmodel: m\n"
        "scorers:\n  - rubric: voice.md\n  - rubric: helpful\n"
    )
    config = Config.load(tmp_path / "promptgauge.yaml")
    assert config.scorers[0].arg == str(tmp_path / "voice.md")
    assert config.scorers[1].arg == "helpful"
    built = main.build_scorers(config.scorers)
    assert [s.key for s in built] == ["rubric:voice", "rubric:helpful"]
    assert isinstance(contains(), ContainsScorer)


def _raise_budget(example: Path, budget: float) -> None:
    config = example / "promptgauge.yaml"
    config.write_text(config.read_text().replace("budget_usd: 1.00", f"budget_usd: {budget}"))


def test_ablate_command_paints_and_writes_the_cut_prompt(example: Path, monkeypatch) -> None:
    provider = FakeProvider(default=JUDGE_OK)
    monkeypatch.setattr(main, "build_provider", lambda pricing, logger: provider)
    _raise_budget(example, 20.0)
    result = CliRunner().invoke(
        main.app,
        ["ablate", "--config", str(example / "promptgauge.yaml"), "--calls-per-month", "1000"],
    )
    assert result.exit_code == 0, result.output
    assert "no measurable effect at this sample size" in result.output
    assert "a month at 1,000 calls" in result.output
    cut = example / "system.cut.md"
    assert cut.is_file() and "cut prompt written to" in result.output
    assert provider.calls


def test_ablate_command_exits_2_over_budget_without_calling(example: Path, monkeypatch) -> None:
    provider = FakeProvider(default=JUDGE_OK)
    monkeypatch.setattr(main, "build_provider", lambda pricing, logger: provider)
    _raise_budget(example, 0.05)
    result = CliRunner().invoke(main.app, ["ablate", "--config", str(example / "promptgauge.yaml")])
    assert result.exit_code == 2, result.output
    assert "exceeds budget $0.05" in result.output and "nothing was called" in result.output
    assert result.output.count("  - ") == 3
    assert provider.calls == [] and not (example / "system.cut.md").exists()


def test_ablate_command_exits_1_on_a_stopped_run(example: Path, monkeypatch) -> None:
    # The estimate passes on the fake's free table, then real prices cross the budget mid-run.
    provider = FakeProvider(default=JUDGE_OK)
    monkeypatch.setattr(main, "build_provider", lambda pricing, logger: provider)
    real_planner = main.BudgetPlanner
    monkeypatch.setattr(
        main, "BudgetPlanner", lambda pricing, budget: real_planner(FREE_PRICING, budget)
    )
    _raise_budget(example, 0.01)
    result = CliRunner().invoke(main.app, ["ablate", "--config", str(example / "promptgauge.yaml")])
    assert result.exit_code == 1, result.output
    assert "Stopped at the budget" in result.output
    assert "cut prompt not written" in result.output and not (example / "system.cut.md").exists()


def test_build_app_reads_the_project_database(example: Path) -> None:
    from fastapi.testclient import TestClient

    config = Config.load(example / "promptgauge.yaml")
    app = main.build_app(example, config, 7331)
    with TestClient(app, base_url="http://127.0.0.1:7331") as client:
        health = client.get("/api/health").json()
        assert health["status"] == "ok"
        assert health["database"].endswith("promptgauge.db")
        assert client.get("/api/experiments").json() == []
        assert client.get("/api/settings").json()["config"]["model"] == config.model
    assert (example / ".promptgauge" / "promptgauge.db").is_file()


def test_ui_serves_on_loopback_and_opens_the_browser(example: Path, monkeypatch) -> None:
    served: dict = {}
    opened: list[str] = []
    monkeypatch.setattr(main.uvicorn, "run", lambda app, **kw: served.update(kw))
    monkeypatch.setattr(main.webbrowser, "open", lambda url: opened.append(url))
    monkeypatch.setattr(main.threading, "Timer", lambda delay, fn, args=(): _Now(fn, args))

    result = CliRunner().invoke(main.app, ["ui", "--config", str(example / "promptgauge.yaml")])
    assert result.exit_code == 0, result.output
    assert served == {"host": "127.0.0.1", "port": 7331, "log_level": "warning"}
    assert opened == ["http://127.0.0.1:7331"]


def test_ui_without_a_config_still_serves_and_skips_the_browser(
    tmp_path: Path, monkeypatch
) -> None:
    served: dict = {}
    monkeypatch.setattr(main.uvicorn, "run", lambda app, **kw: served.update(kw))
    monkeypatch.setattr(main.webbrowser, "open", lambda url: pytest.fail("browser opened"))
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(main.app, ["ui", "--port", "7444", "--no-open-browser"])
    assert result.exit_code == 0, result.output
    assert served["port"] == 7444
    assert (tmp_path / ".promptgauge" / "promptgauge.db").is_file()


def test_ui_reports_a_broken_config(tmp_path: Path) -> None:
    (tmp_path / "promptgauge.yaml").write_text("prompt: [\n")
    result = CliRunner().invoke(main.app, ["ui", "--config", str(tmp_path / "promptgauge.yaml")])
    assert result.exit_code == 1
    assert "error:" in result.output


class _Now:
    """Stands in for threading.Timer: runs the callback on start(), no thread."""

    def __init__(self, fn, args) -> None:
        self._fn, self._args = fn, args

    def start(self) -> None:
        self._fn(*self._args)
