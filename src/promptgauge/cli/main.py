"""Composition root and Typer app: promptgauge eval | ablate | ui. Every object is built here and
injected through constructors.
"""

import asyncio
import os
import sys
from pathlib import Path

import anthropic
import typer
from rich.console import Console
from rich.progress import BarColumn, TextColumn
from rich.progress import Progress as ProgressBar

from promptgauge.cache.call_cache import CallCache
from promptgauge.cli.eval_table import EvalTable
from promptgauge.config.config import Config
from promptgauge.config.pricing import Pricing
from promptgauge.config.scorer_spec import ScorerSpec
from promptgauge.core.errors import ConfigError, PromptgaugeError
from promptgauge.core.logger import Logger
from promptgauge.dataset.dataset_loader import DatasetLoader
from promptgauge.db.call_repository import CallRepository
from promptgauge.db.case_repository import CaseRepository
from promptgauge.db.database import Database
from promptgauge.db.experiment_repository import ExperimentRepository
from promptgauge.db.migrator import Migrator
from promptgauge.db.result_repository import ResultRepository
from promptgauge.provider.anthropic_provider import AnthropicProvider
from promptgauge.provider.provider import Provider
from promptgauge.runner.eval_result import EvalResult
from promptgauge.runner.evaluator import Evaluator, ProgressCallback
from promptgauge.scorers import contains, exact, grounded, json_schema, rubric
from promptgauge.scorers.scorer import Scorer

DB_RELATIVE_PATH = Path(".promptgauge") / "promptgauge.db"

app = typer.Typer(
    help="Which lines of your system prompt actually do anything.",
    no_args_is_help=True,
)


def build_provider(pricing: Pricing, logger: Logger) -> Provider:
    """The one object that talks to the network; the key comes from ANTHROPIC_API_KEY only."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ConfigError("ANTHROPIC_API_KEY is not set; export it before running")
    client = anthropic.AsyncAnthropic(api_key=key, max_retries=3)
    return AnthropicProvider(client, pricing, logger)


def build_scorers(specs: list[ScorerSpec]) -> list[Scorer]:
    """Scorer objects from config entries."""
    built: list[Scorer] = []
    for spec in specs:
        if spec.name == "contains":
            built.append(contains())
        elif spec.name == "exact":
            built.append(exact())
        elif spec.name == "grounded":
            built.append(grounded())
        elif spec.name == "json_schema":
            built.append(json_schema(spec.arg or ""))
        else:
            built.append(rubric(spec.arg or ""))
    return built


def open_database(project_dir: Path) -> Database:
    """The project's SQLite file with every migration applied."""
    database = Database(project_dir / DB_RELATIVE_PATH)
    Migrator(database).apply()
    return database


def run_evaluation(
    config: Config,
    project_dir: Path,
    scorers: list[Scorer],
    *,
    name: str | None = None,
    logger: Logger | None = None,
    progress: ProgressCallback | None = None,
    provider: Provider | None = None,
) -> EvalResult:
    """Wire the evaluator for one run and execute it. Shared by the CLI and the SDK."""
    log = logger or Logger()
    pricing = Pricing()
    for model in (config.model, config.judge):
        pricing.require(model)
    # Fail on a missing key before touching the database, so a bad shell leaves no trace.
    live = provider or build_provider(pricing, log)
    database = open_database(project_dir)
    try:
        cache = CallCache(
            live,
            CallRepository(database),
            log,
            concurrency=config.concurrency,
        )
        evaluator = Evaluator(
            cache,
            ExperimentRepository(database),
            CaseRepository(database),
            ResultRepository(database),
            CallRepository(database),
            log,
            progress,
        )
        dataset = DatasetLoader().load(config.dataset)
        prompt_text = config.prompt.read_text(encoding="utf-8")
        return asyncio.run(
            evaluator.run(
                name=name or f"eval {config.prompt.name}",
                prompt_text=prompt_text,
                dataset=dataset,
                model=config.model,
                judge_model=config.judge,
                scorers=scorers,
                repeats=config.repeats,
                temperature=config.temperature,
                config_json=config.model_dump_json(),
            )
        )
    finally:
        database.close()


@app.command()
def eval(config: str = "promptgauge.yaml") -> None:
    """Run every case against the prompt, score it, store it, print a table."""
    console = Console()
    try:
        config_path = Path(config).resolve()
        settings = Config.load(config_path)
        scorers = build_scorers(settings.scorers)
        with ProgressBar(
            TextColumn("{task.completed}/{task.total} calls"),
            BarColumn(),
            TextColumn("${task.fields[spend]:.4f}"),
            console=console,
            transient=True,
        ) as bar:
            task = bar.add_task("eval", total=None, spend=0.0)

            def progress(done: int, total: int, spend: float) -> None:
                bar.update(task, completed=done, total=total, spend=spend)

            result = run_evaluation(settings, config_path.parent, scorers, progress=progress)
        EvalTable(console).render(result)
    except PromptgaugeError as exc:
        console.print(f"[red]error:[/] {exc}", highlight=False)
        sys.exit(1)
    if result.status != "done":
        sys.exit(1)


@app.command()
def ablate(config: str = "promptgauge.yaml", calls_per_month: int = 100_000) -> None:
    """Knock out blocks then lines, measure, paint the prompt, write the cut prompt."""
    raise NotImplementedError


@app.command()
def ui(port: int = 7331) -> None:
    """Serve the local dashboard and open the browser."""
    raise NotImplementedError
