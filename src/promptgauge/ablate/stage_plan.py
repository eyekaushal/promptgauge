"""StagePlan: the segments one ablation stage removes, one at a time, and the calls that costs."""

from dataclasses import dataclass
from typing import Literal

from promptgauge.prompt.segment import Segment


@dataclass(frozen=True)
class StagePlan:
    """One stage of the plan (PRD F6.1). `segments` are removed one per variant; `baseline` says
    whether the unmodified prompt also runs in this stage (stage one only)."""

    stage: Literal[1, 2]
    segments: list[Segment]
    baseline: bool
    cases: int
    repeats: int

    @property
    def variants(self) -> int:
        """Prompt versions this stage runs, the baseline included."""
        return len(self.segments) + (1 if self.baseline else 0)

    @property
    def calls(self) -> int:
        """Target-model calls: every variant runs the whole dataset with every repeat."""
        return self.variants * self.cases * self.repeats
