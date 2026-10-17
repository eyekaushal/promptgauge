"""PromptCutter: original minus every grey and green segment; red blocks keep only red lines. PRD
F6.6.
"""

from promptgauge.ablate.segment_verdict import SegmentVerdict
from promptgauge.prompt.segment import Segment
from promptgauge.prompt.variant_builder import VariantBuilder


class PromptCutter:
    """Turn verdicts into the shorter prompt. Deletion only: every character of the output comes
    from the original (invariant 2)."""

    def cut(self, text: str, verdicts: list[SegmentVerdict]) -> str:
        """Remove what the verdicts say can go. Segments without a verdict (a run stopped before
        measuring them) stay: there is no evidence to cut on."""
        removed = self._to_remove(verdicts)
        # Later ranges first: a deletion only rewrites text from the previous content onwards, so
        # earlier offsets stay valid and VariantBuilder's exact-match check keeps holding.
        for segment in sorted(removed, key=lambda s: s.start, reverse=True):
            text = VariantBuilder(text).without(segment)
        return text

    @staticmethod
    def _to_remove(verdicts: list[SegmentVerdict]) -> list[Segment]:
        lines_by_block: dict[int, list[SegmentVerdict]] = {}
        for v in verdicts:
            if v.stage == 2 and v.segment.parent_index is not None:
                lines_by_block.setdefault(v.segment.parent_index, []).append(v)
        removed: list[Segment] = []
        for v in verdicts:
            if v.stage != 1:
                continue
            if v.verdict != "red":
                removed.append(v.segment)
                continue
            lines = lines_by_block.get(v.segment.index, []) if v.segment.level == "block" else []
            # A red block keeps only its red lines. With no stage-two lines (single-line block),
            # or none of them red on their own, the block stays whole: cutting a block the data
            # says matters, on line-level evidence that found nothing, would knowingly hurt.
            if any(line.verdict == "red" for line in lines):
                removed.extend(line.segment for line in lines if line.verdict != "red")
        return removed
