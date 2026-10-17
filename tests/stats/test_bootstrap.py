import random

import pytest

from promptgauge.stats.bootstrap import Bootstrap


def _synthetic(n: int, centre: float, spread: float, seed: int = 7) -> list[float]:
    rng = random.Random(seed)
    return [rng.gauss(centre, spread) for _ in range(n)]


def test_mean_is_the_arithmetic_mean_and_inside_the_interval() -> None:
    interval = Bootstrap().mean_ci([-0.2, -0.1, 0.0, 0.1, 0.2, 0.3])
    assert interval.mean == pytest.approx(0.05)
    assert interval.ci_low <= interval.mean <= interval.ci_high
    assert interval.n_cases == 6


def test_same_seed_same_interval() -> None:
    diffs = _synthetic(20, -0.1, 0.2)
    first = Bootstrap(seed=42).mean_ci(diffs)
    second = Bootstrap(seed=42).mean_ci(diffs)
    assert first == second


def test_call_order_does_not_change_the_result() -> None:
    boot = Bootstrap(seed=3)
    diffs = _synthetic(15, 0.0, 0.3)
    alone = Bootstrap(seed=3).mean_ci(diffs)
    boot.mean_ci(_synthetic(9, 0.5, 0.1))
    assert boot.mean_ci(diffs) == alone


def test_different_seed_different_interval() -> None:
    diffs = _synthetic(20, -0.1, 0.2)
    assert Bootstrap(seed=1).mean_ci(diffs) != Bootstrap(seed=2).mean_ci(diffs)


def test_interval_narrows_with_more_cases() -> None:
    boot = Bootstrap()
    widths = []
    for n in (10, 40, 160):
        interval = boot.mean_ci(_synthetic(n, -0.1, 0.25))
        widths.append(interval.ci_high - interval.ci_low)
    assert widths[0] > widths[1] > widths[2]


def test_lower_level_gives_a_narrower_interval() -> None:
    diffs = _synthetic(30, 0.0, 0.2)
    wide = Bootstrap().mean_ci(diffs, level=0.95)
    narrow = Bootstrap().mean_ci(diffs, level=0.50)
    assert narrow.ci_high - narrow.ci_low < wide.ci_high - wide.ci_low
    assert wide.ci_low <= narrow.ci_low and narrow.ci_high <= wide.ci_high


def test_constant_differences_collapse_to_a_point() -> None:
    interval = Bootstrap().mean_ci([-0.2] * 12)
    assert interval.mean == pytest.approx(-0.2)
    assert interval.ci_low == interval.mean == interval.ci_high


def test_single_case_is_a_point_interval() -> None:
    interval = Bootstrap().mean_ci([0.4])
    assert (interval.mean, interval.ci_low, interval.ci_high, interval.n_cases) == (
        0.4,
        0.4,
        0.4,
        1,
    )


def test_interval_covers_the_true_shift_on_clear_signal() -> None:
    interval = Bootstrap().mean_ci(_synthetic(50, -0.2, 0.05))
    assert interval.ci_high < -0.15 and interval.ci_low > -0.25


@pytest.mark.parametrize(
    ("diffs", "kwargs"),
    [
        ([], {}),
        ([0.1], {"resamples": 0}),
        ([0.1], {"level": 0.0}),
        ([0.1], {"level": 1.0}),
    ],
)
def test_bad_arguments_are_rejected(diffs: list[float], kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        Bootstrap().mean_ci(diffs, **kwargs)  # type: ignore[arg-type]
