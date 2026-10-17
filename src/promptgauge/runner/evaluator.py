"""Evaluator: run every (case, repeat) through the cache with a semaphore, score, store experiment
and result rows. PRD F4.1–F4.4.
"""

import asyncio
import hashlib
import time
from collections.abc import Callable

from promptgauge.cache.call_cache import CallCache
from promptgauge.core.errors import ProviderError, ScorerError
from promptgauge.core.logger import Logger
from promptgauge.dataset.case import Case
from promptgauge.dataset.dataset_loader import Dataset
from promptgauge.db.call_repository import CallRepository
from promptgauge.db.case_repository import CaseRepository
from promptgauge.db.experiment_repository import ExperimentRepository
from promptgauge.db.result_repository import ResultRepository
from promptgauge.runner.case_run import CaseRun
from promptgauge.runner.eval_result import EvalResult
from promptgauge.scorers.judge import Judge
from promptgauge.scorers.scorer import Scorer

# Target replies are short support answers (PRD §14).
MAX_TOKENS = 1024

ProgressCallback = Callable[[int, int, float], None]


class Evaluator:
    """Runs one evaluation experiment end to end. Concurrency is enforced by CallCache's
    semaphore; this class fans out one task per (case, repeat) and gathers them."""

    def __init__(
        self,
        cache: CallCache,
        experiments: ExperimentRepository,
        cases: CaseRepository,
        results: ResultRepository,
        calls: CallRepository,
        logger: Logger,
        progress: ProgressCallback | None = None,
    ) -> None:
        self._cache = cache
        self._experiments = experiments
        self._cases = cases
        self._results = results
        self._calls = calls
        self._log = logger
        self._progress = progress

    def start(
        self,
        *,
        kind: str,
        name: str,
        prompt_text: str,
        dataset: Dataset,
        model: str,
        judge_model: str,
        scorers: list[Scorer],
        config_json: str,
    ) -> tuple[int, list[int]]:
        """Create the experiment row, store the cases and bind the judge. Returns the experiment
        id and the case ids in dataset order. Shared by eval runs and ablations."""
        experiment_id = self._experiments.create(
            kind=kind,
            name=name,
            prompt_hash=hashlib.sha256(prompt_text.encode("utf-8")).hexdigest(),
            prompt_text=prompt_text,
            dataset_hash=dataset.hash,
            model=model,
            judge=judge_model,
            config_json=config_json,
        )
        case_ids = self._cases.upsert_many(dataset.hash, [c.to_row() for c in dataset.cases])
        judge = Judge(self._cache, judge_model, experiment_id, self._log)
        for scorer in scorers:
            scorer.bind(judge)
        return experiment_id, case_ids

    async def measure(
        self,
        experiment_id: int,
        *,
        prompt_text: str,
        dataset: Dataset,
        case_ids: list[int],
        model: str,
        temperature: float,
        scorers: list[Scorer],
        repeats: int,
        variant_id: int | None = None,
        store: bool = True,
        progress: ProgressCallback | None = None,
    ) -> list[CaseRun]:
        """Run and score every (case, repeat) for one prompt text. `variant_id` labels the result
        rows (None = baseline); `store=False` measures without writing them (the confirmation
        run). A failed call marks that run failed; the rest continue."""
        total = len(dataset.cases) * repeats
        done = 0

        async def run_one(case: Case, case_id: int, repeat_index: int) -> CaseRun:
            nonlocal done
            run = await self._run_one(
                case, case_id, repeat_index, prompt_text, model, temperature, scorers, experiment_id
            )
            done += 1
            if progress is not None:
                progress(done, total, self._calls.totals(experiment_id)["cost_usd"])
            return run

        runs = await asyncio.gather(
            *(
                run_one(case, case_id, repeat_index)
                for case, case_id in zip(dataset.cases, case_ids, strict=True)
                for repeat_index in range(repeats)
            )
        )
        runs.sort(key=lambda r: (r.case.index, r.repeat_index))
        if store:
            self._store_results(experiment_id, runs, variant_id)
        return runs

    async def run(
        self,
        *,
        name: str,
        prompt_text: str,
        dataset: Dataset,
        model: str,
        judge_model: str,
        scorers: list[Scorer],
        repeats: int,
        temperature: float,
        config_json: str,
    ) -> EvalResult:
        """Write the experiment, run and score every (case, repeat), write results, return totals.

        A failed call marks that run failed and the experiment `partial`; the rest continue.
        """
        started = time.monotonic()
        experiment_id, case_ids = self.start(
            kind="eval",
            name=name,
            prompt_text=prompt_text,
            dataset=dataset,
            model=model,
            judge_model=judge_model,
            scorers=scorers,
            config_json=config_json,
        )
        runs = await self.measure(
            experiment_id,
            prompt_text=prompt_text,
            dataset=dataset,
            case_ids=case_ids,
            model=model,
            temperature=temperature,
            scorers=scorers,
            repeats=repeats,
            progress=self._progress,
        )
        status = "partial" if any(r.failed for r in runs) else "done"
        self._experiments.finish(experiment_id, status)
        totals = self._calls.totals(experiment_id)
        return EvalResult(
            experiment_id=experiment_id,
            name=name,
            status=status,
            model=model,
            scorer_keys=[s.key for s in scorers],
            runs=runs,
            calls=totals["calls"],
            cached=totals["cached"],
            cost_usd=totals["cost_usd"],
            duration_s=time.monotonic() - started,
        )

    async def _run_one(
        self,
        case: Case,
        case_id: int,
        repeat_index: int,
        prompt_text: str,
        model: str,
        temperature: float,
        scorers: list[Scorer],
        experiment_id: int,
    ) -> CaseRun:
        try:
            completion = await self._cache.complete(
                system=prompt_text,
                user=case.input,
                model=model,
                temperature=temperature,
                max_tokens=MAX_TOKENS,
                repeat_index=repeat_index,
                experiment_id=experiment_id,
            )
            scores = {
                scorer.key: await scorer.score(case, completion.text)
                for scorer in scorers
                if scorer.applies_to(case)
            }
        except (ProviderError, ScorerError) as exc:
            self._log.warning("case failed", case=case.index, repeat=repeat_index, error=str(exc))
            return CaseRun(case=case, case_id=case_id, repeat_index=repeat_index, error=str(exc))
        return CaseRun(
            case=case,
            case_id=case_id,
            repeat_index=repeat_index,
            output=completion.text,
            call_hash=completion.call_hash,
            cached=completion.cached,
            scores=scores,
        )

    def _store_results(
        self, experiment_id: int, runs: list[CaseRun], variant_id: int | None
    ) -> None:
        rows = [
            {
                "case_id": run.case_id,
                "repeat_index": run.repeat_index,
                "variant_id": variant_id,
                "scorer": key,
                "score": result.score,
                "reason": result.reason,
                "call_hash": run.call_hash,
            }
            for run in runs
            if not run.failed
            for key, result in run.scores.items()
        ]
        if rows:
            self._results.insert_many(experiment_id, rows)
