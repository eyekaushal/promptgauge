import pytest

from promptgauge.core.errors import PromptError
from promptgauge.prompt.prompt_segmenter import PromptSegmenter
from promptgauge.prompt.segment import Segment
from promptgauge.prompt.variant_builder import VariantBuilder
from tests.prompt.conftest import read_fixture


def _ink(text: str) -> str:
    return "".join(text.split())


def all_segments(text: str) -> list[Segment]:
    segmenter = PromptSegmenter()
    out: list[Segment] = []
    for block in segmenter.blocks(text):
        out.append(block)
        out.extend(segmenter.lines(block))
    return out


def test_every_variant_removes_exactly_its_segment(fixture_text: str) -> None:
    builder = VariantBuilder(fixture_text)
    for seg in all_segments(fixture_text):
        variant = builder.without(seg)
        # Nothing but whitespace changed, and only the segment's characters are gone.
        assert _ink(variant) == _ink(fixture_text[: seg.start]) + _ink(fixture_text[seg.end :])
        assert variant.count(seg.text) == fixture_text.count(seg.text) - 1
        assert "\n\n\n" not in variant
        assert variant != fixture_text
        assert len(variant) < len(fixture_text)


def test_variants_differ_for_different_segments(fixture_text: str) -> None:
    builder = VariantBuilder(fixture_text)
    blocks = PromptSegmenter().blocks(fixture_text)
    variants = [builder.without(b) for b in blocks]
    assert len(set(variants)) == len(variants)


@pytest.mark.parametrize(
    ("text", "which", "expected"),
    [
        # Middle block: one blank line remains, not two.
        ("A\n\nB\n\nC\n", ("block", 1), "A\n\nC\n"),
        # First block: the following block moves to the top.
        ("A\n\nB\n\nC\n", ("block", 0), "B\n\nC\n"),
        # Last block: the final newline is kept.
        ("A\n\nB\n\nC\n", ("block", 2), "A\n\nB\n"),
        ("A\n\nB", ("block", 1), "A"),
        # Middle list item.
        ("- a\n- b\n- c", ("line", 1), "- a\n- c"),
        # Last item of a list that is followed by another block keeps the block gap.
        ("- a\n- b\n\n# H", ("line", 1), "- a\n\n# H"),
        # A heading glued to its content: removing the heading leaves the content as the block.
        ("X\n\n# H\n- a", ("line", 1), "X\n\n- a"),
        # Sentences: a single space remains.
        ("One. Two. Three.", ("line", 1), "One. Three."),
        ("One. Two. Three.", ("line", 0), "Two. Three."),
        ("One. Two. Three.", ("line", 2), "One. Two."),
        # Sentence at a line break: the newline is the separator that stays.
        ("One. Two.\nThree.", ("line", 1), "One.\nThree."),
        ("One.\nTwo. Three.", ("line", 1), "One.\nThree."),
        # Indentation of the next line is preserved.
        ("- a\n  - b\n  - c", ("line", 1), "- a\n  - c"),
        ("- a\n  - b", ("line", 0), "  - b"),
        # Fenced code is removed in one piece.
        ("Use:\n\n```\nx\n```\n\nEnd.", ("block", 1), "Use:\n\nEnd."),
    ],
)
def test_exact_variants(text: str, which: tuple[str, int], expected: str) -> None:
    level, index = which
    segmenter = PromptSegmenter()
    blocks = segmenter.blocks(text)
    if level == "block":
        seg = blocks[index]
    else:
        seg = [ln for b in blocks for ln in segmenter.lines(b)][index]
    assert VariantBuilder(text).without(seg) == expected


def test_single_line_block_variant_equals_block_variant() -> None:
    text = read_fixture("headings_and_bullets")
    segmenter = PromptSegmenter()
    role = segmenter.blocks(text)[0]
    (only_line,) = segmenter.lines(role)
    builder = VariantBuilder(text)
    assert builder.without(role) == builder.without(only_line)


def test_segment_from_another_prompt_is_refused() -> None:
    seg = Segment(level="block", index=0, start=0, end=3, text="abc", tokens=1)
    with pytest.raises(PromptError, match="does not match"):
        VariantBuilder("xyz\n\nmore").without(seg)


def test_builder_never_mutates_its_text() -> None:
    text = "A\n\nB"
    builder = VariantBuilder(text)
    seg = PromptSegmenter().blocks(text)[0]
    builder.without(seg)
    assert builder.without(seg) == "B"
