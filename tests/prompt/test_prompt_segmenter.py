import pytest

from promptgauge.prompt.prompt_segmenter import PromptSegmenter
from promptgauge.prompt.segment import Segment
from tests.prompt.conftest import read_fixture


def reassemble(text: str, segments: list[Segment], base: int = 0) -> str:
    """Join segments with the original separators; every gap must be whitespace only."""
    out: list[str] = []
    pos = 0
    for seg in segments:
        gap = text[pos : seg.start - base]
        assert gap.strip() == "", f"non-whitespace gap {gap!r} before {seg.text!r}"
        assert text[seg.start - base : seg.end - base] == seg.text
        out.extend([gap, seg.text])
        pos = seg.end - base
    tail = text[pos:]
    assert tail.strip() == ""
    out.append(tail)
    return "".join(out)


def test_blocks_round_trip_every_fixture(fixture_text: str) -> None:
    blocks = PromptSegmenter().blocks(fixture_text)
    assert blocks
    assert reassemble(fixture_text, blocks) == fixture_text
    assert [b.index for b in blocks] == list(range(len(blocks)))
    assert all(b.level == "block" and b.parent_index is None for b in blocks)


def test_lines_round_trip_inside_every_block(fixture_text: str) -> None:
    segmenter = PromptSegmenter()
    for block in segmenter.blocks(fixture_text):
        lines = segmenter.lines(block)
        assert lines, block.text
        assert reassemble(block.text, lines, base=block.start) == block.text
        assert lines[0].start == block.start and lines[-1].end == block.end
        assert [ln.index for ln in lines] == list(range(len(lines)))
        assert all(ln.level == "line" and ln.parent_index == block.index for ln in lines)
        # Line offsets are absolute: slicing the full prompt yields the same text.
        assert all(fixture_text[ln.start : ln.end] == ln.text for ln in lines)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        (
            "headings_and_bullets",
            [
                "# Role",
                "You are a helpful assistant.",
                "# Rules",
                "- Answer briefly.\n- Never guess.",
            ],
        ),
        (
            "paragraphs",
            [
                "First sentence of a paragraph. Second sentence here. Third one ends it.",
                "Another paragraph with one sentence.",
            ],
        ),
        ("mixed", ["# A", "- one\n- two", "Para one. Para two?", "## B", "Last line."]),
        (
            "single_block",
            ["Only one block, three sentences. No headings at all. Still ablated line by line."],
        ),
        (
            "fenced_code",
            ["# Example", "Use this format:", '```json\n{"a": 1,\n "b": 2}\n```', "Then stop."],
        ),
    ],
)
def test_block_texts(name: str, expected: list[str]) -> None:
    assert [b.text for b in PromptSegmenter().blocks(read_fixture(name))] == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        (
            "headings_and_bullets",
            [
                ["# Role"],
                ["You are a helpful assistant."],
                ["# Rules"],
                ["- Answer briefly.", "- Never guess."],
            ],
        ),
        (
            "paragraphs",
            [
                ["First sentence of a paragraph.", "Second sentence here.", "Third one ends it."],
                ["Another paragraph with one sentence."],
            ],
        ),
        (
            "mixed",
            [["# A"], ["- one", "- two"], ["Para one.", "Para two?"], ["## B"], ["Last line."]],
        ),
        (
            "single_block",
            [
                [
                    "Only one block, three sentences.",
                    "No headings at all.",
                    "Still ablated line by line.",
                ]
            ],
        ),
        (
            "fenced_code",
            [
                ["# Example"],
                ["Use this format:"],
                ['```json\n{"a": 1,\n "b": 2}\n```'],
                ["Then stop."],
            ],
        ),
    ],
)
def test_line_texts(name: str, expected: list[list[str]]) -> None:
    segmenter = PromptSegmenter()
    blocks = segmenter.blocks(read_fixture(name))
    assert [[ln.text for ln in segmenter.lines(b)] for b in blocks] == expected


