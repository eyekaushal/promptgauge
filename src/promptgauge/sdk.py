"""Public functions evaluate() and ablate().

Both build the same composition root as the CLI (cli/main.py) and call it. PRD §7.4.
Filled at B07 (evaluate) and B11 (ablate).
"""

from typing import Any


def evaluate(**kwargs: Any) -> Any:
    """Run every case against the prompt and return an EvalResult. Built at B07."""
    raise NotImplementedError("evaluate() is built at block B07")


def ablate(**kwargs: Any) -> Any:
    """Knock out segments, measure, and return an AblationReport. Built at B11."""
    raise NotImplementedError("ablate() is built at block B11")
