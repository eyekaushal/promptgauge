"""Scorer: base class; score(case, output) -> ScoreResult; skips cases missing the field it
needs.
"""

import json
import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from promptgauge.dataset.case import Case
from promptgauge.scorers.score_result import ScoreResult

if TYPE_CHECKING:
    from promptgauge.scorers.judge import Judge

_WHITESPACE = re.compile(r"\s+")
# A ```json ... ``` or ``` ... ``` block anywhere in a model's answer.
_FENCE = re.compile(r"```(?:json)?\s*\n?(.*?)```", re.DOTALL | re.IGNORECASE)

# Sentinel for a failed parse: `None` is itself valid JSON (`null`).
NOT_JSON = object()


def normalise(text: str) -> str:
    """Lower-case, collapse whitespace runs to one space, strip. Shared by contains and exact so the
    two scorers can never drift apart (PRD F3.1)."""
    return _WHITESPACE.sub(" ", text).strip().lower()


def parse_json(text: str) -> Any:
    """Parse a model answer as JSON, trying the whole text first and then each fenced block.
    Returns NOT_JSON when nothing parses. Shared by the schema scorer and the judge so both
    tolerate the same answer shapes."""
    candidates = [text.strip()] + [m.group(1).strip() for m in _FENCE.finditer(text)]
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return NOT_JSON


class Scorer(ABC):
    """One scoring rule. `key` labels its column in the result table (matches ScorerSpec.key)."""

    @property
    @abstractmethod
    def key(self) -> str:
        """Stable label, e.g. `contains` or `json_schema:schema.json`."""

    @property
    def uses_judge(self) -> bool:
        """True for scorers that spend a judge call per output; the budget planner counts them."""
        return False

    def applies_to(self, case: Case) -> bool:
        """False when the case lacks the field this scorer needs; the runner then records nothing
        for this (case, scorer) rather than a zero."""
        return True

    def bind(self, judge: "Judge") -> None:
        """Give judge-backed scorers the run's Judge. Free scorers ignore it. Called by the
        runner once per experiment, because SDK users build scorers before any run exists."""
        return None

    @abstractmethod
    async def score(self, case: Case, output: str) -> ScoreResult:
        """Score one output for one case. Only called when `applies_to(case)` is true."""
