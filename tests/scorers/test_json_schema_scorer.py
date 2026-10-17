import json
from pathlib import Path

import pytest

from promptgauge.core.errors import ScorerError
from promptgauge.dataset.case import Case
from promptgauge.scorers.json_schema_scorer import JsonSchemaScorer

SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": ["refund", "eta", "other"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "tags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["intent", "confidence"],
    "additionalProperties": False,
}
CASE = Case(index=0, input="q")


@pytest.fixture
def scorer(tmp_path: Path) -> JsonSchemaScorer:
    path = tmp_path / "schema.json"
    path.write_text(json.dumps(SCHEMA))
    return JsonSchemaScorer(path)


@pytest.mark.parametrize(
    "output",
    [
        '{"intent": "refund", "confidence": 0.9}',
        '  \n{"intent": "eta", "confidence": 0, "tags": []}\n ',
        'Here you go:\n```json\n{"intent": "other", "confidence": 1}\n```',
        '```\n{"intent": "refund", "confidence": 0.5, "tags": ["late"]}\n```\nThanks!',
        '```JSON\n{"intent":"eta","confidence":0.25}```',
    ],
)
async def test_positive(scorer: JsonSchemaScorer, output: str) -> None:
    result = await scorer.score(CASE, output)
    assert (result.score, result.reason) == (1.0, None)


@pytest.mark.parametrize(
    ("output", "reason"),
    [
        ("Sure! A refund is on its way.", "output is not valid JSON"),
        ('{"intent": "refund"', "output is not valid JSON"),
        ('{"intent": "refund"}', "$: 'confidence' is a required property"),
        ('{"intent": "cancel", "confidence": 0.5}', "intent: 'cancel' is not one of"),
        ('{"intent": "refund", "confidence": 1.5}', "confidence: 1.5 is greater than the maximum"),
        ('{"intent": "refund", "confidence": 0.5, "tags": ["a", 2]}', "tags/1: 2 is not of type"),
        ('{"intent": "refund", "confidence": 0.5, "extra": 1}', "$: Additional properties"),
        ('["refund"]', "$: ['refund'] is not of type 'object'"),
        ("null", "$: None is not of type 'object'"),
        ('```json\n{"intent": "refund"}\n```', "$: 'confidence' is a required property"),
    ],
)
async def test_negative(scorer: JsonSchemaScorer, output: str, reason: str) -> None:
    result = await scorer.score(CASE, output)
    assert result.score == 0.0
    assert result.reason is not None and result.reason.startswith(reason)


def test_applies_to_every_case_and_key_uses_file_name(scorer: JsonSchemaScorer) -> None:
    assert scorer.applies_to(CASE) is True
    assert scorer.key == "json_schema:schema.json"


def test_missing_schema_file(tmp_path: Path) -> None:
    with pytest.raises(ScorerError, match="cannot read"):
        JsonSchemaScorer(tmp_path / "nope.json")


def test_schema_file_not_json(tmp_path: Path) -> None:
    path = tmp_path / "schema.json"
    path.write_text("{not json")
    with pytest.raises(ScorerError, match="not valid JSON"):
        JsonSchemaScorer(path)


def test_schema_must_be_an_object(tmp_path: Path) -> None:
    path = tmp_path / "schema.json"
    path.write_text("[1, 2]")
    with pytest.raises(ScorerError, match="must contain a JSON object"):
        JsonSchemaScorer(path)


def test_invalid_schema(tmp_path: Path) -> None:
    path = tmp_path / "schema.json"
    path.write_text('{"type": "not-a-type"}')
    with pytest.raises(ScorerError, match="not a valid schema"):
        JsonSchemaScorer(path)
