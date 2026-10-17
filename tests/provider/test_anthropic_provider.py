"""AnthropicProvider against a stub client: the SDK is imported, the network is never touched."""

from types import SimpleNamespace
from typing import Any

import anthropic
import httpx2
import pytest

from promptgauge.config.pricing import Pricing
from promptgauge.core.errors import ProviderError
from promptgauge.core.logger import Logger
from promptgauge.provider.anthropic_provider import AnthropicProvider

MODEL = "claude-sonnet-4-5"


def _message(blocks: list[Any], input_tokens: int = 100, output_tokens: int = 50, stop="end_turn"):
    return SimpleNamespace(
        content=blocks,
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
        stop_reason=stop,
    )


class StubMessages:
    def __init__(self, outcome: Any) -> None:
        self._outcome = outcome
        self.kwargs: dict[str, Any] | None = None

    async def create(self, **kwargs: Any) -> Any:
        self.kwargs = kwargs
        if isinstance(self._outcome, Exception):
            raise self._outcome
        return self._outcome


def _provider(outcome: Any) -> tuple[AnthropicProvider, StubMessages]:
    messages = StubMessages(outcome)
    client = SimpleNamespace(messages=messages)
    return AnthropicProvider(client, Pricing(), Logger("test")), messages  # type: ignore[arg-type]


def _status_error(status: int, message: str) -> anthropic.APIStatusError:
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx2.Response(status, request=request)
    return anthropic.APIStatusError(message, response=response, body=None)


async def test_sends_one_plain_user_turn_and_prices_the_usage() -> None:
    text = SimpleNamespace(type="text", text="Refund issued.")
    provider, messages = _provider(_message([text], 1000, 200))
    completion = await provider.complete("Be kind.", "My order is late", MODEL, 0.7, 1024)

    assert messages.kwargs == {
        "model": MODEL,
        "max_tokens": 1024,
        "temperature": 0.7,
        "system": "Be kind.",
        "messages": [{"role": "user", "content": "My order is late"}],
    }
    assert completion.text == "Refund issued."
    assert (completion.input_tokens, completion.output_tokens) == (1000, 200)
    assert completion.cost_usd == pytest.approx(Pricing().cost(MODEL, 1000, 200))


async def test_joins_text_blocks_and_skips_other_block_types() -> None:
    blocks = [
        SimpleNamespace(type="thinking", thinking="..."),
        SimpleNamespace(type="text", text="A"),
        SimpleNamespace(type="text", text="B"),
    ]
    provider, _ = _provider(_message(blocks))
    assert (await provider.complete("s", "u", MODEL, 0.0, 64)).text == "AB"


async def test_refusal_returns_the_text_it_got() -> None:
    provider, _ = _provider(_message([], stop="refusal"))
    assert (await provider.complete("s", "u", MODEL, 0.0, 64)).text == ""


async def test_unknown_model_fails_before_any_call() -> None:
    provider, messages = _provider(_message([]))
    with pytest.raises(ProviderError, match="unknown model"):
        await provider.complete("s", "u", "claude-nope", 0.0, 64)
    assert messages.kwargs is None


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (_status_error(429, "rate limited"), f"model {MODEL}: HTTP 429: rate limited"),
        (_status_error(529, "overloaded"), f"model {MODEL}: HTTP 529: overloaded"),
        (_status_error(400, "bad request"), f"model {MODEL}: HTTP 400: bad request"),
        (
            anthropic.APIConnectionError(
                request=httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
            ),
            f"model {MODEL}: connection failed: Connection error.",
        ),
        (anthropic.AnthropicError("no key"), f"model {MODEL}: no key"),
    ],
)
async def test_sdk_failures_become_provider_errors(error: Exception, expected: str) -> None:
    provider, _ = _provider(error)
    with pytest.raises(ProviderError) as info:
        await provider.complete("s", "u", MODEL, 0.0, 64)
    assert str(info.value) == expected
    assert info.value.__cause__ is error
