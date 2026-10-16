"""Logger: thin wrapper over the standard library that never lets an API key reach the output."""

import logging
import re
import sys
from typing import Any

# Anthropic keys all start with this prefix; masking the pattern keeps a stray key out of logs
# even when a caller formats it into a message by mistake.
_KEY_PATTERN = re.compile(r"sk-ant-[A-Za-z0-9_\-]+")
_MASK = "sk-ant-***"


class Logger:
    """Structured-ish logging: `message key=value ...` lines on stderr.

    Prompt and case text may be logged only through `debug()`; API keys are masked in every
    level by `_redact()`.
    """

    def __init__(self, name: str = "promptgauge", level: str = "INFO") -> None:
        self._log = logging.getLogger(name)
        self._log.setLevel(level.upper())
        # Attach the handler once per logger name so repeated construction does not duplicate
        # output.
        if not self._log.handlers:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
            self._log.addHandler(handler)
            self._log.propagate = False

    def debug(self, message: str, **fields: Any) -> None:
        """Verbose detail; the only level allowed to carry prompt or case text."""
        self._log.debug(self._format(message, fields))

    def info(self, message: str, **fields: Any) -> None:
        """Progress a user wants to see."""
        self._log.info(self._format(message, fields))

    def warning(self, message: str, **fields: Any) -> None:
        """Something degraded but the run continues."""
        self._log.warning(self._format(message, fields))

    def error(self, message: str, **fields: Any) -> None:
        """Something failed."""
        self._log.error(self._format(message, fields))

    def _format(self, message: str, fields: dict[str, Any]) -> str:
        parts = [message] + [f"{key}={value}" for key, value in fields.items()]
        return self._redact(" ".join(parts))

    @staticmethod
    def _redact(text: str) -> str:
        return _KEY_PATTERN.sub(_MASK, text)
