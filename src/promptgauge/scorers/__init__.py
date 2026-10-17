"""Scorer factories exposed to the SDK: contains(), exact(), json_schema(path),
rubric(name_or_path), grounded().

rubric() and grounded() arrive with the judge at B06.
"""

from pathlib import Path

from promptgauge.scorers.contains_scorer import ContainsScorer
from promptgauge.scorers.exact_scorer import ExactScorer
from promptgauge.scorers.json_schema_scorer import JsonSchemaScorer


def contains() -> ContainsScorer:
    """Expected text appears in the output (normalised)."""
    return ContainsScorer()


def exact() -> ExactScorer:
    """Output equals the expected text (normalised)."""
    return ExactScorer()


def json_schema(path: Path | str) -> JsonSchemaScorer:
    """Output is JSON that validates against the schema file at `path`."""
    return JsonSchemaScorer(path)
