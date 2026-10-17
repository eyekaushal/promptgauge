from pydantic import BaseModel

from promptgauge.db.call_repository import CallRepository
from promptgauge.provider.fake_provider import FakeProvider
from promptgauge.scorers.judge import MAX_TOKENS, Judge
from tests.scorers.conftest import JUDGE_MODEL, SequenceProvider


class Answer(BaseModel):
    score: float
    reason: str


async def test_well_formed_answer_is_parsed(make_judge) -> None:
    provider = FakeProvider(default='{"score": 0.8, "reason": "fine"}')
    answer = await make_judge(provider).ask("sys", "user", Answer)
    assert answer == Answer(score=0.8, reason="fine")
    call = provider.calls[0]
    assert (call.system, call.user, call.model) == ("sys", "user", JUDGE_MODEL)
    assert (call.temperature, call.max_tokens) == (0.0, MAX_TOKENS)


async def test_fenced_answer_is_parsed(make_judge) -> None:
    provider = FakeProvider(default='```json\n{"score": 1, "reason": "ok"}\n```')
    assert (await make_judge(provider).ask("sys", "user", Answer)).score == 1.0


async def test_malformed_answer_is_retried_once_with_a_new_cache_key(make_judge) -> None:
    provider = SequenceProvider(["not json", '{"score": 0.5, "reason": "second try"}'])
    answer = await make_judge(provider).ask("sys", "user", Answer)
    assert answer == Answer(score=0.5, reason="second try")
    assert len(provider.calls) == 2


async def test_two_malformed_answers_give_none(make_judge) -> None:
    provider = SequenceProvider(['{"score": "high"}', "{}"])
    assert await make_judge(provider).ask("sys", "user", Answer) is None
    assert len(provider.calls) == 2


async def test_judge_calls_are_cached_and_recorded(make_judge, db, experiment_id) -> None:
    provider = FakeProvider(default='{"score": 0.8, "reason": "fine"}')
    judge = make_judge(provider)
    await judge.ask("sys", "user", Answer)
    await judge.ask("sys", "user", Answer)
    assert len(provider.calls) == 1
    totals = CallRepository(db).totals(experiment_id)
    assert (totals["calls"], totals["cached"]) == (2, 1)


async def test_prompt_text_is_part_of_the_key(make_judge) -> None:
    provider = FakeProvider(default='{"score": 0.8, "reason": "fine"}')
    judge = make_judge(provider)
    await judge.ask("sys v1", "user", Answer)
    await judge.ask("sys v2", "user", Answer)
    assert len(provider.calls) == 2


def test_prompts_are_read_from_the_package() -> None:
    assert "JSON" in Judge.prompt("rubric")
    assert "claim" in Judge.prompt("grounded").lower()
