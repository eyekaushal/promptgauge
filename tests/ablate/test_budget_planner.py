import pytest

from promptgauge.ablate.budget_planner import (
    EXPECTED_OUTPUT_TOKENS,
    JUDGE_OUTPUT_TOKENS,
    JUDGE_PROMPT_TOKENS,
    BudgetPlanner,
)
from promptgauge.config.pricing import Pricing
from promptgauge.core.errors import BudgetExceededError
from promptgauge.dataset.case import Case

# Round prices so the arithmetic in the tests stays readable: USD per million (input, output).
PRICING = Pricing(
    {
        "big": (10.0, 50.0),
        "mid": (2.0, 10.0),
        "small": (1.0, 5.0),
        "judge": (1.0, 5.0),
    }
)


def cases(n: int, tags: list[list[str]] | None = None) -> list[Case]:
    # 40-character inputs: 10 tokens each by the len/4 rule.
    return [Case(index=i, input="x" * 40, tags=(tags[i] if tags else [])) for i in range(n)]


def estimate(planner: BudgetPlanner, **overrides: object):
    params: dict[str, object] = {
        "model": "mid",
        "judge": "judge",
        "judge_scorers": 0,
        "prompt_tokens": 1000,
        "cases": cases(10),
        "repeats": 3,
        "stage_one_variants": 5,
        "stage_two_candidates": 10,
    }
    params.update(overrides)
    return planner.estimate(**params)  # type: ignore[arg-type]


def test_calls_cover_stage_one_stage_two_at_30_percent_and_confirmation() -> None:
    # variants = 5 (stage one) + ceil(10 × 0.3) = 3 (stage two) + 1 (confirmation) = 9
    est = estimate(BudgetPlanner(PRICING, 100.0))
    assert est.calls == 9 * 10 * 3
    assert est.judge_calls == 0


def test_cost_is_calls_times_per_call_price() -> None:
    est = estimate(BudgetPlanner(PRICING, 100.0))
    per_call = ((1000 + 10) * 2.0 + EXPECTED_OUTPUT_TOKENS * 10.0) / 1_000_000
    assert est.cost_usd == pytest.approx(270 * per_call)
    assert est.within_budget and est.suggestions == []


def test_judge_scorers_add_one_judge_call_per_output_each() -> None:
    est = estimate(BudgetPlanner(PRICING, 100.0), judge_scorers=2)
    assert est.judge_calls == 2 * 270
    per_call = ((1000 + 10) * 2.0 + EXPECTED_OUTPUT_TOKENS * 10.0) / 1_000_000
    per_judge = (
        (JUDGE_PROMPT_TOKENS + 10 + EXPECTED_OUTPUT_TOKENS) * 1.0 + JUDGE_OUTPUT_TOKENS * 5.0
    ) / 1_000_000
    assert est.cost_usd == pytest.approx(270 * per_call + 540 * per_judge)


def test_context_counts_toward_case_tokens() -> None:
    planner = BudgetPlanner(PRICING, 100.0)
    plain = estimate(planner)
    with_context = estimate(planner, cases=[Case(index=0, input="x" * 40, context="y" * 4000)] * 10)
    assert with_context.cost_usd > plain.cost_usd


def test_summary_line() -> None:
    est = estimate(BudgetPlanner(PRICING, 2.0))
    assert est.summary().startswith("~270 calls, ≈ $") and est.summary().endswith(" of $2.00")


def test_over_budget_carries_three_suggestions_and_require_raises() -> None:
    planner = BudgetPlanner(PRICING, 0.5)
    est = estimate(planner, model="big", judge_scorers=1)
    assert not est.within_budget
    assert len(est.suggestions) == 3
    with pytest.raises(BudgetExceededError) as info:
        planner.require_within_budget(est)
    message = str(info.value)
    assert message.startswith(f"estimate ${est.cost_usd:.2f} exceeds budget $0.50")
    assert "nothing was called" in message
    for suggestion in est.suggestions:
        assert suggestion in message


def test_require_within_budget_is_silent_when_it_fits() -> None:
    planner = BudgetPlanner(PRICING, 100.0)
    planner.require_within_budget(estimate(planner))


def test_fewer_repeats_suggestion_picks_the_largest_that_fits() -> None:
    # repeats=3 costs 270 × $0.00502 ≈ $1.36; 2 → ≈ $0.90; 1 → ≈ $0.45.
    est = estimate(BudgetPlanner(PRICING, 1.0))
    assert est.suggestions[0].startswith("repeats: 2 brings the estimate to ≈ $0.90")


def test_fewer_repeats_reports_when_even_one_is_over() -> None:
    est = estimate(BudgetPlanner(PRICING, 0.1))
    assert est.suggestions[0].startswith("even repeats: 1 is ≈ $0.45, still over budget")


def test_fewer_cases_prefers_the_largest_fitting_tag() -> None:
    tags = [["billing"]] * 6 + [["refund"]] * 3 + [["other"]]
    est = estimate(BudgetPlanner(PRICING, 1.0), cases=cases(10, tags))
    # 6 billing cases: 162 calls ≈ $0.81 fits; the full set (≈ $1.36) does not.
    assert est.suggestions[1] == "only the 6 cases tagged 'billing' bring the estimate to ≈ $0.81"


def test_fewer_cases_falls_back_to_a_count_without_tags() -> None:
    est = estimate(BudgetPlanner(PRICING, 1.0))
    # 7 cases: 189 calls ≈ $0.95 fits; 8 cases ≈ $1.08 does not.
    assert est.suggestions[1] == "7 cases instead of 10 bring the estimate to ≈ $0.95"


def test_fewer_cases_reports_when_nothing_fits() -> None:
    est = estimate(BudgetPlanner(PRICING, 0.001))
    assert est.suggestions[1] == "no smaller dataset fits with these settings"


def test_cheaper_model_picks_the_priciest_that_fits() -> None:
    est = estimate(BudgetPlanner(PRICING, 1.0), model="big")
    assert est.suggestions[2].startswith("model: small brings the estimate to ≈ $")


def test_cheaper_model_reports_when_none_fits() -> None:
    est = estimate(BudgetPlanner(PRICING, 0.001), model="big")
    assert est.suggestions[2] == "no cheaper target model fits with these settings"


def test_exceeded_tracks_real_spend() -> None:
    planner = BudgetPlanner(PRICING, 2.0)
    assert not planner.exceeded(1.99)
    assert planner.exceeded(2.0) and planner.exceeded(2.5)


def test_unknown_models_fail_before_any_arithmetic() -> None:
    from promptgauge.core.errors import ProviderError

    with pytest.raises(ProviderError):
        estimate(BudgetPlanner(PRICING, 2.0), model="nope")
    with pytest.raises(ProviderError):
        estimate(BudgetPlanner(PRICING, 2.0), judge="nope")


def test_non_positive_budget_is_rejected() -> None:
    with pytest.raises(ValueError):
        BudgetPlanner(PRICING, 0.0)
