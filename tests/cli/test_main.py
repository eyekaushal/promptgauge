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
