"""JsonSchemaScorer: parse output as JSON (tolerate a fenced block), validate with jsonschema. PRD
F3.2.
"""

import json
import re
from pathlib import Path
from typing import Any

from jsonschema.exceptions import SchemaError
from jsonschema.validators import validator_for

from promptgauge.core.errors import ScorerError
from promptgauge.dataset.case import Case
from promptgauge.scorers.score_result import ScoreResult
from promptgauge.scorers.scorer import Scorer

# A ```json ... ``` or ``` ... ``` block anywhere in the output; the first one is used.
_FENCE = re.compile(r"```(?:json)?\s*\n?(.*?)```", re.DOTALL | re.IGNORECASE)


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
        data = self._parse(output)
        if data is _NOT_JSON:
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

    @staticmethod
    def _parse(output: str) -> Any:
        candidates = [output.strip()] + [m.group(1).strip() for m in _FENCE.finditer(output)]
        for candidate in candidates:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
        return _NOT_JSON


# Sentinel: `None` is valid JSON (`null`), so a failed parse needs its own marker.
_NOT_JSON = object()
