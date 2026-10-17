"""PromptSegmenter: blocks on blank lines and headings; lines on list items and sentences; fenced
code is one segment; round-trips byte for byte. PRD F5.1, F5.2.
"""

import re
from collections.abc import Callable
from typing import Literal

from promptgauge.prompt.segment import Segment

_HEADING = re.compile(r"^ {0,3}#{1,6}(\s|$)")
_FENCE_OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d{1,9}[.)])\s")
# A sentence ends at . ? or ! (plus any closing quote or bracket) when whitespace and an uppercase
# letter follow. Abbreviations such as "e.g. The" therefore split; that is accepted for v1.
_SENTENCE_END = re.compile(r"[.?!][\"')\]]*(?=\s+[A-Z])")


class PromptSegmenter:
    """Split a prompt into blocks, and a block into lines, without changing a single character.

    Blocks are separated by blank lines; a markdown heading always starts a new block and belongs
    to it. Inside a fenced code block nothing splits, so the fence is one block (or one line when
    it shares a block with surrounding text). Lines are headings, list items (with their indented
    continuation lines), fences, and sentences of a paragraph.
    """

    def __init__(self, count_tokens: Callable[[str], int] | None = None) -> None:
        # prompt/ must not import provider/ (PRD §11.3), so the tokenizer is injected. Offline the
        # estimate is len/4, the usual rule of thumb for English prose (F5.4).
        self._count_tokens = count_tokens or self._estimate_tokens

    def blocks(self, text: str) -> list[Segment]:
        """Top-level segments of `text` in document order (F5.1)."""
        spans: list[tuple[int, int]] = []
        current: tuple[int, int] | None = None
        fence: str | None = None
        for start, end, line in self._physical_lines(text):
            if fence is not None:
                current = (current[0], end) if current else (start, end)
                if self._closes_fence(line, fence):
                    fence = None
                continue
            if not line.strip():
                if current:
                    spans.append(current)
                current = None
                continue
            if _HEADING.match(line):
                if current:
                    spans.append(current)
                current = (start, end)
                continue
            opened = _FENCE_OPEN.match(line)
            if opened:
                fence = opened.group(1)
            current = (current[0], end) if current else (start, end)
        if current:
            spans.append(current)
        return [self._segment("block", i, None, s, e, text) for i, (s, e) in enumerate(spans)]

    def lines(self, block: Segment) -> list[Segment]:
        """Line-level segments inside one block, with absolute offsets (F5.2). A block that
        yields a single line is a "single-line block" for the cutter (F6.6)."""
        spans: list[tuple[int, int]] = []
        paragraph: tuple[int, int] | None = None
        fence: str | None = None
        in_item = False
        for start, end, line in self._physical_lines(block.text):
            if fence is not None:
                spans[-1] = (spans[-1][0], end)
                if self._closes_fence(line, fence):
                    fence = None
                continue
            is_item = bool(_LIST_ITEM.match(line))
            opened = _FENCE_OPEN.match(line)
            if _HEADING.match(line) or is_item or opened:
                self._flush(paragraph, block.text, spans)
                paragraph = None
                spans.append((start, end))
                in_item = is_item
                if opened:
                    fence = opened.group(1)
                continue
            if in_item and line[:1].isspace() and line.strip():
                # An indented line right after a list item wraps that item.
                spans[-1] = (spans[-1][0], end)
                continue
            in_item = False
            paragraph = (paragraph[0], end) if paragraph else (start, end)
        self._flush(paragraph, block.text, spans)
        base = block.start
        return [
            self._segment("line", i, block.index, base + s, base + e, block.text, base)
            for i, (s, e) in enumerate(spans)
        ]

    def _flush(
        self,
        paragraph: tuple[int, int] | None,
        text: str,
        spans: list[tuple[int, int]],
    ) -> None:
        """Append the sentences of a finished paragraph to `spans`."""
        if paragraph is None:
            return
        start, end = paragraph
        body = text[start:end]
        sentence_start = 0
        for match in _SENTENCE_END.finditer(body):
            spans.append((start + sentence_start, start + match.end()))
            sentence_start = match.end()
            while sentence_start < len(body) and body[sentence_start].isspace():
                sentence_start += 1
        tail = len(body.rstrip())
        if sentence_start < tail:
            spans.append((start + sentence_start, start + tail))

    def _segment(
        self,
        level: Literal["block", "line"],
        index: int,
        parent_index: int | None,
        start: int,
        end: int,
        text: str,
        base: int = 0,
    ) -> Segment:
        piece = text[start - base : end - base]
        return Segment(
            level=level,
            index=index,
            parent_index=parent_index,
            start=start,
            end=end,
            text=piece,
            tokens=self._count_tokens(piece),
        )

    @staticmethod
    def _physical_lines(text: str) -> list[tuple[int, int, str]]:
        """(start, end, content) per line; `end` excludes the newline so it never joins a span."""
        out: list[tuple[int, int, str]] = []
        pos = 0
        for raw in text.splitlines(keepends=True):
            content = raw.rstrip("\r\n")
            out.append((pos, pos + len(content), content))
            pos += len(raw)
        return out

    @staticmethod
    def _closes_fence(line: str, fence: str) -> bool:
        stripped = line.strip()
        return (
            len(stripped) >= len(fence)
            and stripped[0] == fence[0]
            and stripped == stripped[0] * len(stripped)
        )

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return max(1, len(text) // 4)
