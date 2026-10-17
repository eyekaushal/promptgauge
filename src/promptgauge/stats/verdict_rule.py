"""VerdictRule(delta): red if ci_high < -delta, green if ci_low > +delta, grey otherwise. PRD
F6.5.
"""

from typing import Literal

Verdict = Literal["red", "grey", "green"]


class VerdictRule:
    """Turn an interval of (variant − baseline) into a colour. Red: removing the segment hurts by
    more than `delta` with confidence. Green: removing it helps. Grey: no measurable effect at this
    sample size, which is not the same as "does nothing" (invariant 4)."""

    def __init__(self, delta: float) -> None:
        if delta < 0.0:
            raise ValueError("delta must be >= 0")
        self._delta = delta

    @property
    def delta(self) -> float:
        """The indifference margin in score units."""
        return self._delta

    def verdict(self, ci_low: float, ci_high: float) -> Verdict:
        """Colour for one stored interval. Takes the bounds, not a MeanInterval, so the API can
        repaint straight from verdict rows."""
        if ci_high < -self._delta:
            return "red"
        if ci_low > self._delta:
            return "green"
        return "grey"
