"""Config: the validated contents of promptgauge.yaml. Fields in PRD F1.1."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from promptgauge.config.scorer_spec import ScorerSpec
from promptgauge.core.errors import ConfigError


class Config(BaseModel):
    """Everything a run needs. Paths are absolute once loaded through `load()`."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    prompt: Path
    dataset: Path
    model: str = Field(min_length=1)
    judge: str = Field(default="claude-haiku-4-5", min_length=1)
    scorers: list[ScorerSpec] = Field(min_length=1)
    repeats: int = Field(default=3, ge=1)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    budget_usd: float = Field(default=2.00, gt=0.0)
    delta: float = Field(default=0.03, ge=0.0)
    concurrency: int = Field(default=8, ge=1)
    inr_rate: float = Field(default=84.0, gt=0.0)

    @field_validator("scorers", mode="before")
    @classmethod
    def _parse_scorers(cls, value: Any) -> Any:
        if not isinstance(value, list):
            raise ValueError("must be a list")
        return [
            entry if isinstance(entry, ScorerSpec) else ScorerSpec.parse(entry) for entry in value
        ]

    @classmethod
    def load(cls, path: Path | str) -> "Config":
        """Read and validate a YAML file; relative paths resolve against the file's directory.

        Raises ConfigError with a one-line message naming the field for every failure.
        """
        config_path = Path(path)
        if not config_path.is_file():
            raise ConfigError(f"config file not found: {config_path}")
        try:
            data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ConfigError(f"{config_path}: not valid YAML: {exc}") from exc
        if not isinstance(data, dict):
            raise ConfigError(f"{config_path}: top level must be a mapping of fields")

        base = config_path.resolve().parent
        for field in ("prompt", "dataset"):
            if isinstance(data.get(field), str):
                data[field] = str(base / data[field])
        data["scorers"] = cls._resolve_scorer_paths(data.get("scorers"), base)

        try:
            config = cls.model_validate(data)
        except ValidationError as exc:
            raise ConfigError(cls._describe(exc)) from exc

        for field in ("prompt", "dataset"):
            file = getattr(config, field)
            if not file.is_file():
                raise ConfigError(f"{field}: file not found: {file}")
        for spec in config.scorers:
            if spec.name == "json_schema" and not Path(spec.arg or "").is_file():
                raise ConfigError(f"scorers: json_schema file not found: {spec.arg}")
        return config

    @staticmethod
    def _resolve_scorer_paths(entries: Any, base: Path) -> Any:
        # json_schema always carries a path. A rubric value is a built-in name unless a file of
        # that name sits next to the config, in which case it is a custom rubric path.
        if not isinstance(entries, list):
            return entries
        resolved = []
        for entry in entries:
            if isinstance(entry, dict) and len(entry) == 1:
                (name, arg), *_ = entry.items()
                if isinstance(arg, str) and (
                    name == "json_schema" or (name == "rubric" and (base / arg).is_file())
                ):
                    entry = {name: str(base / arg)}
            resolved.append(entry)
        return resolved

    @staticmethod
    def _describe(exc: ValidationError) -> str:
        lines = []
        for error in exc.errors():
            field = ".".join(str(part) for part in error["loc"]) or "config"
            message = error["msg"].removeprefix("Value error, ")
            lines.append(f"{field}: {message}")
        return "; ".join(lines)