def test_single_block_prompt_still_yields_lines() -> None:
    # F5.5: nothing special is needed; the one block simply has three lines.
    segmenter = PromptSegmenter()
    blocks = segmenter.blocks(read_fixture("single_block"))
    assert len(blocks) == 1 and len(segmenter.lines(blocks[0])) == 3


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # A heading starts a new block even without a blank line before it, and belongs to it.
        ("Intro line.\n# Rules\n- a\n- b", ["Intro line.", "# Rules\n- a\n- b"]),
        # Blank lines and '#' lines inside a fence never split it.
        (
            "```\n# not a heading\n\nstill code\n```\nAfter.",
            ["```\n# not a heading\n\nstill code\n```\nAfter."],
        ),
        ("A\n\n```\n\n# x\n```\n\nB", ["A", "```\n\n# x\n```", "B"]),
        # Tilde fences and longer backtick fences close only on a matching run.
        (
            "~~~\n```\nnot closed by backticks\n~~~\n\nB",
            ["~~~\n```\nnot closed by backticks\n~~~", "B"],
        ),
        ("````\n```\ninner\n```\n````\n\nB", ["````\n```\ninner\n```\n````", "B"]),
        # An unterminated fence runs to the end of the prompt.
        ("A\n\n```\nopen\n\nforever", ["A", "```\nopen\n\nforever"]),
        # Whitespace-only lines are blank lines; leading and trailing blank lines are separators.
        ("\n\nA\n  \nB\n\n\n", ["A", "B"]),
        # Windows line endings do not end up inside a block's text.
        ("A\r\n\r\nB\r\n", ["A", "B"]),
        # A '#' with no space is not a heading.
        ("A\n#tag\nB", ["A\n#tag\nB"]),
        ("", []),
        ("   \n\n", []),
    ],
)
def test_block_rules(text: str, expected: list[str]) -> None:
    assert [b.text for b in PromptSegmenter().blocks(text)] == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # Each list item is one line, including numbered and nested items.
        ("1. First\n2. Second\n   - nested", ["1. First", "2. Second", "   - nested"]),
        ("* a\n+ b\n- c", ["* a", "+ b", "- c"]),
        # An indented continuation belongs to its list item.
        ("- A long item\n  that wraps.\n- Next.", ["- A long item\n  that wraps.", "- Next."]),
        # Sentences split on . ? ! followed by whitespace and an uppercase letter.
        (
            "Stop here. then lower. Then Upper! Really? Yes.",
            ["Stop here. then lower.", "Then Upper!", "Really?", "Yes."],
        ),
        # Closing quotes and brackets stay with their sentence.
        ('Say "no." Then stop (now.) Done.', ['Say "no."', "Then stop (now.)", "Done."]),
        # A wrapped paragraph splits across physical lines; the newline is the separator.
        ("First one.\nSecond one. Third\none.", ["First one.", "Second one.", "Third\none."]),
        # Heading + paragraph in one block (no blank line between them).
        ("# H\nOne. Two.", ["# H", "One.", "Two."]),
        # Text followed by a fence in the same block: the fence is one line.
        ("Use:\n```\nx\n\ny\n```\nEnd.", ["Use:", "```\nx\n\ny\n```", "End."]),
        # A paragraph with no boundary is one line; trailing punctuation-free text too.
        ("no punctuation at all", ["no punctuation at all"]),
        ("Ends with no period", ["Ends with no period"]),
        # Decimal numbers and ellipses followed by lowercase do not split.
        ("Pay 3.50 for it... then leave. Go.", ["Pay 3.50 for it... then leave.", "Go."]),
    ],
)
def test_line_rules(text: str, expected: list[str]) -> None:
    segmenter = PromptSegmenter()
    blocks = segmenter.blocks(text)
    assert len(blocks) == 1
    assert [ln.text for ln in segmenter.lines(blocks[0])] == expected


def test_tokens_default_to_len_over_four_with_a_floor_of_one() -> None:
    blocks = PromptSegmenter().blocks("abcdefgh\n\nxy")
    assert [b.tokens for b in blocks] == [2, 1]


def test_tokens_use_the_injected_counter() -> None:
    blocks = PromptSegmenter(count_tokens=lambda s: len(s.split())).blocks("one two three\n\nfour")
    assert [b.tokens for b in blocks] == [3, 1]
