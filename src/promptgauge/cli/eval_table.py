"""EvalTable: rich table for promptgauge eval; one row per case, totals underneath. PRD F4.2."""

from rich.console import Console
from rich.table import Table

from promptgauge.runner.eval_result import EvalResult

INPUT_WIDTH = 48


class EvalTable:
    """Prints the per-case table and the totals line for one EvalResult."""

    def __init__(self, console: Console) -> None:
        self._console = console

    def render(self, result: EvalResult) -> None:
        """Print the table, the failures (if any) and the totals."""
        table = Table(title=f"{result.name} · {result.model}", title_justify="left")
        table.add_column("#", justify="right")
        table.add_column("input", overflow="ellipsis", no_wrap=True, max_width=INPUT_WIDTH)
        for key in result.scorer_keys:
            table.add_column(key, justify="right")
        table.add_column("score", justify="right")

        for row in result.per_case():
            cells = [str(row.index), row.input]
            cells += [_fmt(row.scorer_means[key]) for key in result.scorer_keys]
            cells.append(_fmt(row.score))
            style = "red" if row.failures else None
            table.add_row(*cells, style=style)
        self._console.print(table)

        for run in result.runs:
            if run.failed:
                self._console.print(
                    f"[red]case {run.case.index} repeat {run.repeat_index} failed:[/] {run.error}"
                )

        cases = len(result.per_case())
        self._console.print(
            f"score {_fmt(result.score)} · cases {cases} · repeats {result.repeats}"
            f" · calls {result.calls} · cached {result.cached_share:.0%}"
            f" · cost ${result.cost_usd:.2f} · time {result.duration_s:.1f}s"
            + (f" · [yellow]{result.status}[/]" if result.status != "done" else "")
        )


def _fmt(value: float | None) -> str:
    return "—" if value is None else f"{value:.2f}"
