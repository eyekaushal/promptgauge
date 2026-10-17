from promptgauge.ablate.segment_verdict import SegmentVerdict
from promptgauge.prompt.segment import Segment
from promptgauge.stats.mean_interval import MeanInterval


def test_mean_delta_is_the_interval_mean() -> None:
    seg = Segment(level="block", index=0, start=0, end=2, text="hi", tokens=1)
    verdict = SegmentVerdict(
        seg, 1, MeanInterval(mean=-0.2, ci_low=-0.3, ci_high=-0.1, n_cases=5), "red"
    )
    assert verdict.mean_delta == -0.2 and verdict.stage == 1 and verdict.verdict == "red"
