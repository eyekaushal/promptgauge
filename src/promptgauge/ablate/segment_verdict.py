"""SegmentVerdict: segment + mean_delta, ci_low, ci_high, n_cases, verdict, stage."""

from dataclasses import dataclass
from typing import Literal

from promptgauge.prompt.segment import Segment
from promptgauge.stats.mean_interval import MeanInterval
from promptgauge.stats.verdict_rule import Verdict


@dataclass(frozen=True)
class SegmentVerdict:
    """What removing one segment did: the interval of (variant − baseline) across cases and the
    colour the rule gave it (PRD F6.5). Grey means no measurable effect at this sample size."""

    segment: Segment
    stage: Literal[1, 2]
    interval: MeanInterval
    verdict: Verdict

    @property
    def mean_delta(self) -> float:
        """Mean score change when the segment is removed; negative means the segment helps."""
        return self.interval.mean
