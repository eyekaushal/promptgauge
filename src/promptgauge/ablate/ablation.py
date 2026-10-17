"""Ablation: baseline → stage one → stage two → cut → confirmation; writes segment, verdict and
ablation rows. PRD F6.3, F6.7.
"""

import time
from statistics import fmean

from promptgauge.ablate.ablation_planner import AblationPlanner
from promptgauge.ablate.ablation_report import AblationReport, Stopped
from promptgauge.ablate.budget_planner import BudgetPlanner
from promptgauge.ablate.prompt_cutter import PromptCutter
from promptgauge.ablate.segment_verdict import SegmentVerdict
from promptgauge.ablate.stage_plan import StagePlan
from promptgauge.core.errors import AblationError, BudgetExceededError
from promptgauge.core.logger import Logger
from promptgauge.dataset.dataset_loader import Dataset
from promptgauge.db.call_repository import CallRepository
from promptgauge.db.experiment_repository import ExperimentRepository
from promptgauge.db.segment_repository import SegmentRepository
from promptgauge.db.verdict_repository import VerdictRepository
from promptgauge.prompt.prompt_segmenter import PromptSegmenter
from promptgauge.prompt.segment import Segment
from promptgauge.prompt.variant_builder import VariantBuilder
from promptgauge.runner.case_run import CaseRun
from promptgauge.runner.evaluator import Evaluator, ProgressCallback
from promptgauge.scorers.scorer import Scorer
from promptgauge.stats.bootstrap import Bootstrap
from promptgauge.stats.mean_interval import MeanInterval
from promptgauge.stats.verdict_rule import VerdictRule

CaseMeans = dict[int, float]


