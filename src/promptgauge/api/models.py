"""Pydantic request and response models for every route. PRD §13.

Response models are built from repository rows; the one request model (`SettingsIn`) is what
`PUT /api/settings` validates, so bad input is a 422 before any write.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DatasetSummary(BaseModel):
    """One dataset hash with its case count and when it was first seen."""

    dataset_hash: str
    case_count: int
    first_seen: str


class CaseOut(BaseModel):
    """One stored case."""

    id: int
    dataset_hash: str
    index: int
    input: str
    expected: str | None
    context: str | None
    tags: list[str]


class Totals(BaseModel):
    """Call counts and spend summed from the call table (PRD F2.6)."""

    calls: int
    cached: int
    input_tokens: int
    output_tokens: int
    cost_usd: float


class CaseScore(BaseModel):
    """Baseline score of one case: mean over repeats, per scorer and overall."""

    case_id: int
    index: int
    input: str
    score: float | None
    scorer_means: dict[str, float | None]
    repeats: int


class ExperimentSummary(BaseModel):
    """One row of the runs table."""

    id: int
    kind: str
    name: str | None
    prompt_hash: str
    dataset_hash: str
    model: str
    judge: str
    status: str
    stopped_reason: str | None
    created_at: str
    finished_at: str | None
    score: float | None
    scorer_means: dict[str, float | None]
    cases: int
    totals: Totals


class ExperimentDetail(ExperimentSummary):
    """A run with its prompt, config and per-case baseline scores."""

    prompt_text: str
    config: dict[str, Any]
    repeats: int
    case_scores: list[CaseScore]


class ResultOut(BaseModel):
    """One result row (case, repeat, variant, scorer) with the output it scored."""

    case_id: int
    case_index: int
    repeat_index: int
    variant_id: int | None
    scorer: str
    score: float | None
    reason: str | None
    call_hash: str
    output: str | None


class CompareCase(BaseModel):
    """One case side by side: baseline score under experiment a and under b."""

    index: int
    input: str
    a: float | None
    b: float | None
    delta: float | None


class CompareScorer(BaseModel):
    """One scorer side by side."""

    a: float | None
    b: float | None
    delta: float | None


class CompareOut(BaseModel):
    """Two experiments compared case by case and scorer by scorer."""

    a: ExperimentSummary
    b: ExperimentSummary
    delta: float | None
    scorers: dict[str, CompareScorer]
    cases: list[CompareCase]


class VerdictOut(BaseModel):
    """The bootstrap interval and colour of one measured segment."""

    mean_delta: float
    ci_low: float
    ci_high: float
    n_cases: int
    verdict: str
    stage: int


class SegmentOut(BaseModel):
    """One block or line of the prompt; `verdict` is None when it was never measured."""

    id: int
    parent_segment_id: int | None
    level: str
    index: int
    start_offset: int
    end_offset: int
    text: str
    tokens: int
    verdict: VerdictOut | None


class AblationRow(BaseModel):
    """The ablation summary: baseline, cut prompt and its confirmation run (PRD §12)."""

    baseline_score: float
    cut_score: float | None
    cut_ci_low: float | None
    cut_ci_high: float | None
    cut_prompt: str
    tokens_before: int
    tokens_after: int
    confirmed: bool


class AblationOut(BaseModel):
    """Everything the ablation screen paints: segments with verdicts, the row, totals."""

    experiment: ExperimentSummary
    prompt_text: str
    delta: float
    input_usd_per_million: float | None
    legend: dict[str, str]
    segments: list[SegmentOut]
    ablation: AblationRow | None
    totals: Totals


class SettingsOut(BaseModel):
    """Config echo, whether the key is present (never the key itself), display settings."""

    config: dict[str, Any] | None
    api_key_present: bool
    calls_per_month: int
    inr_rate: float


class SettingsIn(BaseModel):
    """Display settings a user may change from the dashboard (PRD F7.2). Omitted keys keep
    their value."""

    model_config = ConfigDict(extra="forbid")

    calls_per_month: int | None = Field(default=None, ge=1)
    inr_rate: float | None = Field(default=None, gt=0.0)


class HealthOut(BaseModel):
    """`GET /health`."""

    status: str
    database: str


class SummaryOut(BaseModel):
    """`GET /summary`: the sidebar's spend card, summed over every run in the database."""

    runs: int
    calls: int
    cached: int
    cost_usd: float
