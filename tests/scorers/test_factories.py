import json
from pathlib import Path

from promptgauge import scorers
from promptgauge.scorers.contains_scorer import ContainsScorer
from promptgauge.scorers.exact_scorer import ExactScorer
from promptgauge.scorers.json_schema_scorer import JsonSchemaScorer


def test_factories_build_the_scorers(tmp_path: Path) -> None:
    schema = tmp_path / "s.json"
    schema.write_text(json.dumps({"type": "object"}))
    assert isinstance(scorers.contains(), ContainsScorer)
    assert isinstance(scorers.exact(), ExactScorer)
    assert isinstance(scorers.json_schema(schema), JsonSchemaScorer)
