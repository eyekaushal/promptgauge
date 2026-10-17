"""Scorer factories exposed to the SDK: contains(), exact(), json_schema(path),
rubric(name_or_path), grounded().
"""

from pathlib import Path

from promptgauge.scorers.contains_scorer import ContainsScorer
from promptgauge.scorers.exact_scorer import ExactScorer
from promptgauge.scorers.grounded_scorer import GroundedScorer
from promptgauge.scorers.json_schema_scorer import JsonSchemaScorer
from promptgauge.scorers.rubric_scorer import RubricScorer


def contains() -> ContainsScorer:
    """Expected text appears in the output (normalised)."""
    return ContainsScorer()


def exact() -> ExactScorer:
    """Output equals the expected text (normalised)."""
    return ExactScorer()


def json_schema(path: Path | str) -> JsonSchemaScorer:
    """Output is JSON that validates against the schema file at `path`."""
    return JsonSchemaScorer(path)


def rubric(name_or_path: str | Path) -> RubricScorer:
    """The judge scores the output against a built-in rubric name or a rubric file."""
    return RubricScorer(name_or_path)


def grounded() -> GroundedScorer:
    """The judge checks every claim in the output against the case context."""
    return GroundedScorer()
