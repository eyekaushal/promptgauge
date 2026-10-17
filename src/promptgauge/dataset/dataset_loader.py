"""DatasetLoader: cases.jsonl → list[Case] plus the dataset hash; errors carry the line number."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from promptgauge.core.errors import DatasetError
from promptgauge.dataset.case import Case


@dataclass(frozen=True)
class Dataset:
    """The loaded cases and the SHA-256 that identifies them (PRD F1.3)."""

    path: Path
    hash: str
    cases: list[Case]


class DatasetLoader:
    """Read a JSONL dataset: one object per non-empty line, every line validated as a Case."""

    def load(self, path: Path | str) -> Dataset:
        """Load and hash the file. Raises DatasetError naming the file and the 1-based line."""
        dataset_path = Path(path)
        if not dataset_path.is_file():
            raise DatasetError(f"dataset file not found: {dataset_path}")
        try:
            text = dataset_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise DatasetError(f"{dataset_path}: not UTF-8 text: {exc}") from exc

        cases: list[Case] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            cases.append(self._parse_line(dataset_path, line_number, line, len(cases)))
        if not cases:
            raise DatasetError(f"{dataset_path}: dataset has no cases")
        return Dataset(path=dataset_path, hash=self.hash_cases(cases), cases=cases)

    @staticmethod
    def hash_cases(cases: list[Case]) -> str:
        """SHA-256 of the normalised dataset: canonical JSON per case, one per line.

        Whitespace, key order, blank lines and a trailing newline in the file do not change
        the hash; any change to a case's content does.
        """
        digest = hashlib.sha256()
        for case in cases:
            payload = json.dumps(
                case.model_dump(), sort_keys=True, separators=(",", ":"), ensure_ascii=False
            )
            digest.update(payload.encode("utf-8"))
            digest.update(b"\n")
        return digest.hexdigest()

    @staticmethod
    def _parse_line(path: Path, line_number: int, line: str, index: int) -> Case:
        try:
            data = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DatasetError(f"{path}:{line_number}: not valid JSON: {exc.msg}") from exc
        if not isinstance(data, dict):
            raise DatasetError(f"{path}:{line_number}: each line must be a JSON object")
        if "index" in data:
            raise DatasetError(f"{path}:{line_number}: 'index' is assigned by position, remove it")
        try:
            return Case(index=index, **data)
        except ValidationError as exc:
            raise DatasetError(f"{path}:{line_number}: {_describe(exc)}") from exc
        except TypeError as exc:
            # A non-string key like {"1": ...} cannot be passed as a keyword argument.
            raise DatasetError(f"{path}:{line_number}: field names must be strings") from exc


def _describe(exc: ValidationError) -> str:
    parts = []
    for error in exc.errors():
        field = ".".join(str(part) for part in error["loc"]) or "row"
        parts.append(f"{field}: {error['msg'].removeprefix('Value error, ')}")
    return "; ".join(parts)
