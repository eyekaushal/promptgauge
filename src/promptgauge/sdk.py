"""Public functions evaluate() and ablate().

Both build the same composition root as the CLI (cli/main.py) and call it. PRD §7.4.
ablate() is filled at B11.
"""

from pathlib import Path

from promptgauge.ablate.ablation_report import AblationReport
from promptgauge.config.config import Config
from promptgauge.config.scorer_spec import ScorerSpec
from promptgauge.core.errors import ConfigError
from promptgauge.runner.eval_result import EvalResult
from promptgauge.scorers.scorer import Scorer


def evaluate(
    *,
    dataset: str | Path,
    prompt: str | Path,
    model: str,
    scorers: list[Scorer | str | dict[str, str]],
    repeats: int = 3,
    judge: str = "claude-haiku-4-5",
    temperature: float = 0.7,
    concurrency: int = 8,
    name: str | None = None,
) -> EvalResult:
    """Run every case against the prompt and return an EvalResult.

    Takes the same fields as promptgauge.yaml (PRD F1.5). `scorers` may mix scorer objects from
    `promptgauge.scorers` with config-style entries like `"contains"` or `{"rubric": "helpful"}`.
    Results are stored in `.promptgauge/promptgauge.db` next to the prompt file.
    """
    from promptgauge.cli.main import run_evaluation

    config, built = _config_and_scorers(
        dataset=dataset,
        prompt=prompt,
        model=model,
        scorers=scorers,
        repeats=repeats,
        judge=judge,
        temperature=temperature,
        concurrency=concurrency,
    )
    return run_evaluation(config, config.prompt.parent, built, name=name)


def ablate(
    *,
    dataset: str | Path,
    prompt: str | Path,
    model: str,
    scorers: list[Scorer | str | dict[str, str]],
    repeats: int = 3,
    judge: str = "claude-haiku-4-5",
    temperature: float = 0.7,
    budget_usd: float = 2.0,
    delta: float = 0.03,
    concurrency: int = 8,
    name: str | None = None,
) -> AblationReport:
    """Delete every segment of the prompt in turn, measure, and return an AblationReport with the
    verdicts, the cut prompt and its confirmation run (PRD §7.4).

    Same fields as promptgauge.yaml plus `budget_usd` and `delta`. Raises BudgetExceededError
    before any call when the estimate is over budget.
    """
    from promptgauge.cli.main import run_ablation

    config, built = _config_and_scorers(
        dataset=dataset,
        prompt=prompt,
        model=model,
        scorers=scorers,
        repeats=repeats,
        judge=judge,
        temperature=temperature,
        concurrency=concurrency,
        budget_usd=budget_usd,
        delta=delta,
    )
    return run_ablation(config, config.prompt.parent, built, name=name)


def _config_and_scorers(
    *,
    dataset: str | Path,
    prompt: str | Path,
    model: str,
    scorers: list[Scorer | str | dict[str, str]],
    **fields: object,
) -> tuple[Config, list[Scorer]]:
    from promptgauge.cli.main import build_scorers

    prompt_path = Path(prompt).resolve()
    dataset_path = Path(dataset).resolve()
    for label, path in (("prompt", prompt_path), ("dataset", dataset_path)):
        if not path.is_file():
            raise ConfigError(f"{label}: file not found: {path}")

    objects = [s for s in scorers if isinstance(s, Scorer)]
    specs = [ScorerSpec.parse(s) for s in scorers if not isinstance(s, Scorer)]
    config = Config(
        prompt=prompt_path,
        dataset=dataset_path,
        model=model,
        scorers=specs or [ScorerSpec(name="contains")],
        **fields,  # type: ignore[arg-type]
    )
    built = objects + build_scorers(specs)
    if not built:
        raise ConfigError("scorers: at least one scorer is required")
    return config, built
