import pytest

from promptgauge.dataset.case import Case
from promptgauge.scorers.contains_scorer import ContainsScorer
from promptgauge.scorers.scorer import normalise


def _case(expected: str | None) -> Case:
    return Case(index=0, input="q", expected=expected)


@pytest.mark.parametrize(
    ("expected", "output"),
    [
        ("refund", "We will issue a refund of the delivery fee."),
        ("Refund", "A REFUND is on its way."),
        ("delivery fee", "Refund of the delivery\n   fee issued."),
        ("website", "Please see our website for partnerships."),
        ("  hi  ", "hi"),
    ],
)
async def test_positive(expected: str, output: str) -> None:
    result = await ContainsScorer().score(_case(expected), output)
    assert (result.score, result.reason) == (1.0, None)


@pytest.mark.parametrize(
    ("expected", "output"),
    [
        ("refund", "We cannot help with that."),
        ("delivery fee", "We refund the fee for delivery."),
        ("refunds", "A refund is coming."),
        ("website", ""),
        ("re fund", "refund"),
    ],
)
async def test_negative(expected: str, output: str) -> None:
    result = await ContainsScorer().score(_case(expected), output)
    assert result.score == 0.0
    assert result.reason is not None and expected in result.reason


def test_skips_cases_without_expected() -> None:
    scorer = ContainsScorer()
    assert scorer.applies_to(_case(None)) is False
    assert scorer.applies_to(Case(index=0, input="q", expected="")) is False
    assert scorer.applies_to(_case("x")) is True


def test_key() -> None:
    assert ContainsScorer().key == "contains"


def test_normalise() -> None:
    assert normalise("  Hello,\n\tWorld  ") == "hello, world"
