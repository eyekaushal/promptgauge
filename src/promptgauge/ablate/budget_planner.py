"""BudgetPlanner: estimate before the first call, refuse over budget with three suggestions, stop a
running ablation at the budget. PRD F6.2.
"""

import math
from collections import Counter

from promptgauge.ablate.budget_estimate import BudgetEstimate
from promptgauge.config.pricing import Pricing
from promptgauge.core.errors import BudgetExceededError
from promptgauge.dataset.case import Case

# Token guesses for the parts no tokenizer can see before the run. Tuned at B12 against a real
# bill; the F6.2 target is an estimate within 25% of what is spent.
EXPECTED_OUTPUT_TOKENS = 300
JUDGE_PROMPT_TOKENS = 400
JUDGE_OUTPUT_TOKENS = 150
RED_BLOCK_SHARE = 0.30


class BudgetPlanner:
    """Price an ablation before it starts and police it while it runs (invariant 3).

    Cost = target calls × (prompt + mean case + expected output tokens) × target price, plus one
    judge call per judge scorer per output. Calls cover stage one, stage two at `RED_BLOCK_SHARE`
    of the candidate lines, and the confirmation run of the cut prompt (F6.7).
    """

    def __init__(self, pricing: Pricing, budget_usd: float) -> None:
        if budget_usd <= 0.0:
            raise ValueError("budget_usd must be positive")
        self._pricing = pricing
        self._budget = budget_usd

    @property
    def budget_usd(self) -> float:
        """The ceiling in USD."""
        return self._budget

    def estimate(
        self,
        *,
        model: str,
        judge: str,
        judge_scorers: int,
        prompt_tokens: int,
        cases: list[Case],
        repeats: int,
        stage_one_variants: int,
        stage_two_candidates: int,
    ) -> BudgetEstimate:
        """Price the whole ablation. Over budget, the estimate carries three suggestions."""
        self._pricing.require(model)
        self._pricing.require(judge)
        variants = self._variants(stage_one_variants, stage_two_candidates)
        estimate = self._price(model, judge, judge_scorers, prompt_tokens, cases, repeats, variants)
        if estimate.within_budget:
            return estimate
        suggestions = [
            self._fewer_repeats(
                model, judge, judge_scorers, prompt_tokens, cases, repeats, variants
            ),
            self._fewer_cases(model, judge, judge_scorers, prompt_tokens, cases, repeats, variants),
            self._cheaper_model(
                model, judge, judge_scorers, prompt_tokens, cases, repeats, variants
            ),
        ]
        return BudgetEstimate(
            estimate.calls, estimate.judge_calls, estimate.cost_usd, self._budget, suggestions
        )

    def require_within_budget(self, estimate: BudgetEstimate) -> None:
        """Raise BudgetExceededError, message ready for the terminal, when the estimate is over."""
        if estimate.within_budget:
            return
        lines = [
            f"estimate ${estimate.cost_usd:.2f} exceeds budget ${estimate.budget_usd:.2f} "
            f"({estimate.calls:,} calls); nothing was called",
            *(f"  - {s}" for s in estimate.suggestions),
        ]
        raise BudgetExceededError("\n".join(lines))

    def exceeded(self, spend_usd: float) -> bool:
        """True once real spend has crossed the budget; the caller stops and writes `stopped:
        budget` (F6.2)."""
        return spend_usd >= self._budget

    @staticmethod
    def _variants(stage_one: int, stage_two_candidates: int) -> int:
        # +1 is the confirmation run of the cut prompt.
        return stage_one + math.ceil(stage_two_candidates * RED_BLOCK_SHARE) + 1

    def _price(
        self,
        model: str,
        judge: str,
        judge_scorers: int,
        prompt_tokens: int,
        cases: list[Case],
        repeats: int,
        variants: int,
    ) -> BudgetEstimate:
        calls = variants * len(cases) * repeats
        judge_calls = calls * judge_scorers
        if not cases:
            return BudgetEstimate(0, 0, 0.0, self._budget)
        mean_case = sum(self._case_tokens(c) for c in cases) / len(cases)
        per_call = self._pricing.cost(
            model, round(prompt_tokens + mean_case), EXPECTED_OUTPUT_TOKENS
        )
        per_judge = self._pricing.cost(
            judge,
            round(JUDGE_PROMPT_TOKENS + mean_case + EXPECTED_OUTPUT_TOKENS),
            JUDGE_OUTPUT_TOKENS,
        )
        cost = calls * per_call + judge_calls * per_judge
        return BudgetEstimate(calls, judge_calls, cost, self._budget)

    def _fewer_repeats(
        self,
        model: str,
        judge: str,
        judge_scorers: int,
        prompt_tokens: int,
        cases: list[Case],
        repeats: int,
        variants: int,
    ) -> str:
        for r in range(repeats - 1, 0, -1):
            cost = self._price(model, judge, judge_scorers, prompt_tokens, cases, r, variants)
            if cost.within_budget:
                return f"repeats: {r} brings the estimate to ≈ ${cost.cost_usd:.2f}"
        floor = self._price(model, judge, judge_scorers, prompt_tokens, cases, 1, variants)
        return f"even repeats: 1 is ≈ ${floor.cost_usd:.2f}, still over budget"

    def _fewer_cases(
        self,
        model: str,
        judge: str,
        judge_scorers: int,
        prompt_tokens: int,
        cases: list[Case],
        repeats: int,
        variants: int,
    ) -> str:
        # The largest tagged subset that fits is the least loss of coverage.
        tags = Counter(tag for case in cases for tag in case.tags)
        for tag, _ in tags.most_common():
            subset = [c for c in cases if tag in c.tags]
            if len(subset) == len(cases):
                continue
            cost = self._price(
                model, judge, judge_scorers, prompt_tokens, subset, repeats, variants
            )
            if cost.within_budget:
                return (
                    f"only the {len(subset)} cases tagged '{tag}' bring the estimate to "
                    f"≈ ${cost.cost_usd:.2f}"
                )
        for n in range(len(cases) - 1, 0, -1):
            cost = self._price(
                model, judge, judge_scorers, prompt_tokens, cases[:n], repeats, variants
            )
            if cost.within_budget:
                return (
                    f"{n} cases instead of {len(cases)} bring the estimate to "
                    f"≈ ${cost.cost_usd:.2f}"
                )
        return "no smaller dataset fits with these settings"

    def _cheaper_model(
        self,
        model: str,
        judge: str,
        judge_scorers: int,
        prompt_tokens: int,
        cases: list[Case],
        repeats: int,
        variants: int,
    ) -> str:
        current = self._pricing.input_per_million(model)
        cheaper = sorted(
            (m for m in self._pricing.models() if self._pricing.input_per_million(m) < current),
            key=self._pricing.input_per_million,
            reverse=True,
        )
        for candidate in cheaper:
            cost = self._price(
                candidate, judge, judge_scorers, prompt_tokens, cases, repeats, variants
            )
            if cost.within_budget:
                return f"model: {candidate} brings the estimate to ≈ ${cost.cost_usd:.2f}"
        return "no cheaper target model fits with these settings"

    @staticmethod
    def _case_tokens(case: Case) -> int:
        # Same len/4 rule as the segmenter's offline estimate.
        return max(1, (len(case.input) + len(case.context or "")) // 4)
