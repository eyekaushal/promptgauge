import pytest

from promptgauge.stats.verdict_rule import VerdictRule


@pytest.mark.parametrize(
    ("delta", "ci_low", "ci_high", "expected"),
    [
        # Red: the whole interval sits below -delta.
        (0.03, -0.30, -0.10, "red"),
        (0.03, -0.05, -0.04, "red"),
        (0.00, -0.10, -0.01, "red"),
        (0.10, -0.50, -0.11, "red"),
        # Green: the whole interval sits above +delta.
        (0.03, 0.10, 0.30, "green"),
        (0.03, 0.04, 0.05, "green"),
        (0.00, 0.01, 0.10, "green"),
        (0.10, 0.11, 0.50, "green"),
        # Grey: the interval touches or straddles the [-delta, +delta] band.
        (0.03, -0.10, 0.10, "grey"),
        (0.03, -0.03, -0.01, "grey"),
        (0.03, -0.02, 0.02, "grey"),
        (0.03, 0.01, 0.03, "grey"),
        (0.03, -0.20, -0.03, "grey"),
        (0.03, 0.03, 0.20, "grey"),
        (0.03, -0.20, 0.00, "grey"),
        (0.00, 0.00, 0.00, "grey"),
        (0.00, -0.10, 0.00, "grey"),
        (0.03, 0.00, 0.00, "grey"),
    ],
)
def test_verdict_table(delta: float, ci_low: float, ci_high: float, expected: str) -> None:
    assert VerdictRule(delta).verdict(ci_low, ci_high) == expected


def test_a_wider_delta_turns_red_into_grey() -> None:
    assert VerdictRule(0.03).verdict(-0.08, -0.05) == "red"
    assert VerdictRule(0.05).verdict(-0.08, -0.05) == "grey"


def test_delta_is_exposed_and_negative_is_rejected() -> None:
    assert VerdictRule(0.03).delta == 0.03
    with pytest.raises(ValueError):
        VerdictRule(-0.01)
