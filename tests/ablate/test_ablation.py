from statistics import fmean

import pytest

from promptgauge.ablate.ablation import Ablation
from promptgauge.ablate.ablation_planner import AblationPlanner
from promptgauge.ablate.budget_planner import BudgetPlanner
from promptgauge.ablate.prompt_cutter import PromptCutter
from promptgauge.cache.call_cache import CallCache
from promptgauge.config.pricing import Pricing
from promptgauge.core.errors import BudgetExceededError
from promptgauge.core.logger import Logger
from promptgauge.dataset.case import Case
from promptgauge.dataset.dataset_loader import Dataset, DatasetLoader
from promptgauge.db.call_repository import CallRepository
from promptgauge.db.case_repository import CaseRepository
from promptgauge.db.database import Database
from promptgauge.db.experiment_repository import ExperimentRepository
from promptgauge.db.result_repository import ResultRepository
from promptgauge.db.segment_repository import SegmentRepository
from promptgauge.db.verdict_repository import VerdictRepository
from promptgauge.prompt.prompt_segmenter import PromptSegmenter
from promptgauge.prompt.variant_builder import VariantBuilder
from promptgauge.provider.fake_provider import FakeProvider
from promptgauge.runner.evaluator import Evaluator
from promptgauge.scorers.score_result import ScoreResult
from promptgauge.scorers.scorer import Scorer
from promptgauge.stats.bootstrap import Bootstrap
from promptgauge.stats.verdict_rule import VerdictRule

MODEL = "claude-sonnet-4-5"
JUDGE = "claude-haiku-4-5"
N_CASES = 6
REPEATS = 2

# Three single-line blocks: A matters (-0.2 when removed), B does nothing, C hurts (+0.1).
THREE = "Always answer in French.\n\nBe polite.\n\nUse emoji.\n"
SHIFTS_THREE = {"Always answer in French.": -0.2, "Be polite.": 0.0, "Use emoji.": 0.1}

# A red block with three lines, of which only one matters, plus a grey block.
RULES = "# Rules\n- Always answer in French.\n- Mention the weather.\n\nBe polite.\n"
SHIFTS_RULES = {"- Always answer in French.": -0.3}


class ScoreFromOutput(Scorer):
    """Test scorer: the model's reply is the score."""

    @property
    def key(self) -> str:
        return "score"

    async def score(self, case: Case, output: str) -> ScoreResult:
        return ScoreResult(score=float(output), reason=None)


def baseline_score(case_index: int) -> float:
    return 0.5 + 0.05 * case_index


def scripted(text: str, shifts: dict[str, float]) -> dict[tuple[str, str], str]:
    """Replies for every prompt the ablation can send: baseline, each block or line variant and
    every prompt built from a subset of blocks. The reply depends only on which lines are gone."""
    segmenter = PromptSegmenter()
    builder = VariantBuilder(text)
    prompts = {text}
    blocks = segmenter.blocks(text)
    for block in blocks:
        prompts.add(builder.without(block))
        for line in segmenter.lines(block):
            prompts.add(builder.without(line))
    # Cut prompts: any subset of lines kept, in order, joined as the cutter would. Enumerating the
    # few shapes the tests need is enough.
    for kept in ("Always answer in French.\n", "- Always answer in French.\n", ""):
        prompts.add(kept)
    outputs: dict[tuple[str, str], str] = {}
    for system in prompts:
        shift = sum(delta for needle, delta in shifts.items() if needle not in system)
        for i in range(N_CASES):
            outputs[(system, f"q{i}")] = f"{baseline_score(i) + shift:.4f}"
    return outputs


def make_dataset() -> Dataset:
    cases = [Case(index=i, input=f"q{i}") for i in range(N_CASES)]
    return Dataset(path=None, hash=DatasetLoader.hash_cases(cases), cases=cases)  # type: ignore[arg-type]


def make_ablation(
    db: Database,
    provider: FakeProvider,
    *,
    budget_usd: float = 100.0,
    budget_pricing: Pricing | None = None,
    delta: float = 0.03,
    progress=None,
) -> Ablation:
    log = Logger("test")
    cache = CallCache(provider, CallRepository(db), log)
    evaluator = Evaluator(
        cache,
        ExperimentRepository(db),
        CaseRepository(db),
        ResultRepository(db),
        CallRepository(db),
        log,
    )
    segmenter = PromptSegmenter()
    return Ablation(
        evaluator,
        segmenter,
        AblationPlanner(segmenter, N_CASES, REPEATS),
        BudgetPlanner(budget_pricing or Pricing(), budget_usd),
        Bootstrap(),
        VerdictRule(delta),
        PromptCutter(),
        ExperimentRepository(db),
        SegmentRepository(db),
        VerdictRepository(db),
        CallRepository(db),
        log,
        progress,
    )


