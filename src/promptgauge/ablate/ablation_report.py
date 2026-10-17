"""AblationReport: verdicts, cut prompt, baseline and confirmation scores, tokens removed, cost,
duration, stopped.
"""

from dataclasses import dataclass
from typing import Literal

from promptgauge.ablate.segment_verdict import SegmentVerdict
from promptgauge.stats.mean_interval import MeanInterval

Stopped = Literal["none", "budget", "error"]


@dataclass(frozen=True)
class AblationReport:
    """Everything the CLI paints and the ablation row stores (PRD F6.8). The cut prompt is a
    result only when `confirmation` is present and `confirmed` is true; otherwise it is a
    suggestion (invariant 5, F6.7)."""

    experiment_id: int
    name: str
    model: str
    delta: float
    prompt_text: str
    verdicts: list[SegmentVerdict]
    baseline_score: float
    cut_prompt: str
    cut_score: float | None
    confirmation: MeanInterval | None
    confirmed: bool
    tokens_before: int
    tokens_after: int
    calls: int
    cached: int
    cost_usd: float
    duration_s: float
    stopped: Stopped

    @property
    def tokens_removed(self) -> int:
        """Tokens the cut prompt saves on every call."""
        return self.tokens_before - self.tokens_after

    @property
    def status(self) -> str:
        """Experiment status as stored: `done`, or `stopped` when the run ended early."""
        return "done" if self.stopped == "none" else "stopped"

    def count(self, verdict: str) -> int:
        """Number of segments painted `verdict` across both stages."""
        return sum(1 for v in self.verdicts if v.verdict == verdict)
