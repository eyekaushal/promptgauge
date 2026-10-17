"""BudgetEstimate: calls, judge calls, USD before the first call, and how to get under budget."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BudgetEstimate:
    """What `BudgetPlanner.estimate()` returns (PRD F6.2). `suggestions` is empty when the
    estimate fits; otherwise it holds the three cheapest ways under budget, ready to print."""

    calls: int
    judge_calls: int
    cost_usd: float
    budget_usd: float
    suggestions: list[str] = field(default_factory=list)

    @property
    def within_budget(self) -> bool:
        """True when the ablation may start."""
        return self.cost_usd <= self.budget_usd

    def summary(self) -> str:
        """One line for the CLI: `~1,240 calls, ≈ $1.60 of $2.00`."""
        return f"~{self.calls:,} calls, ≈ ${self.cost_usd:.2f} of ${self.budget_usd:.2f}"