async def run(ablation: Ablation, text: str):
    return await ablation.run(
        name="synthetic",
        prompt_text=text,
        dataset=make_dataset(),
        model=MODEL,
        judge_model=JUDGE,
        scorers=[ScoreFromOutput()],
        repeats=REPEATS,
        temperature=0.0,
        config_json="{}",
    )


async def test_synthetic_three_blocks_paint_red_grey_green_and_cut_keeps_a(db: Database) -> None:
    provider = FakeProvider(scripted(THREE, SHIFTS_THREE), default="0.0")
    report = await run(make_ablation(db, provider), THREE)

    assert {v.segment.text: v.verdict for v in report.verdicts} == {
        "Always answer in French.": "red",
        "Be polite.": "grey",
        "Use emoji.": "green",
    }
    assert all(v.stage == 1 for v in report.verdicts)
    by_text = {v.segment.text: v for v in report.verdicts}
    assert by_text["Always answer in French."].mean_delta == pytest.approx(-0.2)
    assert by_text["Use emoji."].mean_delta == pytest.approx(0.1)
    assert by_text["Be polite."].interval.n_cases == N_CASES

    assert report.cut_prompt == "Always answer in French.\n"
    assert report.baseline_score == pytest.approx(fmean(baseline_score(i) for i in range(N_CASES)))
    # The cut prompt also drops C, which hurt the score, so the confirmation lands above baseline.
    assert report.cut_score == pytest.approx(report.baseline_score + 0.1)
    assert report.confirmation is not None and report.confirmation.mean == pytest.approx(0.1)
    assert report.confirmed and report.stopped == "none" and report.status == "done"
    assert report.tokens_removed > 0 and report.tokens_after < report.tokens_before
    # (baseline + 3 variants + confirmation) × cases × repeats, no cache hits: every prompt is new.
    assert report.calls == 5 * N_CASES * REPEATS and report.cached == 0
    assert report.cost_usd > 0 and report.count("red") == 1


async def test_synthetic_run_writes_every_row(db: Database) -> None:
    provider = FakeProvider(scripted(THREE, SHIFTS_THREE), default="0.0")
    report = await run(make_ablation(db, provider), THREE)
    eid = report.experiment_id

    experiment = ExperimentRepository(db).get(eid)
    assert experiment["kind"] == "ablation" and experiment["status"] == "done"
    assert experiment["stopped_reason"] is None

    segments = SegmentRepository(db).list_by_experiment(eid)
    assert [s["text"] for s in segments] == ["Always answer in French.", "Be polite.", "Use emoji."]
    assert all(s["level"] == "block" and s["parent_segment_id"] is None for s in segments)

    verdicts = VerdictRepository(db).list_by_experiment(eid)
    assert [v["verdict"] for v in verdicts] == ["red", "grey", "green"]
    assert {v["segment_id"] for v in verdicts} == {s["id"] for s in segments}
    assert all(v["stage"] == 1 and v["n_cases"] == N_CASES for v in verdicts)

    row = ExperimentRepository(db).get_ablation(eid)
    assert row["confirmed"] == 1 and row["cut_prompt"] == "Always answer in French.\n"
    assert row["cut_score"] == pytest.approx(row["baseline_score"] + 0.1)
    assert row["cut_ci_low"] == pytest.approx(0.1) and row["cut_ci_high"] == pytest.approx(0.1)
    assert row["tokens_before"] > row["tokens_after"]

    results = ResultRepository(db)
    assert len(results.list_by_variant(eid, None)) == N_CASES * REPEATS
    for segment in segments:
        assert len(results.list_by_variant(eid, segment["id"])) == N_CASES * REPEATS
    # The confirmation run is measured, not stored as a variant.
    assert len(results.list_by_experiment(eid)) == 4 * N_CASES * REPEATS


