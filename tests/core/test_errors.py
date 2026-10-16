import pytest

from promptgauge.core.errors import (
    BudgetExceededError,
    ConfigError,
    DatasetError,
    PromptgaugeError,
    ProviderError,
    ScorerError,
)


@pytest.mark.parametrize(
    "error", [ConfigError, DatasetError, ProviderError, BudgetExceededError, ScorerError]
)
def test_every_error_is_a_promptgauge_error(error: type[Exception]) -> None:
    assert issubclass(error, PromptgaugeError)
    with pytest.raises(PromptgaugeError, match="boom"):
        raise error("boom")
