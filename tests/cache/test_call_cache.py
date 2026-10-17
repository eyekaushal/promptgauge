import asyncio

import pytest

from promptgauge.cache.call_cache import CallCache
from promptgauge.core.errors import ProviderError
from promptgauge.core.logger import Logger
from promptgauge.db.call_repository import CallRepository
from promptgauge.db.database import Database
from promptgauge.provider.fake_provider import FakeProvider

MODEL = "claude-sonnet-4-5"
SYSTEM = "You are a support bot."


def _cache(db: Database, provider: FakeProvider, concurrency: int = 8) -> CallCache:
    return CallCache(provider, CallRepository(db), Logger("test"), concurrency=concurrency)


def _call(cache: CallCache, experiment_id: int, **overrides):
    kwargs = dict(
        system=SYSTEM,
        user="hi",
        model=MODEL,
        temperature=0.7,
        max_tokens=1024,
        repeat_index=0,
        experiment_id=experiment_id,
    )
    kwargs.update(overrides)
    return cache.complete(**kwargs)


def test_key_is_sha256_over_the_five_fields() -> None:
    base = CallCache.key(SYSTEM, "hi", MODEL, 0.7, 0)
    assert len(base) == 64
    assert base == CallCache.key(SYSTEM, "hi", MODEL, 0.7, 0)
    assert base != CallCache.key(SYSTEM + " ", "hi", MODEL, 0.7, 0)
    assert base != CallCache.key(SYSTEM, "hi!", MODEL, 0.7, 0)
    assert base != CallCache.key(SYSTEM, "hi", "claude-haiku-4-5", 0.7, 0)
    assert base != CallCache.key(SYSTEM, "hi", MODEL, 0.0, 0)
    assert base != CallCache.key(SYSTEM, "hi", MODEL, 0.7, 1)


async def test_miss_calls_provider_and_writes_a_priced_row(
    db: Database, experiment_id: int
) -> None:
    provider = FakeProvider({"hi": "hello"})
    cache = _cache(db, provider)
    completion = await _call(cache, experiment_id)

    assert completion.text == "hello"
    assert completion.cached is False
    assert completion.cost_usd > 0
    assert completion.call_hash == CallCache.key(SYSTEM, "hi", MODEL, 0.7, 0)
    rows = CallRepository(db).list_by_experiment(experiment_id)
    assert len(rows) == 1
    assert (rows[0]["cached"], rows[0]["output"]) == (0, "hello")
    assert rows[0]["cost_usd"] == pytest.approx(completion.cost_usd)
    assert rows[0]["hash"] == completion.call_hash
    assert len(provider.calls) == 1


async def test_hit_costs_nothing_and_still_writes_a_row(db: Database, experiment_id: int) -> None:
    provider = FakeProvider({"hi": "hello"})
    cache = _cache(db, provider)
    first = await _call(cache, experiment_id)
    second = await _call(cache, experiment_id)

    assert second.text == first.text
    assert second.cached is True
    assert second.cost_usd == 0.0
    assert (second.input_tokens, second.output_tokens) == (first.input_tokens, first.output_tokens)
    assert len(provider.calls) == 1
    totals = CallRepository(db).totals(experiment_id)
    assert (totals["calls"], totals["cached"]) == (2, 1)
    assert totals["cost_usd"] == pytest.approx(first.cost_usd)


async def test_hit_applies_across_experiments(db: Database, experiment_id: int) -> None:
    from promptgauge.db.experiment_repository import ExperimentRepository

    provider = FakeProvider({"hi": "hello"})
    cache = _cache(db, provider)
    await _call(cache, experiment_id)
    other = ExperimentRepository(db).create(
        kind="eval",
        name="second",
        prompt_hash="p" * 8,
        prompt_text=SYSTEM,
        dataset_hash="d" * 8,
        model=MODEL,
        judge="claude-haiku-4-5",
        config_json="{}",
    )
    completion = await _call(cache, other)
    assert completion.cached is True
    assert CallRepository(db).totals(other)["cost_usd"] == 0.0
    assert len(provider.calls) == 1


async def test_repeats_and_variants_are_separate_keys(db: Database, experiment_id: int) -> None:
    provider = FakeProvider({"hi": "hello"})
    cache = _cache(db, provider)
    await _call(cache, experiment_id, repeat_index=0)
    await _call(cache, experiment_id, repeat_index=1)
    await _call(cache, experiment_id, system=SYSTEM + "\nBe brief.")
    assert len(provider.calls) == 3
    assert CallRepository(db).totals(experiment_id)["cached"] == 0


async def test_max_tokens_is_not_part_of_the_key(db: Database, experiment_id: int) -> None:
    provider = FakeProvider()
    cache = _cache(db, provider)
    await _call(cache, experiment_id, max_tokens=512)
    second = await _call(cache, experiment_id, max_tokens=1024)
    assert second.cached is True


async def test_provider_error_propagates_and_writes_no_row(
    db: Database, experiment_id: int
) -> None:
    provider = FakeProvider(errors={"hi": "overloaded"})
    cache = _cache(db, provider)
    with pytest.raises(ProviderError, match="overloaded"):
        await _call(cache, experiment_id)
    assert CallRepository(db).totals(experiment_id)["calls"] == 0


async def test_semaphore_limits_in_flight_provider_calls(db: Database, experiment_id: int) -> None:
    class SlowProvider(FakeProvider):
        in_flight = 0
        peak = 0

        async def complete(self, *args, **kwargs):
            SlowProvider.in_flight += 1
            SlowProvider.peak = max(SlowProvider.peak, SlowProvider.in_flight)
            await asyncio.sleep(0.01)
            SlowProvider.in_flight -= 1
            return await super().complete(*args, **kwargs)

    cache = _cache(db, SlowProvider(), concurrency=2)
    await asyncio.gather(*(_call(cache, experiment_id, user=f"q{i}") for i in range(6)))
    assert SlowProvider.peak == 2
    assert CallRepository(db).totals(experiment_id)["calls"] == 6


def test_concurrency_must_be_positive(db: Database) -> None:
    with pytest.raises(ValueError):
        _cache(db, FakeProvider(), concurrency=0)
