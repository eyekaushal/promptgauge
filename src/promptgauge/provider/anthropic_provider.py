"""AnthropicProvider: the only class that talks to the network. One complete() method. PRD
F2.1–F2.3.
"""

import anthropic

from promptgauge.config.pricing import Pricing
from promptgauge.core.errors import ProviderError
from promptgauge.core.logger import Logger
from promptgauge.provider.completion import Completion


class AnthropicProvider:
    """Plain text in, plain text out. No tools, no streaming, no prefill (PRD §14).

    Retries and timeouts belong to the client (built with `max_retries=3` in the composition
    root); 429 and 529 back off there. Anything that still fails becomes a ProviderError.
    Cost is computed from `Pricing`, not from the response, so FakeProvider reports the same way.
    """

    def __init__(self, client: anthropic.AsyncAnthropic, pricing: Pricing, logger: Logger) -> None:
        self._client = client
        self._pricing = pricing
        self._log = logger

    async def complete(
        self, system: str, user: str, model: str, temperature: float, max_tokens: int
    ) -> Completion:
        """Call the Messages API once. Raises ProviderError for an unknown model or any failure."""
        self._pricing.require(model)
        try:
            message = await self._client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
        except anthropic.APIStatusError as exc:
            raise ProviderError(f"model {model}: HTTP {exc.status_code}: {exc.message}") from exc
        except anthropic.APIConnectionError as exc:
            raise ProviderError(f"model {model}: connection failed: {exc.message}") from exc
        except anthropic.AnthropicError as exc:
            raise ProviderError(f"model {model}: {exc}") from exc

        text = "".join(block.text for block in message.content if block.type == "text")
        if message.stop_reason == "refusal":
            # Not an error: a refused output is a real, scoreable outcome of the prompt.
            self._log.warning("model refused", model=model)
        usage = message.usage
        return Completion(
            text=text,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cost_usd=self._pricing.cost(model, usage.input_tokens, usage.output_tokens),
        )
