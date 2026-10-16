"""Pricing: USD per million tokens by model id, dated. Unknown ids fail before any call."""

from datetime import date

from promptgauge.core.errors import ProviderError

# Checked against https://platform.claude.com/docs/en/about-claude/pricing on CHECKED_ON.
# Base input and output rates only: no cache tiers, no batch discount. Haiku 5.5 is listed at
# its rate for prompts up to 100K tokens; promptgauge prompts are far smaller than that.
CHECKED_ON = date(2026, 10, 17)

_TABLE: dict[str, tuple[float, float]] = {
    "claude-fable-5-1": (10.00, 50.00),
    "claude-fable-5": (10.00, 50.00),
    "claude-opus-5-5": (4.00, 20.00),
    "claude-opus-5": (5.00, 25.00),
    "claude-opus-4-8": (5.00, 25.00),
    "claude-opus-4-7": (5.00, 25.00),
    "claude-opus-4-6": (5.00, 25.00),
    "claude-opus-4-5": (5.00, 25.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-sonnet-5": (2.00, 10.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-sonnet-4-5": (3.00, 15.00),
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-haiku-4-5": (1.00, 5.00),
}


class Pricing:
    """Look up prices and compute the cost of a call."""

    def __init__(self, table: dict[str, tuple[float, float]] | None = None) -> None:
        self._table = dict(_TABLE if table is None else table)

    @property
    def checked_on(self) -> date:
        """The day the built-in table was last verified against the pricing page."""
        return CHECKED_ON

    def models(self) -> list[str]:
        """Known model ids, in table order."""
        return list(self._table)

    def require(self, model: str) -> None:
        """Raise ProviderError if the model has no known price."""
        if model not in self._table:
            known = ", ".join(self._table)
            raise ProviderError(f"unknown model '{model}'; known models: {known}")

    def input_per_million(self, model: str) -> float:
        """USD per million input tokens."""
        self.require(model)
        return self._table[model][0]

    def output_per_million(self, model: str) -> float:
        """USD per million output tokens."""
        self.require(model)
        return self._table[model][1]

    def cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """USD for one call."""
        self.require(model)
        in_rate, out_rate = self._table[model]
        return (input_tokens * in_rate + output_tokens * out_rate) / 1_000_000
