"""FakeProvider: scripted outputs keyed by system/user text for tests; records every call."""

from dataclasses import dataclass

from promptgauge.config.pricing import Pricing
from promptgauge.core.errors import ProviderError
from promptgauge.provider.completion import Completion


@dataclass(frozen=True)
class FakeCall:
    """One recorded complete() invocation."""

    system: str
    user: str
    model: str
    temperature: float
    max_tokens: int


class FakeProvider:
    """Deterministic stand-in for AnthropicProvider.

    `outputs` maps a user text (or a `(system, user)` pair, which wins) to the reply; anything
    else gets `default`. `errors` maps a user text to a message raised as ProviderError. Token
    counts are character counts divided by four so costs are non-zero and reproducible.
    """

    def __init__(
        self,
        outputs: dict[str | tuple[str, str], str] | None = None,
        *,
        default: str = "ok",
        errors: dict[str, str] | None = None,
        pricing: Pricing | None = None,
    ) -> None:
        self._outputs = dict(outputs or {})
        self._default = default
        self._errors = dict(errors or {})
        self._pricing = pricing or Pricing()
        self.calls: list[FakeCall] = []

    async def complete(
        self, system: str, user: str, model: str, temperature: float, max_tokens: int
    ) -> Completion:
        """Record the call and return the scripted reply."""
        self._pricing.require(model)
        self.calls.append(FakeCall(system, user, model, temperature, max_tokens))
        if user in self._errors:
            raise ProviderError(f"model {model}: {self._errors[user]}")
        text = self._outputs.get((system, user), self._outputs.get(user, self._default))
        input_tokens = max(1, (len(system) + len(user)) // 4)
        output_tokens = max(1, len(text) // 4)
        return Completion(
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=self._pricing.cost(model, input_tokens, output_tokens),
        )
