import json

import pytest

from promptgauge.core.errors import ScorerError
from promptgauge.dataset.case import Case
from promptgauge.provider.fake_provider import FakeProvider
from promptgauge.scorers.grounded_scorer import GroundedScorer
from promptgauge.scorers.judge import Judge
from tests.scorers.conftest import SequenceProvider

CASE = Case(index=0, input="When does it arrive?", context="Order 2210, ETA 20 minutes.")


def _answer(*claims: tuple[str, bool]) -> str:
    return json.dumps({"claims": [{"text": t, "supported": s} for t, s in claims]})


@pytest.mark.parametrize(
    ("answer", "score", "reason"),
    [
        (_answer(("ETA is 20 minutes", True)), 1.0, None),
        (_answer(("ETA is 20 minutes", True), ("order is 2210", True)), 1.0, None),
        (
            _answer(("ETA 20 min", True), ("driver is Ravi", False)),
            0.5,
            "unsupported: driver is Ravi",
        ),
        (
            _answer(("a", True), ("b", False), ("c", False), ("d", True)),
            0.5,
            "unsupported: b; c",
        ),
        (
            _answer(("a", False), ("b", False), ("c", True)),
            pytest.approx(1 / 3),
            "unsupported: a; b",
        ),
        (_answer(("it is raining", False)), 0.0, "unsupported: it is raining"),
        (_answer(), 1.0, "no factual claims"),
        ("```json\n" + _answer(("x", True)) + "\n```", 1.0, None),
    ],
)
async def test_positive(make_judge, answer: str, score, reason) -> None:
    scorer = GroundedScorer()
    scorer.bind(make_judge(FakeProvider(default=answer)))
    result = await scorer.score(CASE, "Your order arrives in 20 minutes.")
    assert result.score == score
    assert result.reason == reason


@pytest.mark.parametrize(
    "answer",
    [
        "All claims are supported.",
        '{"claims": "none"}',
        '{"claims": [{"text": "x"}]}',
        '{"claims": [{"supported": true}]}',
        '{"supported": 2, "total": 3}',
    ],
)
async def test_negative_malformed_answers_score_none(make_judge, answer: str) -> None:
    provider = SequenceProvider([answer, answer])
    scorer = GroundedScorer()
    scorer.bind(make_judge(provider))
    result = await scorer.score(CASE, "whatever")
    assert (result.score, result.reason) == (None, "judge_failed")
    assert len(provider.calls) == 2


async def test_judge_sees_context_and_output(make_judge) -> None:
    provider = FakeProvider(default=_answer())
    scorer = GroundedScorer()
    scorer.bind(make_judge(provider))
    await scorer.score(CASE, "Twenty minutes.")
    call = provider.calls[0]
    assert call.system == Judge.prompt("grounded")
    assert "Order 2210, ETA 20 minutes." in call.user
    assert "Twenty minutes." in call.user


def test_skips_cases_without_context() -> None:
    scorer = GroundedScorer()
    assert scorer.applies_to(Case(index=0, input="q")) is False
    assert scorer.applies_to(Case(index=0, input="q", context="")) is False
    assert scorer.applies_to(CASE) is True
    assert scorer.key == "grounded"


async def test_scoring_without_a_judge_is_an_error() -> None:
    with pytest.raises(ScorerError, match="no judge bound"):
        await GroundedScorer().score(CASE, "x")
