"""Provider: the one-method interface AnthropicProvider and FakeProvider both satisfy."""

from typing import Protocol

from promptgauge.provider.completion import Completion


class Provider(Protocol):
    """Anything CallCache can ask for a completion."""

    async def complete(
        self, system: str, user: str, model: str, temperature: float, max_tokens: int
    ) -> Completion:
        """One system + user turn in, one Completion out."""
        ...