async def test_stage_two_runs_lines_of_red_blocks_and_cut_keeps_red_lines(db: Database) -> None:
    provider = FakeProvider(scripted(RULES, SHIFTS_RULES), default="0.0")
    report = await run(make_ablation(db, provider), RULES)

    stage_one = {v.segment.text: v.verdict for v in report.verdicts if v.stage == 1}
    stage_two = {v.segment.text: v.verdict for v in report.verdicts if v.stage == 2}
    assert stage_one == {
        "# Rules\n- Always answer in French.\n- Mention the weather.": "red",
        "Be polite.": "grey",
    }
    assert stage_two == {
        "# Rules": "grey",
        "- Always answer in French.": "red",
        "- Mention the weather.": "grey",
    }
    assert report.cut_prompt == "- Always answer in French.\n"
    assert report.confirmed and report.stopped == "none"

    segments = SegmentRepository(db).list_by_experiment(report.experiment_id)
    blocks = {s["text"]: s["id"] for s in segments if s["level"] == "block"}
    lines = [s for s in segments if s["level"] == "line"]
    assert len(lines) == 3
    rules_id = blocks["# Rules\n- Always answer in French.\n- Mention the weather."]
    assert all(line["parent_segment_id"] == rules_id for line in lines)
    verdict_stages = {
        v["stage"] for v in VerdictRepository(db).list_by_experiment(report.experiment_id)
    }
    assert verdict_stages == {1, 2}
    # (baseline + 2 blocks + 3 lines + confirmation) × cases × repeats
    assert report.calls == 7 * N_CASES * REPEATS


async def test_over_budget_estimate_refuses_before_any_call_or_row(db: Database) -> None:
    provider = FakeProvider(scripted(THREE, SHIFTS_THREE), default="0.0")
    ablation = make_ablation(db, provider, budget_usd=0.000001)
    with pytest.raises(BudgetExceededError, match="exceeds budget"):
        await run(ablation, THREE)
    assert provider.calls == []
    assert ExperimentRepository(db).list() == []


async def test_spend_crossing_the_budget_stops_the_run_and_writes_what_it_measured(
    db: Database,
) -> None:
    # The estimate is priced with a free table so it fits; the provider bills real prices, so the
    # budget is crossed after the baseline and the first variant.
    provider = FakeProvider(scripted(THREE, SHIFTS_THREE), default="0.0")
    free = Pricing({MODEL: (0.0, 0.0), JUDGE: (0.0, 0.0)})
    per_call = provider._pricing.cost(MODEL, 13, 1)
    budget = 1.5 * N_CASES * REPEATS * per_call
    report = await run(make_ablation(db, provider, budget_usd=budget, budget_pricing=free), THREE)

    assert report.stopped == "budget" and report.status == "stopped"
    assert report.cost_usd >= budget
    assert [v.segment.text for v in report.verdicts] == ["Always answer in French."]
    # Unmeasured segments stay, so the cut prompt is the original; it is unconfirmed.
    assert report.cut_prompt == THREE
    assert report.cut_score is None and report.confirmation is None and not report.confirmed

    experiment = ExperimentRepository(db).get(report.experiment_id)
    assert (experiment["status"], experiment["stopped_reason"]) == ("stopped", "budget")
    row = ExperimentRepository(db).get_ablation(report.experiment_id)
    assert row["confirmed"] == 0 and row["cut_score"] is None and row["cut_prompt"] == THREE
    assert len(VerdictRepository(db).list_by_experiment(report.experiment_id)) == 1


async def test_every_case_failing_stops_with_error(db: Database) -> None:
    provider = FakeProvider(errors={f"q{i}": "boom" for i in range(N_CASES)})
    report = await run(make_ablation(db, provider), THREE)
    assert report.stopped == "error" and report.verdicts == []
    assert report.baseline_score == 0.0 and report.cut_score is None
    experiment = ExperimentRepository(db).get(report.experiment_id)
    assert (experiment["status"], experiment["stopped_reason"]) == ("stopped", "error")
    assert ExperimentRepository(db).get_ablation(report.experiment_id) is None


async def test_progress_counts_every_planned_call_once(db: Database) -> None:
    seen: list[tuple[int, int, float]] = []
    provider = FakeProvider(scripted(THREE, SHIFTS_THREE), default="0.0")
    ablation = make_ablation(db, provider, progress=lambda d, t, s: seen.append((d, t, s)))
    report = await run(ablation, THREE)
    dones = [d for d, _, _ in seen]
    assert dones == sorted(dones) and dones[-1] == report.calls
    assert seen[-1][1] == report.calls
    assert seen[-1][2] == pytest.approx(report.cost_usd)


async def test_a_wider_delta_turns_green_grey(db: Database) -> None:
    provider = FakeProvider(scripted(THREE, SHIFTS_THREE), default="0.0")
    report = await run(make_ablation(db, provider, delta=0.15), THREE)
    assert {v.segment.text: v.verdict for v in report.verdicts} == {
        "Always answer in French.": "red",
        "Be polite.": "grey",
        "Use emoji.": "grey",
    }
