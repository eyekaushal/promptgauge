import pytest

from promptgauge.config.pricing import Pricing
from promptgauge.core.errors import ProviderError
from promptgauge.provider.fake_provider import FakeCall, FakeProvider

MODEL = "claude-sonnet-4-5"


async def test_scripted_output_by_user_text_and_default() -> None:
    provider = FakeProvider({"hi": "hello"}, default="dunno")
    assert (await provider.complete("sys", "hi", MODEL, 0.7, 64)).text == "hello"
    assert (await provider.complete("sys", "other", MODEL, 0.7, 64)).text == "dunno"


async def test_system_user_pair_wins_over_user_text() -> None:
    provider = FakeProvider({"hi": "generic", ("strict", "hi"): "specific"})
    assert (await provider.complete("strict", "hi", MODEL, 0.7, 64)).text == "specific"
    assert (await provider.complete("loose", "hi", MODEL, 0.7, 64)).text == "generic"


async def test_records_every_call_in_order() -> None:
    provider = FakeProvider()
    await provider.complete("s", "a", MODEL, 0.0, 10)
    await provider.complete("s", "b", MODEL, 1.0, 20)
    assert provider.calls == [
        FakeCall("s", "a", MODEL, 0.0, 10),
        FakeCall("s", "b", MODEL, 1.0, 20),
    ]


async def test_tokens_and_cost_come_from_pricing() -> None:
    provider = FakeProvider({"u" * 40: "o" * 20})
    completion = await provider.complete("s" * 40, "u" * 40, MODEL, 0.7, 64)
    assert (completion.input_tokens, completion.output_tokens) == (20, 5)
    assert completion.cost_usd == pytest.approx(Pricing().cost(MODEL, 20, 5))
    assert completion.cost_usd > 0
    assert completion.cached is False


async def test_scripted_error_is_a_provider_error_and_is_recorded() -> None:
    provider = FakeProvider(errors={"boom": "overloaded"})
    with pytest.raises(ProviderError, match=f"model {MODEL}: overloaded"):
        await provider.complete("s", "boom", MODEL, 0.7, 64)
    assert len(provider.calls) == 1


async def test_unknown_model_fails_before_recording() -> None:
    provider = FakeProvider()
    with pytest.raises(ProviderError, match="unknown model"):
        await provider.complete("s", "u", "gpt-9", 0.7, 64)
    assert provider.calls == []
