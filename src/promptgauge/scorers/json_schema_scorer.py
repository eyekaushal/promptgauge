"""JsonSchemaScorer: parse output as JSON (tolerate a fenced block), validate with jsonschema. PRD
F3.2.
"""

import json
from pathlib import Path
from typing import Any

from jsonschema.exceptions import SchemaError
from jsonschema.validators import validator_for

from promptgauge.core.errors import ScorerError
from promptgauge.dataset.case import Case
from promptgauge.scorers.score_result import ScoreResult
from promptgauge.scorers.scorer import NOT_JSON, Scorer, parse_json


class JsonSchemaScorer(Scorer):
    """1.0 if the output is JSON that validates against the schema file, else 0.0 with the first
    validation error as the reason. Applies to every case; the schema is fixed per scorer."""

    def __init__(self, schema_path: Path | str) -> None:
        self._path = Path(schema_path)
        schema = self._read_schema(self._path)
        validator_class = validator_for(schema)
        try:
            validator_class.check_schema(schema)
        except SchemaError as exc:
            raise ScorerError(
                f"json_schema: {self._path} is not a valid schema: {exc.message}"
            ) from exc
        self._validator = validator_class(schema)

    @property
    def key(self) -> str:
        return f"json_schema:{self._path.name}"

    async def score(self, case: Case, output: str) -> ScoreResult:
        data = parse_json(output)
        if data is NOT_JSON:
            return ScoreResult(score=0.0, reason="output is not valid JSON")
        error = next(iter(self._validator.iter_errors(data)), None)
        if error is None:
            return ScoreResult(score=1.0)
        path = "/".join(str(part) for part in error.absolute_path) or "$"
        return ScoreResult(score=0.0, reason=f"{path}: {error.message}")

    @staticmethod
    def _read_schema(path: Path) -> dict[str, Any]:
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ScorerError(f"json_schema: cannot read {path}: {exc.strerror}") from exc
        except json.JSONDecodeError as exc:
            raise ScorerError(f"json_schema: {path} is not valid JSON: {exc.msg}") from exc
        if not isinstance(schema, dict):
            raise ScorerError(f"json_schema: {path} must contain a JSON object")
        return schema
