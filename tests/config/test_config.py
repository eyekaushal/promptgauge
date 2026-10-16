from pathlib import Path

import pytest

from promptgauge.config.config import Config
from promptgauge.core.errors import ConfigError

BASE = "prompt: system.md\ndataset: cases.jsonl\nmodel: m\n"


def test_load_resolves_paths_and_applies_defaults(project: Path) -> None:
    config = Config.load(project / "promptgauge.yaml")
    assert config.prompt == (project / "system.md").resolve()
    assert config.dataset == (project / "cases.jsonl").resolve()
    assert config.model == "claude-sonnet-4-5"
    assert config.judge == "claude-haiku-4-5"
    assert [s.key for s in config.scorers] == ["contains", "rubric:helpful"]
    assert (config.repeats, config.temperature, config.budget_usd) == (3, 0.7, 2.0)
    assert (config.delta, config.concurrency) == (0.03, 8)


def test_load_resolves_json_schema_path(project: Path) -> None:
    (project / "promptgauge.yaml").write_text(BASE + "scorers:\n  - json_schema: schema.json\n")
    config = Config.load(project / "promptgauge.yaml")
    assert config.scorers[0].arg == str((project / "schema.json").resolve())


def test_load_accepts_a_string_path(project: Path) -> None:
    assert Config.load(str(project / "promptgauge.yaml")).repeats == 3


def test_missing_config_file() -> None:
    with pytest.raises(ConfigError, match="config file not found"):
        Config.load("/nowhere/promptgauge.yaml")


@pytest.mark.parametrize(
    ("yaml_text", "message"),
    [
        (
            BASE + "scorers: [contains]\nrepeats: 0\n",
            "repeats:",
        ),
        (BASE + "scorers: [bleu]\n", "scorers"),
        (BASE + "scorers: []\n", "scorers:"),
        (
            "prompt: system.md\ndataset: missing.jsonl\nmodel: m\nscorers: [contains]\n",
            "dataset: file not found",
        ),
        (
            "prompt: nope.md\ndataset: cases.jsonl\nmodel: m\nscorers: [contains]\n",
            "prompt: file not found",
        ),
        (
            BASE + "scorers: [contains]\nbudget_usd: 0\n",
            "budget_usd:",
        ),
        (
            BASE + "scorers: [contains]\ntemperature: 2\n",
            "temperature:",
        ),
        (
            BASE + "scorers: [contains]\nmodle: x\n",
            "modle:",
        ),
        ("dataset: cases.jsonl\nmodel: m\nscorers: [contains]\n", "prompt:"),
        (
            BASE + "scorers:\n  - json_schema: no.json\n",
            "json_schema file not found",
        ),
        ("- just\n- a list\n", "must be a mapping"),
        ("prompt: [unclosed\n", "not valid YAML"),
    ],
)
def test_bad_config_names_the_problem(project: Path, yaml_text: str, message: str) -> None:
    (project / "promptgauge.yaml").write_text(yaml_text)
    with pytest.raises(ConfigError, match=message):
        Config.load(project / "promptgauge.yaml")


def test_config_is_frozen(project: Path) -> None:
    config = Config.load(project / "promptgauge.yaml")
    with pytest.raises(Exception):  # noqa: B017 - pydantic raises its own ValidationError
        config.repeats = 5  # type: ignore[misc]
