import pytest
from pydantic import ValidationError

from promptgauge.stats.mean_interval import MeanInterval


def test_degenerate_interval_is_allowed() -> None:
    interval = MeanInterval(mean=0.1, ci_low=0.1, ci_high=0.1, n_cases=1)
    assert (interval.ci_low, interval.ci_high) == (0.1, 0.1)


@pytest.mark.parametrize(
    "fields",
    [
        {"mean": 0.0, "ci_low": 0.1, "ci_high": 0.2, "n_cases": 3},
        {"mean": 0.3, "ci_low": 0.1, "ci_high": 0.2, "n_cases": 3},
        {"mean": 0.15, "ci_low": 0.2, "ci_high": 0.1, "n_cases": 3},
        {"mean": 0.0, "ci_low": 0.0, "ci_high": 0.0, "n_cases": 0},
        {"mean": 0.0, "ci_low": 0.0, "ci_high": 0.0, "n_cases": 1, "verdict": "red"},
    ],
)
def test_invalid_intervals_are_rejected(fields: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        MeanInterval(**fields)  # type: ignore[arg-type]
