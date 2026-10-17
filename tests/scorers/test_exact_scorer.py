import pytest

from promptgauge.dataset.case import Case
from promptgauge.scorers.exact_scorer import ExactScorer


def _case(expected: str | None) -> Case:
    return Case(index=0, input="q", expected=expected)


@pytest.mark.parametrize(
    ("expected", "output"),
    [
        ("refund", "refund"),
        ("Refund", "REFUND"),
        ("delivery fee", "  delivery\n fee  "),
        ("yes.", "Yes."),
        ("a b c", "a   b\tc"),
    ],
)
async def test_positive(expected: str, output: str) -> None:
    result = await ExactScorer().score(_case(expected), output)
    assert (result.score, result.reason) == (1.0, None)


@pytest.mark.parametrize(
    ("expected", "output"),
    [
        ("refund", "a refund"),
        ("refund", "refunds"),
        ("yes", "yes."),
        ("delivery fee", "deliveryfee"),
        ("x", ""),
    ],
)
async def test_negative(expected: str, output: str) -> None:
    result = await ExactScorer().score(_case(expected), output)
    assert result.score == 0.0
    assert result.reason is not None


def test_skips_cases_without_expected() -> None:
    assert ExactScorer().applies_to(_case(None)) is False
    assert ExactScorer().applies_to(_case("x")) is True


def test_key() -> None:
    assert ExactScorer().key == "exact"
