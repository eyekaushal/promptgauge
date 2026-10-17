"""Scorer: base class; score(case, output) -> ScoreResult; skips cases missing the field it
needs.
"""

import re
from abc import ABC, abstractmethod

from promptgauge.dataset.case import Case
from promptgauge.scorers.score_result import ScoreResult

_WHITESPACE = re.compile(r"\s+")


def normalise(text: str) -> str:
    """Lower-case, collapse whitespace runs to one space, strip. Shared by contains and exact so the
    two scorers can never drift apart (PRD F3.1)."""
    return _WHITESPACE.sub(" ", text).strip().lower()


class Scorer(ABC):
    """One scoring rule. `key` labels its column in the result table (matches ScorerSpec.key)."""

    @property
    @abstractmethod
    def key(self) -> str:
        """Stable label, e.g. `contains` or `json_schema:schema.json`."""

    def applies_to(self, case: Case) -> bool:
        """False when the case lacks the field this scorer needs; the runner then records nothing
        for this (case, scorer) rather than a zero."""
        return True

    @abstractmethod
    async def score(self, case: Case, output: str) -> ScoreResult:
        """Score one output for one case. Only called when `applies_to(case)` is true."""
