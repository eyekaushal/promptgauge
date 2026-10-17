from pathlib import Path

import pytest

from promptgauge.cache.call_cache import CallCache
from promptgauge.core.logger import Logger
from promptgauge.dataset.dataset_loader import DatasetLoader
from promptgauge.db.call_repository import CallRepository
from promptgauge.db.case_repository import CaseRepository
from promptgauge.db.database import Database
from promptgauge.db.experiment_repository import ExperimentRepository
from promptgauge.db.result_repository import ResultRepository
from promptgauge.provider.fake_provider import FakeProvider
from promptgauge.runner.evaluator import Evaluator
from promptgauge.scorers import contains, grounded, rubric

ROWS = (
    '{"input": "late order", "expected": "refund"}\n'
    '{"input": "eta?", "expected": "", "context": "ETA 20 min"}\n'
    '{"input": "hello"}\n'
)
JUDGE_OK = '{"score": 0.5, "reason": "meh"}'
GROUNDED_OK = '{"claims": [{"text": "20 min", "supported": true}]}'


@pytest.fixture
def dataset(tmp_path: Path):
    path = tmp_path / "cases.jsonl"
    path.write_text(ROWS)
    return DatasetLoader().load(path)


def _evaluator(db: Database, provider: FakeProvider, progress=None) -> Evaluator:
    cache = CallCache(provider, CallRepository(db), Logger("test"))
    return Evaluator(
        cache,
        ExperimentRepository(db),
        CaseRepository(db),
        ResultRepository(db),
        CallRepository(db),
        Logger("test"),
        progress,
    )


def _provider(**extra) -> FakeProvider:
    # Target replies by case input; everything else (judge calls) gets the rubric JSON.
    return FakeProvider(
        {"late order": "We will refund you.", "eta?": "20 min"}, default=JUDGE_OK, **extra
    )


async def _run(evaluator: Evaluator, dataset, scorers, repeats=2, name="t"):
    return await evaluator.run(
        name=name,
        prompt_text="Be kind.",
        dataset=dataset,
        model="claude-sonnet-4-5",
        judge_model="claude-haiku-4-5",
        scorers=scorers,
        repeats=repeats,
        temperature=0.7,
        config_json="{}",
    )


async def test_runs_every_case_and_repeat_and_stores_rows(db: Database, dataset) -> None:
    provider = _provider()
    result = await _run(_evaluator(db, provider), dataset, [contains(), rubric("helpful")])

    assert result.status == "done"
    assert len(result.runs) == 6
    assert result.scorer_keys == ["contains", "rubric:helpful"]
    # contains applies to case 0 only (case 1 has expected "", case 2 none); rubric to all.
    means = result.scorer_means()
    assert means["contains"] == 1.0
    assert means["rubric:helpful"] == 0.5
    assert result.score == pytest.approx((0.75 * 2 + 0.5 * 4) / 6)

    rows = ResultRepository(db).list_by_experiment(result.experiment_id)
    assert len(rows) == 2 + 6
    assert all(r["variant_id"] is None and r["call_hash"] for r in rows)
    experiment = ExperimentRepository(db).get(result.experiment_id)
    assert (experiment["status"], experiment["kind"], experiment["name"]) == ("done", "eval", "t")
    assert experiment["dataset_hash"] == dataset.hash
    assert len(experiment["prompt_hash"]) == 64
    assert len(CaseRepository(db).list_by_dataset(dataset.hash)) == 3


async def test_totals_come_from_the_call_table(db: Database, dataset) -> None:
    result = await _run(_evaluator(db, _provider()), dataset, [contains(), rubric("helpful")])
    # 6 target calls + 6 judge calls. FakeProvider repeats the same output for both repeats, so
    # the judge's second verdict per case is a cache hit: identical outputs share one verdict.
    assert (result.calls, result.cached) == (12, 3)
    assert result.cost_usd == pytest.approx(
        CallRepository(db).totals(result.experiment_id)["cost_usd"]
    )
    assert result.cost_usd > 0
    assert result.duration_s >= 0


async def test_rerun_is_free_and_fully_cached(db: Database, dataset) -> None:
    provider = _provider()
    first = await _run(_evaluator(db, provider), dataset, [contains(), rubric("helpful")])
    second = await _run(_evaluator(db, provider), dataset, [contains(), rubric("helpful")])
    assert second.experiment_id != first.experiment_id
    assert second.score == first.score
    assert (second.calls, second.cached, second.cost_usd) == (12, 12, 0.0)
    assert second.cached_share == 1.0
    assert all(run.cached for run in second.runs)


async def test_failed_call_marks_run_and_experiment_partial(db: Database, dataset) -> None:
    provider = _provider(errors={"hello": "HTTP 529: overloaded"})
    result = await _run(_evaluator(db, provider), dataset, [contains()])

    assert result.status == "partial"
    assert result.failures == 2
    failed = [r for r in result.runs if r.failed]
    assert all(r.case.index == 2 and "overloaded" in r.error for r in failed)
    assert all(r.output is None and r.scores == {} for r in failed)
    assert ExperimentRepository(db).get(result.experiment_id)["status"] == "partial"
    assert len(ResultRepository(db).list_by_experiment(result.experiment_id)) == 2


async def test_judge_failure_stores_null_score_not_zero(db: Database, dataset) -> None:
    provider = FakeProvider({"late order": "x", "eta?": "y"}, default="not json at all")
    result = await _run(_evaluator(db, provider), dataset, [rubric("helpful")], repeats=1)
    assert result.status == "done"
    assert result.score is None
    rows = ResultRepository(db).list_by_experiment(result.experiment_id)
    assert [(r["score"], r["reason"]) for r in rows] == [(None, "judge_failed")] * 3


async def test_grounded_skips_cases_without_context(db: Database, dataset) -> None:
    provider = FakeProvider({"late order": "x", "eta?": "20 min"}, default=GROUNDED_OK)
    result = await _run(_evaluator(db, provider), dataset, [grounded()], repeats=1)
    rows = ResultRepository(db).list_by_experiment(result.experiment_id)
    assert len(rows) == 1
    assert result.per_case()[0].scorer_means["grounded"] is None
    assert result.per_case()[1].scorer_means["grounded"] == 1.0


async def test_progress_reports_done_total_and_spend(db: Database, dataset) -> None:
    ticks: list[tuple[int, int, float]] = []
    evaluator = _evaluator(db, _provider(), progress=lambda d, t, s: ticks.append((d, t, s)))
    await _run(evaluator, dataset, [contains()], repeats=2)
    assert [t[0] for t in ticks] == list(range(1, 7))
    assert all(t[1] == 6 for t in ticks)
    assert ticks[-1][2] > 0 and ticks == sorted(ticks, key=lambda t: t[2])


async def test_per_case_table(db: Database, dataset) -> None:
    result = await _run(_evaluator(db, _provider()), dataset, [contains(), rubric("helpful")])
    table = result.per_case()
    assert [row.index for row in table] == [0, 1, 2]
    assert table[0].input == "late order"
    assert (table[0].scorer_means, table[0].score) == (
        {"contains": 1.0, "rubric:helpful": 0.5},
        0.75,
    )
    assert (table[1].scorer_means["contains"], table[1].repeats, table[1].failures) == (None, 2, 0)
    assert result.repeats == 2
