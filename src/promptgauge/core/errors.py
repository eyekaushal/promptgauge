"""Typed errors. Every error promptgauge raises on purpose derives from PromptgaugeError."""


class PromptgaugeError(Exception):
    """Base class for all promptgauge errors; the CLI turns these into one-line messages."""


class ConfigError(PromptgaugeError):
    """promptgauge.yaml is missing, malformed, or names a value that cannot work."""


class DatasetError(PromptgaugeError):
    """cases.jsonl is missing or has a bad line; the message carries the line number."""


class ProviderError(PromptgaugeError):
    """A model call failed, or the model id has no known price."""


class BudgetExceededError(PromptgaugeError):
    """The estimate exceeds budget_usd, or real spend crossed it during a run."""


class ScorerError(PromptgaugeError):
    """A scorer was misconfigured (unknown name, missing rubric, unreadable schema)."""


class AblationError(PromptgaugeError):
    """An ablation could not measure a variant: every case failed, nothing to compare."""


class PromptError(PromptgaugeError):
    """A segment was applied to prompt text it was not cut from (offsets or text do not match)."""
