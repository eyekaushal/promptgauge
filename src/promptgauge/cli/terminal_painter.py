"""TerminalPainter: the prompt with ANSI colours per verdict, legend, totals, the grey wording, the
>80% grey hint. PRD F6.8.
"""

from pathlib import Path

from rich.console import Console
from rich.text import Text

from promptgauge.ablate.ablation_report import AblationReport
from promptgauge.config.pricing import Pricing

# DESIGN.md verdict colours: ink on the soft shade, so a long red block stays readable.
INK = "#1c1c1e"
STYLES = {
    "red": f"{INK} on #fbe4e1",
    "grey": f"{INK} on #ececee",
    "green": f"{INK} on #dff2e6",
}
STRONG = {"red": "#c0392b", "grey": "#7a7a80", "green": "#2e7d4f"}
WORDS = {
    "red": "load-bearing",
    "grey": "no measurable effect at this sample size",
    "green": "removing it helped",
}
GREY_HINT_SHARE = 0.8


class TerminalPainter:
    """Print one AblationReport: the painted prompt, a legend with the word for every colour
    (invariant 4), the cut-prompt verdict (invariant 5), tokens, cost and money saved (F6.9)."""

    def __init__(self, console: Console, pricing: Pricing) -> None:
        self._console = console
        self._pricing = pricing

    def paint(self, report: AblationReport) -> Text:
        """The prompt text with each measured segment on its verdict's colour. Lines inside a red
        block paint over the block, so stage two is what the eye sees there."""
        text = Text(report.prompt_text, no_wrap=False)
        for stage in (1, 2):
            for v in report.verdicts:
                if v.stage == stage:
                    text.stylize(STYLES[v.verdict], v.segment.start, v.segment.end)
        return text

    def render(
        self,
        report: AblationReport,
        *,
        calls_per_month: int,
        inr_rate: float,
        cut_path: Path | None,
    ) -> None:
        """Print everything. `cut_path` is where the cut prompt was written, or None if it was
        not (no confirmation run)."""
        out = self._console
        out.print(f"[bold]{report.name}[/] · {report.model} · delta {report.delta:g}")
        if report.stopped != "none":
            out.print(self._stopped_line(report), highlight=False)
        out.print()
        out.print(self.paint(report))
        out.print()
        out.print(self._legend(report), highlight=False)
        if self._mostly_grey(report):
            out.print(
                "[#9a6400]Most segments are grey:[/] at this sample size the run cannot separate "
                "them from the baseline. More cases or repeats narrow the intervals.",
                highlight=False,
            )
        out.print()
        out.print(self._confirmation_line(report), highlight=False)
        out.print(self._tokens_line(report, calls_per_month, inr_rate), highlight=False)
        out.print(
            f"calls {report.calls} · cached {self._cached_share(report):.0%} · "
            f"cost ${report.cost_usd:.2f} · time {report.duration_s:.1f}s",
            highlight=False,
        )
        if cut_path is None:
            out.print("cut prompt not written: there was no confirmation run", highlight=False)
        else:
            out.print(f"cut prompt written to {cut_path}", highlight=False)

    @staticmethod
    def _stopped_line(report: AblationReport) -> str:
        measured = len({v.segment for v in report.verdicts})
        reason = "at the budget" if report.stopped == "budget" else "on an error"
        return (
            f"[#9a6400]Stopped {reason}.[/] {measured} segments measured; the rest are unpainted."
        )

    @staticmethod
    def _legend(report: AblationReport) -> str:
        parts = [
            f"[{STRONG[c]}]■[/] {c}: {WORDS[c]} ({report.count(c)})"
            for c in ("red", "grey", "green")
        ]
        parts.append("unpainted: not measured")
        return "  ".join(parts)

    @staticmethod
    def _mostly_grey(report: AblationReport) -> bool:
        measured = len(report.verdicts)
        return measured > 0 and report.count("grey") / measured > GREY_HINT_SHARE

    @staticmethod
    def _confirmation_line(report: AblationReport) -> str:
        base = f"baseline {report.baseline_score:.2f}"
        if report.confirmation is None or report.cut_score is None:
            return (
                f"{base} · [#c0392b]cut prompt not confirmed[/]: no confirmation run "
                f"(stopped: {report.stopped}); the cut below is a suggestion"
            )
        ci = report.confirmation
        diff = f"difference {ci.mean:+.2f} [{ci.ci_low:+.2f}, {ci.ci_high:+.2f}]"
        if report.confirmed:
            return f"{base} · cut {report.cut_score:.2f} · [#2e7d4f]confirmed[/] · {diff}"
        return (
            f"{base} · cut {report.cut_score:.2f} · [#c0392b]cut prompt not confirmed[/] "
            f"(below baseline − delta) · {diff} · shown as a suggestion"
        )

    def _tokens_line(self, report: AblationReport, calls_per_month: int, inr_rate: float) -> str:
        before, after = report.tokens_before, report.tokens_after
        share = (report.tokens_removed / before) if before else 0.0
        per_token = self._pricing.input_per_million(report.model) / 1_000_000
        usd = report.tokens_removed * per_token * calls_per_month
        return (
            f"tokens {before} → {after} (−{report.tokens_removed}, −{share:.0%}) · "
            f"saves ${usd:,.2f} / ₹{usd * inr_rate:,.0f} a month at {calls_per_month:,} calls"
        )

    @staticmethod
    def _cached_share(report: AblationReport) -> float:
        return report.cached / report.calls if report.calls else 0.0
