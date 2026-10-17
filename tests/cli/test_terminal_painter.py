from pathlib import Path

from rich.console import Console

from promptgauge.ablate.ablation_report import AblationReport
from promptgauge.ablate.segment_verdict import SegmentVerdict
from promptgauge.cli.terminal_painter import STYLES, TerminalPainter
from promptgauge.config.pricing import Pricing
from promptgauge.prompt.prompt_segmenter import PromptSegmenter
from promptgauge.stats.mean_interval import MeanInterval

TEXT = "# Rules\n- Keep it short.\n- Mention the weather.\n\nBe polite.\n\nUse emoji.\n"
INTERVALS = {
    "red": MeanInterval(mean=-0.3, ci_low=-0.4, ci_high=-0.2, n_cases=10),
    "grey": MeanInterval(mean=0.0, ci_low=-0.05, ci_high=0.05, n_cases=10),
    "green": MeanInterval(mean=0.1, ci_low=0.05, ci_high=0.15, n_cases=10),
}
PRICING = Pricing({"m": (2.0, 10.0)})


def verdicts(
    block_colours: list[str], line_colours: list[str] | None = None
) -> list[SegmentVerdict]:
    segmenter = PromptSegmenter()
    blocks = segmenter.blocks(TEXT)
    out = [
        SegmentVerdict(b, 1, INTERVALS[c], c) for b, c in zip(blocks, block_colours, strict=True)
    ]  # type: ignore[arg-type]
    if line_colours:
        lines = segmenter.lines(blocks[0])
        out += [
            SegmentVerdict(ln, 2, INTERVALS[c], c)
            for ln, c in zip(lines, line_colours, strict=True)
        ]  # type: ignore[arg-type]
    return out


def report(**overrides) -> AblationReport:
    fields = dict(
        experiment_id=1,
        name="ablate system.md",
        model="m",
        delta=0.03,
        prompt_text=TEXT,
        verdicts=verdicts(["red", "grey", "green"], ["grey", "red", "grey"]),
        baseline_score=0.80,
        cut_prompt="- Keep it short.\n",
        cut_score=0.82,
        confirmation=MeanInterval(mean=0.02, ci_low=-0.01, ci_high=0.05, n_cases=10),
        confirmed=True,
        tokens_before=1000,
        tokens_after=400,
        calls=200,
        cached=50,
        cost_usd=1.23,
        duration_s=12.3,
        stopped="none",
    )
    fields.update(overrides)
    return AblationReport(**fields)  # type: ignore[arg-type]


def rendered(rep: AblationReport, **kwargs) -> str:
    console = Console(record=True, width=200, force_terminal=False, color_system=None)
    args = dict(calls_per_month=100_000, inr_rate=84.0, cut_path=Path("/p/system.cut.md"))
    args.update(kwargs)
    TerminalPainter(console, PRICING).render(rep, **args)
    return console.export_text()


def test_paint_puts_every_measured_segment_on_its_colour_and_lines_over_blocks() -> None:
    text = TerminalPainter(Console(), PRICING).paint(report())
    assert text.plain == TEXT
    styles_at = {}
    for span in text.spans:
        for pos in range(span.start, span.end):
            styles_at[pos] = span.style  # later spans win, as rich renders them
    assert styles_at[TEXT.index("- Keep it short.")] == STYLES["red"]
    assert styles_at[TEXT.index("# Rules")] == STYLES["grey"]  # a grey line inside a red block
    assert styles_at[TEXT.index("Be polite.")] == STYLES["grey"]
    assert styles_at[TEXT.index("Use emoji.")] == STYLES["green"]
    assert TEXT.index("\n\nBe") + 1 not in styles_at  # the gap between blocks is unpainted


def test_unmeasured_segments_stay_unpainted() -> None:
    text = TerminalPainter(Console(), PRICING).paint(
        report(verdicts=verdicts(["red", "grey", "green"])[:1])
    )
    painted = {pos for span in text.spans for pos in range(span.start, span.end)}
    assert TEXT.index("Be polite.") not in painted and TEXT.index("# Rules") in painted


def test_legend_carries_the_grey_wording_and_counts() -> None:
    out = rendered(report())
    assert "grey: no measurable effect at this sample size (3)" in out
    assert "red: load-bearing (2)" in out and "green: removing it helped (1)" in out
    assert "unpainted: not measured" in out
    assert "Most segments are grey" not in out


def test_mostly_grey_hint_appears_above_80_percent() -> None:
    out = rendered(report(verdicts=verdicts(["grey", "grey", "grey"], ["grey", "red", "grey"])))
    assert "Most segments are grey" in out  # 5 of 6
    out = rendered(report(verdicts=verdicts(["grey", "grey", "grey"], ["grey", "red", "red"])))
    assert "Most segments are grey" not in out  # 4 of 6


def test_confirmed_line_and_money_saved() -> None:
    out = rendered(report())
    assert "baseline 0.80 · cut 0.82 · confirmed · difference +0.02 [-0.01, +0.05]" in out
    # 600 tokens × $2/M × 100,000 calls = $120.00; × 84 = ₹10,080
    assert (
        "tokens 1000 → 400 (−600, −60%) · saves $120.00 / ₹10,080 a month at 100,000 calls" in out
    )
    assert "calls 200 · cached 25% · cost $1.23 · time 12.3s" in out
    assert "cut prompt written to /p/system.cut.md" in out


def test_calls_per_month_scales_the_saving() -> None:
    out = rendered(report(), calls_per_month=10_000, inr_rate=80.0)
    assert "saves $12.00 / ₹960 a month at 10,000 calls" in out


def test_not_confirmed_is_shown_as_a_suggestion() -> None:
    out = rendered(report(cut_score=0.70, confirmed=False))
    assert "cut prompt not confirmed (below baseline − delta)" in out
    assert "shown as a suggestion" in out


def test_stopped_run_without_confirmation() -> None:
    rep = report(
        verdicts=verdicts(["red", "grey", "green"])[:1],
        cut_prompt=TEXT,
        cut_score=None,
        confirmation=None,
        confirmed=False,
        tokens_after=1000,
        stopped="budget",
    )
    out = rendered(rep, cut_path=None)
    assert "Stopped at the budget. 1 segments measured; the rest are unpainted." in out
    assert "cut prompt not confirmed: no confirmation run (stopped: budget)" in out
    assert "cut prompt not written: there was no confirmation run" in out
    assert "tokens 1000 → 1000 (−0, −0%)" in out
