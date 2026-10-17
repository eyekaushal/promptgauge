"""AblationPlanner: stage one (baseline + one variant per block), stage two (lines inside red
blocks); call counts. PRD F6.1.
"""

from promptgauge.ablate.stage_plan import StagePlan
from promptgauge.prompt.prompt_segmenter import PromptSegmenter
from promptgauge.prompt.segment import Segment


class AblationPlanner:
    """Decide which segments each stage removes. Pure: no calls, no database."""

    def __init__(self, segmenter: PromptSegmenter, cases: int, repeats: int) -> None:
        if cases < 1 or repeats < 1:
            raise ValueError("an ablation needs at least one case and one repeat")
        self._segmenter = segmenter
        self._cases = cases
        self._repeats = repeats

    def stage_one(self, text: str) -> StagePlan:
        """Baseline plus one variant per block. A prompt with a single block is ablated at the
        line level directly (F5.5), and then has no stage two."""
        blocks = self._segmenter.blocks(text)
        segments = self._segmenter.lines(blocks[0]) if len(blocks) == 1 else blocks
        return StagePlan(1, segments, True, self._cases, self._repeats)

    def stage_two(self, red: list[Segment]) -> StagePlan:
        """One variant per line inside every red block. A block with a single line has nothing
        to split and stays whole (F6.6); red lines from a single-block stage one have no children.
        """
        segments = [line for block in red for line in self._lines_of(block)]
        return StagePlan(2, segments, False, self._cases, self._repeats)

    def stage_two_candidates(self, text: str) -> int:
        """Lines stage two would run if every block went red. The budget planner scales this by
        the share of blocks expected to go red (F6.2)."""
        blocks = self._segmenter.blocks(text)
        if len(blocks) == 1:
            return 0
        return sum(len(self._lines_of(block)) for block in blocks)

    def _lines_of(self, segment: Segment) -> list[Segment]:
        if segment.level != "block":
            return []
        lines = self._segmenter.lines(segment)
        return lines if len(lines) > 1 else []