class Ablation:
    """Measure what every segment of a prompt does, by deleting it (invariant 2), and build the
    shorter prompt with its confirmation run (invariant 5). Money is checked before the first call
    and between variants (invariant 3)."""

    def __init__(
        self,
        evaluator: Evaluator,
        segmenter: PromptSegmenter,
        planner: AblationPlanner,
        budget: BudgetPlanner,
        bootstrap: Bootstrap,
        rule: VerdictRule,
        cutter: PromptCutter,
        experiments: ExperimentRepository,
        segments: SegmentRepository,
        verdicts: VerdictRepository,
        calls: CallRepository,
        logger: Logger,
        progress: ProgressCallback | None = None,
    ) -> None:
        self._evaluator = evaluator
        self._segmenter = segmenter
        self._planner = planner
        self._budget = budget
        self._bootstrap = bootstrap
        self._rule = rule
        self._cutter = cutter
        self._experiments = experiments
        self._segments = segments
        self._verdicts = verdicts
        self._calls = calls
        self._log = logger
        self._progress = progress

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
    ) -> AblationReport:
        """Plan, price, refuse if over budget (before any call or row), then measure and write.

        Raises BudgetExceededError from the estimate. A budget crossed mid-run or a variant with
        no measurable case ends the run early; what was measured is written and `stopped` says why.
        """
        started = time.monotonic()
        stage_one = self._planner.stage_one(prompt_text)
        estimate = self._budget.estimate(
            model=model,
            judge=judge_model,
            judge_scorers=sum(1 for s in scorers if s.uses_judge),
            prompt_tokens=self._segmenter.tokens(prompt_text),
            cases=dataset.cases,
            repeats=repeats,
            stage_one_variants=stage_one.variants,
            stage_two_candidates=self._planner.stage_two_candidates(prompt_text),
        )
        self._budget.require_within_budget(estimate)
        self._log.info("ablation planned", estimate=estimate.summary())

        experiment_id, case_ids = self._evaluator.start(
            kind="ablation",
            name=name,
            prompt_text=prompt_text,
            dataset=dataset,
            model=model,
            judge_model=judge_model,
            scorers=scorers,
            config_json=config_json,
        )
        measure_args = dict(
            dataset=dataset,
            case_ids=case_ids,
            model=model,
            temperature=temperature,
            scorers=scorers,
            repeats=repeats,
        )
        # Planned calls drive the progress line; stage two is unknown until stage one is in, so
        # the total grows as the plan does.
        self._planned = stage_one.calls + len(dataset.cases) * repeats
        self._done = 0
        segment_ids: dict[Segment, int] = {}
        verdicts: list[SegmentVerdict] = []
        stopped: Stopped = "none"
        builder = VariantBuilder(prompt_text)
        baseline: CaseMeans = {}
        cut_prompt = prompt_text
        cut_means: CaseMeans | None = None
        try:
            baseline_runs = await self._measure(experiment_id, prompt_text, None, **measure_args)
            baseline = self._case_means(baseline_runs)
            if not baseline:
                raise AblationError("baseline: every case failed")
            for segment in stage_one.segments:
                segment_ids[segment] = self._insert_segment(experiment_id, segment, None)
            await self._run_stage(
                experiment_id, stage_one, builder, baseline, segment_ids, verdicts, measure_args
            )
            red_blocks = [v.segment for v in verdicts if v.verdict == "red"]
            stage_two = self._planner.stage_two(red_blocks)
            self._planned += stage_two.calls
            block_ids = {s.index: i for s, i in segment_ids.items() if s.level == "block"}
            for line in stage_two.segments:
                parent_id = block_ids[line.parent_index or 0]
                segment_ids[line] = self._insert_segment(experiment_id, line, parent_id)
            await self._run_stage(
                experiment_id, stage_two, builder, baseline, segment_ids, verdicts, measure_args
            )
            cut_prompt = self._cutter.cut(prompt_text, verdicts)
            self._check_budget(experiment_id)
            cut_runs = await self._measure(
                experiment_id, cut_prompt, None, store=False, **measure_args
            )
            cut_means = self._case_means(cut_runs)
            if not cut_means:
                raise AblationError("confirmation: every case failed")
        except (BudgetExceededError, AblationError) as exc:
            # Stop, keep what was measured, and say why (F6.2, F6.8). The cut prompt built from
            # partial verdicts is a suggestion only: it has no confirmation run (invariant 5).
            stopped = "budget" if isinstance(exc, BudgetExceededError) else "error"
            self._log.warning("ablation stopped", reason=stopped, detail=str(exc))
            if baseline:
                cut_prompt = self._cutter.cut(prompt_text, verdicts)

        baseline_score = fmean(baseline.values()) if baseline else 0.0
        confirmation = self._interval(baseline, cut_means) if cut_means else None
        cut_score = fmean(cut_means.values()) if cut_means else None
        confirmed = (
            confirmation is not None
            and cut_score is not None
            and cut_score >= baseline_score - self._rule.delta
        )
        tokens_before = self._segmenter.tokens(prompt_text)
        tokens_after = self._segmenter.tokens(cut_prompt)
        if baseline:
            self._experiments.save_ablation(
                experiment_id,
                baseline_score=baseline_score,
                cut_score=cut_score,
                cut_ci_low=confirmation.ci_low if confirmation else None,
                cut_ci_high=confirmation.ci_high if confirmation else None,
                cut_prompt=cut_prompt,
                tokens_before=tokens_before,
                tokens_after=tokens_after,
                confirmed=confirmed,
            )
        status = "done" if stopped == "none" else "stopped"
        self._experiments.finish(experiment_id, status, None if stopped == "none" else stopped)
        totals = self._calls.totals(experiment_id)
        return AblationReport(
            experiment_id=experiment_id,
            name=name,
            model=model,
            delta=self._rule.delta,
            prompt_text=prompt_text,
            verdicts=verdicts,
            baseline_score=baseline_score,
            cut_prompt=cut_prompt,
            cut_score=cut_score,
            confirmation=confirmation,
            confirmed=confirmed,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            calls=totals["calls"],
            cached=totals["cached"],
            cost_usd=totals["cost_usd"],
            duration_s=time.monotonic() - started,
            stopped=stopped,
        )

    async def _run_stage(
        self,
        experiment_id: int,
        plan: StagePlan,
        builder: VariantBuilder,
        baseline: CaseMeans,
        segment_ids: dict[Segment, int],
        verdicts: list[SegmentVerdict],
        measure_args: dict[str, object],
    ) -> None:
        for segment in plan.segments:
            self._check_budget(experiment_id)
            variant_id = segment_ids[segment]
            runs = await self._measure(
                experiment_id, builder.without(segment), variant_id, **measure_args
            )
            interval = self._interval(baseline, self._case_means(runs))
            if interval is None:
                raise AblationError(f"{segment.level} {segment.index}: every case failed")
            colour = self._rule.verdict(interval.ci_low, interval.ci_high)
            verdicts.append(SegmentVerdict(segment, plan.stage, interval, colour))
            self._verdicts.upsert(
                experiment_id,
                variant_id,
                mean_delta=interval.mean,
                ci_low=interval.ci_low,
                ci_high=interval.ci_high,
                n_cases=interval.n_cases,
                verdict=colour,
                stage=plan.stage,
            )

    async def _measure(
        self,
        experiment_id: int,
        prompt_text: str,
        variant_id: int | None,
        *,
        store: bool = True,
        **measure_args: object,
    ) -> list[CaseRun]:
        offset = self._done

        def progress(done: int, total: int, spend: float) -> None:
            self._done = offset + done
            if self._progress is not None:
                self._progress(self._done, self._planned, spend)

        runs = await self._evaluator.measure(
            experiment_id,
            prompt_text=prompt_text,
            variant_id=variant_id,
            store=store,
            progress=progress,
            **measure_args,  # type: ignore[arg-type]
        )
        self._done = offset + len(runs)
        return runs

    def _check_budget(self, experiment_id: int) -> None:
        spend = self._calls.totals(experiment_id)["cost_usd"]
        if self._budget.exceeded(spend):
            raise BudgetExceededError(
                f"spend ${spend:.2f} crossed budget ${self._budget.budget_usd:.2f}"
            )

    def _insert_segment(self, experiment_id: int, segment: Segment, parent_id: int | None) -> int:
        return self._segments.insert(
            experiment_id,
            parent_segment_id=parent_id,
            level=segment.level,
            index=segment.index,
            start_offset=segment.start,
            end_offset=segment.end,
            text=segment.text,
            tokens=segment.tokens,
        )

    def _interval(self, baseline: CaseMeans, variant: CaseMeans) -> MeanInterval | None:
        # F6.3: per case, mean over repeats of the variant minus the same for the baseline. Cases
        # that failed on either side are left out; none left means nothing was measured.
        diffs = [variant[i] - baseline[i] for i in variant if i in baseline]
        return self._bootstrap.mean_ci(diffs) if diffs else None

    @staticmethod
    def _case_means(runs: list[CaseRun]) -> CaseMeans:
        scores: dict[int, list[float]] = {}
        for run in runs:
            if run.score is not None:
                scores.setdefault(run.case.index, []).append(run.score)
        return {index: fmean(values) for index, values in scores.items()}
