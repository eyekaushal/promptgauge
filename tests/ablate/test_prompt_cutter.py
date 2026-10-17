import pytest

from promptgauge.ablate.prompt_cutter import PromptCutter
from promptgauge.ablate.segment_verdict import SegmentVerdict
from promptgauge.prompt.prompt_segmenter import PromptSegmenter
from promptgauge.prompt.segment import Segment
from promptgauge.stats.mean_interval import MeanInterval

RED = MeanInterval(mean=-0.3, ci_low=-0.4, ci_high=-0.2, n_cases=6)
GREY = MeanInterval(mean=0.0, ci_low=-0.05, ci_high=0.05, n_cases=6)
GREEN = MeanInterval(mean=0.1, ci_low=0.05, ci_high=0.15, n_cases=6)
COLOURS = {"red": RED, "grey": GREY, "green": GREEN}


def verdict(segment: Segment, colour: str, stage: int) -> SegmentVerdict:
    return SegmentVerdict(segment, stage, COLOURS[colour], colour)  # type: ignore[arg-type]


def cut(text: str, blocks: dict[int, str], lines: dict[tuple[int, int], str] | None = None) -> str:
    """`blocks` maps block index → colour (stage 1); `lines` maps (block, line) → colour (stage 2).
    Blocks and lines not named stay unmeasured."""
    segmenter = PromptSegmenter()
    all_blocks = segmenter.blocks(text)
    verdicts = [verdict(all_blocks[i], colour, 1) for i, colour in blocks.items()]
    for (b, i), colour in (lines or {}).items():
        verdicts.append(verdict(segmenter.lines(all_blocks[b])[i], colour, 2))
    return PromptCutter().cut(text, verdicts)


THREE = "A one.\n\nB two.\n\nC three.\n"
RULES = "# Rules\n- Keep it short.\n- Mention the weather.\n\nBe polite.\n"


@pytest.mark.parametrize(
    ("text", "blocks", "lines", "expected"),
    [
        # Grey and green blocks go; red blocks stay.
        (THREE, {0: "red", 1: "grey", 2: "green"}, None, "A one.\n"),
        (THREE, {0: "grey", 1: "red", 2: "grey"}, None, "B two.\n"),
        (THREE, {0: "red", 1: "red", 2: "green"}, None, "A one.\n\nB two.\n"),
        (THREE, {0: "red", 1: "red", 2: "red"}, None, THREE),
        # Everything grey: nothing is left (the confirmation run will judge that).
        (THREE, {0: "grey", 1: "grey", 2: "grey"}, None, ""),
        # Unmeasured segments stay: a stopped run has no evidence against them.
        (THREE, {0: "grey"}, None, "B two.\n\nC three.\n"),
        (THREE, {}, None, THREE),
        # Inside a red block only red lines stay.
        (
            RULES,
            {0: "red", 1: "grey"},
            {(0, 0): "grey", (0, 1): "red", (0, 2): "grey"},
            "- Keep it short.\n",
        ),
        (
            RULES,
            {0: "red", 1: "red"},
            {(0, 0): "red", (0, 1): "red", (0, 2): "grey"},
            "# Rules\n- Keep it short.\n\nBe polite.\n",
        ),
        # A red block whose lines were all grey on their own stays whole.
        (
            RULES,
            {0: "red", 1: "grey"},
            {(0, 0): "grey", (0, 1): "grey", (0, 2): "grey"},
            "# Rules\n- Keep it short.\n- Mention the weather.\n",
        ),
        # A red block with no stage-two lines stays whole.
        (RULES, {0: "red", 1: "grey"}, None, "# Rules\n- Keep it short.\n- Mention the weather.\n"),
    ],
)
def test_cut(text: str, blocks: dict[int, str], lines, expected: str) -> None:
    assert cut(text, blocks, lines) == expected


def test_single_block_prompt_cuts_its_stage_one_lines() -> None:
    text = "Keep it short. Mention the weather. Be polite."
    segmenter = PromptSegmenter()
    lines = segmenter.lines(segmenter.blocks(text)[0])
    verdicts = [
        verdict(lines[0], "red", 1),
        verdict(lines[1], "grey", 1),
        verdict(lines[2], "green", 1),
    ]
    assert PromptCutter().cut(text, verdicts) == "Keep it short."


def test_output_only_ever_contains_original_characters() -> None:
    out = cut(RULES, {0: "red", 1: "grey"}, {(0, 0): "grey", (0, 1): "red", (0, 2): "grey"})
    assert "".join(out.split()) in "".join(RULES.split()).replace("#Rules", "")  # subsequence check
    assert all(ch in RULES for ch in out)
