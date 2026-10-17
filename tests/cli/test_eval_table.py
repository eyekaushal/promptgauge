from rich.console import Console

from promptgauge.cli.eval_table import EvalTable
from promptgauge.dataset.case import Case
from promptgauge.runner.case_run import CaseRun
from promptgauge.runner.eval_result import EvalResult
from promptgauge.scorers.score_result import ScoreResult


def _result(status: str = "done") -> EvalResult:
    a = Case(index=0, input="late order", expected="refund")
    b = Case(index=1, input="hello " * 30)
    runs = [
        CaseRun(a, 1, 0, "ok", "h1", False, {"contains": ScoreResult(score=1.0)}),
        CaseRun(a, 1, 1, "ok", "h2", True, {"contains": ScoreResult(score=0.0, reason="no")}),
        CaseRun(b, 2, 0, error="HTTP 529: overloaded"),
        CaseRun(b, 2, 1, "ok", "h3", False, {}),
    ]
    return EvalResult(
        7, "eval system.md", status, "claude-sonnet-4-5", ["contains"], runs, 4, 1, 0.0123, 2.34
    )


def _render(result: EvalResult) -> str:
    console = Console(record=True, width=120, force_terminal=False, color_system=None)
    EvalTable(console).render(result)
    return console.export_text()


def test_table_has_one_row_per_case_and_totals() -> None:
    text = _render(_result())
    assert "eval system.md · claude-sonnet-4-5" in text
    assert "late order" in text and "0.50" in text
    assert "—" in text  # case 1 has no contains score
    assert "case 1 repeat 0 failed: HTTP 529: overloaded" in text
    assert (
        "score 0.50 · cases 2 · repeats 2 · calls 4 · cached 25% · cost $0.01 · time 2.3s" in text
    )


def test_long_input_is_truncated_and_status_shown_when_not_done() -> None:
    text = _render(_result(status="partial"))
    assert "hello hello" in text and ("…" in text or "..." in text)
    assert "partial" in text
