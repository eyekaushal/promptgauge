from datetime import date

import pytest

from promptgauge.config.pricing import Pricing
from promptgauge.core.errors import ProviderError


def test_cost_uses_input_and_output_rates() -> None:
    pricing = Pricing()
    # Sonnet 4.5: $3 in, $15 out per million tokens.
    assert pricing.cost("claude-sonnet-4-5", 1_000_000, 0) == pytest.approx(3.0)
    assert pricing.cost("claude-sonnet-4-5", 0, 1_000_000) == pytest.approx(15.0)
    assert pricing.cost("claude-haiku-4-5", 2_000, 500) == pytest.approx(0.002 + 0.0025)
    assert pricing.cost("claude-haiku-4-5", 0, 0) == 0.0


def test_rates_are_exposed() -> None:
    pricing = Pricing()
    assert pricing.input_per_million("claude-haiku-4-5") == 1.0
    assert pricing.output_per_million("claude-haiku-4-5") == 5.0


@pytest.mark.parametrize("model", ["claude-sonnet-4-5", "claude-haiku-4-5", "claude-opus-5-5"])
def test_defaults_are_known(model: str) -> None:
    Pricing().require(model)


@pytest.mark.parametrize("method", ["require", "input_per_million", "output_per_million"])
def test_unknown_model_raises_before_any_call(method: str) -> None:
    with pytest.raises(ProviderError, match="unknown model 'gpt-9'"):
        getattr(Pricing(), method)("gpt-9")
    with pytest.raises(ProviderError, match="known models"):
        Pricing().cost("gpt-9", 1, 1)


def test_custom_table_and_date() -> None:
    pricing = Pricing({"fake": (1.0, 2.0)})
    assert pricing.models() == ["fake"]
    assert pricing.cost("fake", 1_000_000, 1_000_000) == 3.0
    assert isinstance(pricing.checked_on, date)
    with pytest.raises(ProviderError):
        pricing.require("claude-haiku-4-5")
