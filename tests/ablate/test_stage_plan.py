from promptgauge.ablate.stage_plan import StagePlan
from promptgauge.prompt.segment import Segment


def _seg(i: int) -> Segment:
    return Segment(level="block", index=i, start=i * 2, end=i * 2 + 1, text="x", tokens=1)


def test_stage_one_counts_the_baseline() -> None:
    plan = StagePlan(1, [_seg(0), _seg(1), _seg(2)], True, cases=10, repeats=3)
    assert (plan.variants, plan.calls) == (4, 120)


def test_stage_two_has_no_baseline() -> None:
    plan = StagePlan(2, [_seg(0), _seg(1)], False, cases=10, repeats=3)
    assert (plan.variants, plan.calls) == (2, 60)


def test_empty_stage_two_costs_nothing() -> None:
    assert StagePlan(2, [], False, cases=10, repeats=3).calls == 0
