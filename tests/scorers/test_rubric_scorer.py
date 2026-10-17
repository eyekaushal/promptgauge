from pathlib import Path

import pytest

from promptgauge.core.errors import ScorerError
from promptgauge.dataset.case import Case
from promptgauge.provider.fake_provider import FakeProvider
from promptgauge.scorers.judge import Judge
from promptgauge.scorers.rubric_scorer import BUILT_IN_RUBRICS, RubricScorer
from tests.scorers.conftest import SequenceProvider

CASE = Case(index=0, input="Where is my order?")


@pytest.mark.parametrize(
    ("answer", "score", "reason"),
    [
        ('{"score": 1.0, "reason": "direct"}', 1.0, "direct"),
        ('{"score": 0, "reason": "ignores the question"}', 0.0, "ignores the question"),
        ('{"score": 0.5, "reason": "partial", "extra": true}', 0.5, "partial"),
        ('Sure:\n```json\n{"score": 0.75, "reason": "mostly"}\n```', 0.75, "mostly"),
    ],
)
async def test_positive(make_judge, answer: str, score: float, reason: str) -> None:
    scorer = RubricScorer("helpful")
    scorer.bind(make_judge(FakeProvider(default=answer)))
    result = await scorer.score(CASE, "It arrives in 10 minutes.")
    assert (result.score, result.reason) == (score, reason)


@pytest.mark.parametrize(
    "answer",
    [
        "I would say this is helpful.",
        '{"score": 7, "reason": "out of ten"}',
        '{"score": 0.5}',
        '{"reason": "no score"}',
        '{"score": -0.1, "reason": "negative"}',
    ],
)
async def test_negative_malformed_answers_score_none(make_judge, answer: str) -> None:
    provider = SequenceProvider([answer, answer])
    scorer = RubricScorer("helpful")
    scorer.bind(make_judge(provider))
    result = await scorer.score(CASE, "whatever")
    assert (result.score, result.reason) == (None, "judge_failed")
    assert len(provider.calls) == 2


async def test_judge_sees_rubric_input_and_output(make_judge) -> None:
    provider = FakeProvider(default='{"score": 1, "reason": "x"}')
    scorer = RubricScorer("concise")
    scorer.bind(make_judge(provider))
    await scorer.score(CASE, "Ten minutes.")
    call = provider.calls[0]
    assert call.system == Judge.prompt("rubric")
    assert scorer.rubric in call.user
    assert "Where is my order?" in call.user
    assert "Ten minutes." in call.user


@pytest.mark.parametrize("name", BUILT_IN_RUBRICS)
def test_built_in_rubrics_load(name: str) -> None:
    scorer = RubricScorer(name)
    assert scorer.key == f"rubric:{name}"
    assert scorer.rubric.startswith("Score")


def test_custom_rubric_file(tmp_path: Path) -> None:
    path = tmp_path / "brand_voice.md"
    path.write_text("Score whether the reply sounds like Swiggle.\n")
    scorer = RubricScorer(path)
    assert scorer.key == "rubric:brand_voice"
    assert scorer.rubric == "Score whether the reply sounds like Swiggle."


def test_unknown_rubric() -> None:
    with pytest.raises(ScorerError, match="unknown rubric 'nope'"):
        RubricScorer("nope")


async def test_scoring_without_a_judge_is_an_error() -> None:
    with pytest.raises(ScorerError, match="no judge bound"):
        await RubricScorer("helpful").score(CASE, "x")


def test_applies_to_every_case() -> None:
    assert RubricScorer("helpful").applies_to(CASE) is True
