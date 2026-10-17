"""VariantBuilder: the prompt minus one segment's character range, by slicing. Deletion only. PRD
F5.3.
"""

from promptgauge.core.errors import PromptError
from promptgauge.prompt.segment import Segment


class VariantBuilder:
    """Build deletion variants of one prompt. The only operation is removing a segment's exact
    character range and collapsing the whitespace that the removal left touching, so no double
    blank line remains. No character outside that whitespace ever changes (invariant 2)."""

    def __init__(self, text: str) -> None:
        self._text = text

    def without(self, segment: Segment) -> str:
        """The prompt with `segment` removed."""
        if self._text[segment.start : segment.end] != segment.text:
            raise PromptError(
                f"segment {segment.level}[{segment.index}] at {segment.start}:{segment.end} "
                "does not match this prompt text"
            )
        before = self._text[: segment.start]
        after = self._text[segment.end :]
        lead = before[len(before.rstrip()) :]
        trail = after[: len(after) - len(after.lstrip())]
        if not before.strip():
            # Removed the first segment: drop the blank lines before what follows but keep its
            # indentation; a same-line gap (sentence) goes entirely.
            return after[trail.rfind("\n") + 1 :] if "\n" in trail else after.lstrip()
        if not after.strip():
            # Removed the last segment: keep the file's final newline if it had one.
            return before.rstrip() + ("\n" if self._text.endswith("\n") else "")
        newlines = max(lead.count("\n"), trail.count("\n"))
        if newlines:
            indent = trail[trail.rfind("\n") + 1 :] if "\n" in trail else ""
            separator = "\n" * newlines + indent
        else:
            separator = lead or trail
        return before.rstrip() + separator + after.lstrip()
