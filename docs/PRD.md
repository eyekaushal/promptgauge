# promptgauge — Product Requirements Document (v1)

> **Status:** Draft v1 · 17 Oct 2026
> **Owner:** Kaushal Shahare (author) · Reviewer: Sujay
> **Companion documents:**
> - `docs/PLAN.md` — blocks, branches, schedule, progress tracker.
> - `docs/DESIGN.md` — the UI law (v0; rewritten at the UI branch).
> - `docs/DISTRIBUTION.md` — how users get it, what it costs.
> - `docs/HANDOFF.md` — the origin notes this PRD grew from. `docs/PRIOR_ART.md` — ProCut and every adjacent tool.

---

## Table of contents

1. [Product summary](#1-product-summary)
2. [Problem](#2-problem)
3. [Goals, non-goals, success metrics](#3-goals-non-goals-success-metrics)
4. [Users](#4-users)
5. [Scope of v1](#5-scope-of-v1)
6. [Feature requirements](#6-feature-requirements)
7. [Key user flows](#7-key-user-flows)
8. [Screens](#8-screens)
9. [Non-functional requirements](#9-non-functional-requirements)
10. [Tech stack](#10-tech-stack)
11. [Architecture and class design](#11-architecture-and-class-design)
12. [Data model](#12-data-model)
13. [Internal API](#13-internal-api)
14. [LLM usage](#14-llm-usage)
15. [Engineering conventions](#15-engineering-conventions)
16. [v1 release criteria](#16-v1-release-criteria)
17. [Risks and mitigations](#17-risks-and-mitigations)
18. [Open questions](#18-open-questions)
19. [Future versions](#19-future-versions)

---

## 1. Product summary

**promptgauge** is an open-source Python tool that measures which parts of a system prompt actually change a model's behaviour. It removes one block of the prompt at a time, reruns the developer's own test cases, and paints every block and line red (load-bearing), grey (no measurable effect at this sample size) or green (removing it helped). It then produces a shorter prompt made only of the red parts, confirms that it scores the same, and reports the tokens and money saved per month.

- **Runs on the developer's machine.** `pip install promptgauge`, their own Anthropic key, results in a local SQLite file. No hosted service, no telemetry.
- **Three parts, one package:** an SDK (`evaluate()`, `ablate()`), a CLI (`promptgauge eval | ablate | ui`), and a local dashboard (FastAPI + React) that reads the results.
- **The method is ProCut's** (Xu, Li, Chen, Wang, EMNLP 2025 Industry Track): leave-one-out attribution over prompt segments. ProCut released no code. promptgauge is that method shipped as a tool, with repeated runs, confidence intervals, a budget planner, a confirmation run and a dashboard.

**One-line pitch:** *Find out which lines of your prompt do anything, with proof, and ship the short one.*

---

## 2. Problem

1. Production system prompts grow by accretion. Every incident adds a line; nothing removes one. A 2,400-token prompt is normal and nobody knows which 400 tokens matter.
2. The only way to find out is manual: remove a line, rerun the evals, compare, repeat. Claude Code's own team did exactly this to cut about 80% of their prompt (Boris Cherny's playbook). It took engineers days.
3. Existing tools do not do this. Eval runners (promptfoo, DeepEval, Braintrust, Langfuse) compare prompt versions the developer wrote. Optimizers (DSPy GEPA, Opik) rewrite the prompt into something the developer did not write. Compressors (LLMLingua) drop tokens and produce unreadable text. None of them says "line 31 is dead".
4. Single runs lie. LLM output is sampled, so one run per variant is noise. Any honest answer needs repeats and a confidence interval, and no eval tool gives one per prompt segment.

---

## 3. Goals, non-goals, success metrics

### 3.1 Goals

| # | Goal |
|---|---|
| G1 | Given a prompt and a dataset, produce a per-segment verdict (red / grey / green) with a confidence interval, and a cut prompt whose score is confirmed against the baseline. |
| G2 | Never spend more than the developer's stated budget, and tell them the estimate before the first call. |
| G3 | Be honest about noise: grey is "could not detect a difference at this sample size", with the sample size shown. |
| G4 | Work from a repo in under ten minutes: install, write a config, run, open the dashboard. |
| G5 | Be a credible portfolio project: one-class-per-file OOP, tests, a real ablation of mailmoat's Planner prompt in the README, ProCut cited. |

### 3.2 Non-goals (v1)

Hosting anything; teams or auth; providers other than Anthropic; ablating tool descriptions or few-shot examples; prompt rewriting or optimisation; prompt version management; more than four scorers; a plugin for pytest or CI gates; importing promptfoo, Braintrust or Langfuse datasets; dark theme.

### 3.3 Success metrics

| Type | Metric | Target |
|---|---|---|
| Correctness | Verdict rule on synthetic scores with known effects | 100% of the table in `tests/ablate/test_verdict_rule.py` |
| Correctness | Segmenter round-trip: joining all segments reproduces the prompt byte for byte | 100% on the fixture prompts |
| Cost | Budget planner estimate vs real bill on the support-bot example | within 25% |
| Cost | Cache hit rate on a rerun with an unchanged prompt | 100%, $0.00 spent |
| Product | `pip install` to first `promptgauge eval` table on a clean machine | ≤ 10 min |
| Product | Full ablation of a 30-block prompt, 40 cases, 3 repeats, Haiku judge, Sonnet target | ≤ $10 and ≤ 30 min |
| Demo | mailmoat Planner prompt ablation in the README | a number of tokens cut, and a confirmation score within `delta` of baseline |
| Adoption | Developers trying it (stars, installs, replies from outreach) | ~50 within a month of release |

---

## 4. Users

| Persona | Description | What they need |
|---|---|---|
| **P1 — The backend engineer with a fat prompt** (primary) | Owns an LLM feature in production, has 20 to 100 test cases or can write them, pays the API bill. | A verdict per line, a shorter prompt they can trust, a number for the finance conversation. |
| **P2 — The solo founder migrating models** | Moving from one model to a cheaper one and does not know which prompt lines were written for the old model's quirks. | A fast way to see what is dead before rewriting anything. |
| **P3 — The evaluator** (founder, interviewer, reviewer) | Looks at the repo and the README for three minutes. | The painted prompt screenshot, the mailmoat demo numbers, clean code, ProCut cited. |

---

## 5. Scope of v1

### 5.1 In scope

| ID | Feature | Priority |
|---|---|---|
| F1 | Config and dataset loading | Must |
| F2 | Provider and call cache | **Must (core)** |
| F3 | Scorers (four) | Must |
| F4 | Evaluator (`evaluate()`, `promptgauge eval`) | Must |
| F5 | Segmentation and variants | **Must (core)** |
| F6 | Ablation: plan, budget, measure, verdicts, cut prompt, confirmation (`ablate()`, `promptgauge ablate`) | **Must (core)** |
| F7 | API server | Must |
| F8 | Dashboard: Datasets, Experiments, Ablation, Settings | Must |
| F9 | Example project and the mailmoat demo | Must |

### 5.2 Out of scope (v1) — see §19

Pairwise interaction checks; pytest plugin; OpenAI and other providers; promptfoo YAML import; prompt versioning; experiment diff beyond two runs side by side; hosted anything.

---

## 6. Feature requirements

Each requirement has an ID for traceability in `PLAN.md` and tests. "AC" = acceptance criteria.

### F1 — Config and dataset loading

**Description:** A `promptgauge.yaml` in the project directory and a `cases.jsonl` dataset. Both validated with Pydantic; errors name the field and the line.

| ID | Requirement |
|---|---|
| F1.1 | Config fields: `prompt` (path), `dataset` (path), `model`, `judge` (default `claude-haiku-4-5`), `scorers` (list; a string for a free scorer, a one-key mapping for a configured one, e.g. `rubric: helpful` or `json_schema: schema.json`), `repeats` (default 3), `temperature` (default 0.7), `budget_usd` (default 2.00), `delta` (default 0.03), `concurrency` (default 8). |
| F1.2 | Dataset rows: `{"input": str, "expected": str?, "context": str?, "tags": [str]?}`. One JSON object per line. Empty lines ignored. A bad line fails the whole load with its line number. |
| F1.3 | The dataset hash (SHA-256 of the normalised file) and the prompt hash identify an experiment. Changing either makes a new experiment; the call cache still applies to unchanged (prompt, input) pairs. |
| F1.4 | `ANTHROPIC_API_KEY` is read from the environment. Nothing secret is ever written to config or SQLite. |
| F1.5 | `--config` on every CLI command, default `./promptgauge.yaml`. The SDK functions take the same fields as keyword arguments. |

**AC:** A config with a missing dataset file, an unknown scorer, or `repeats: 0` fails before any call with a one-line message naming the problem.

### F2 — Provider and call cache (core)

| ID | Requirement |
|---|---|
| F2.1 | `AnthropicProvider` is the only class that talks to the network. One method, `complete(system, user, model, temperature, max_tokens)`, returns a `Completion` with text, input tokens, output tokens, cost in USD. |
| F2.2 | A pricing table (`Pricing`) maps model id to USD per million input and output tokens. Unknown model → `ProviderError` before any call. |
| F2.3 | Retries and timeouts come from the SDK (`max_retries=3`); 429 and 529 back off; any other failure raises `ProviderError` with the model and the case id. |
| F2.4 | `CallCache` keys on SHA-256 of (model, system prompt, user input, temperature, repeat index). A hit costs nothing and is recorded with `cost_usd = 0` and `cached = 1`. |
| F2.5 | Concurrency is an asyncio semaphore of `concurrency` in-flight calls. |
| F2.6 | Every call, cached or not, is written to the `call` table with tokens and cost. Totals per experiment come from that table, never from a counter in memory. |

**AC:** Running `promptgauge eval` twice on an unchanged prompt and dataset reports `$0.00` and `cached 100%` the second time.

### F3 — Scorers

Each scorer implements `score(case, output) -> ScoreResult(score: float in [0,1], reason: str | None)`.

| ID | Requirement |
|---|---|
| F3.1 | `contains`: 1.0 if `case.expected` appears in `output` after lower-casing and whitespace normalisation, else 0.0. Cases with no `expected` are skipped by this scorer (not scored as 0). `exact` is full equality under the same normalisation. |
| F3.2 | `json_schema`: parse `output` as JSON (tolerating a fenced ```json block), validate with `jsonschema`. 1.0 or 0.0; reason is the first validation error path. |
| F3.3 | `rubric`: the judge receives the rubric text, the input and the output, and must return `{"score": number, "reason": string}` as JSON, validated with Pydantic. Five rubrics ship in `promptgauge/rubrics/`: `helpful`, `concise`, `on_topic`, `tone_professional`, `follows_instructions`. A path to a custom rubric file is accepted. |
| F3.4 | `grounded`: the judge lists the claims in `output` and marks each supported or unsupported by `case.context`. Score is supported / total; reason lists the unsupported claims. Cases with no `context` are skipped. |
| F3.5 | Judge calls go through the same provider and cache, with temperature 0 and a fixed system prompt per scorer. A malformed judge answer is retried once, then scored as `None` (excluded from means) with the reason `judge_failed`. |
| F3.6 | A case's score for an experiment is the mean over scorers that returned a value; an experiment's score is the mean over cases and repeats. |

**AC:** Each scorer has a table test with at least four positive and four negative cases; rubric and grounded run against `FakeProvider` returning canned JSON.

### F4 — Evaluator

| ID | Requirement |
|---|---|
| F4.1 | `evaluate(dataset, prompt, model, scorers, repeats, judge, temperature)` runs every (case, repeat), scores every output, writes an `experiment` row and one `result` row per (case, repeat, scorer), and returns an `EvalResult` with per-scorer means, a per-case table, total cost and duration. |
| F4.2 | `promptgauge eval` prints a table (rich): one row per case with the mean score per scorer, then totals: score, cases, repeats, calls, cached, cost, time. |
| F4.3 | A failed call for one case does not abort the run; the case is reported as failed with the error, and the experiment's `status` is `partial`. |
| F4.4 | Progress is shown as a single updating line (calls done / total, spend so far). |

**AC:** On `examples/support-bot`, `promptgauge eval` completes with 10 rows and a total; `uv run pytest` covers the evaluator with `FakeProvider`.

### F5 — Segmentation and variants (core)

| ID | Requirement |
|---|---|
| F5.1 | `PromptSegmenter.blocks(text)` splits on blank lines and markdown headings (`#` lines start a new block and belong to it). Each block records `start` and `end` character offsets. Joining every block's text with its original separators reproduces the prompt byte for byte. |
| F5.2 | `PromptSegmenter.lines(block)` splits a block into lines: a list item is one line; a paragraph is split on sentence boundaries (`.`, `?`, `!` followed by whitespace and an uppercase letter or end of text). Same offset and round-trip rule. |
| F5.3 | `VariantBuilder.without(segment)` returns the prompt text with that segment's character range removed and surrounding whitespace collapsed so no double blank line is left. Nothing else changes. |
| F5.4 | Segments are stored with `level` (`block` or `line`), `parent_segment_id`, offsets, text and token count (from the provider's tokenizer, or a `len/4` estimate when offline). |
| F5.5 | A prompt with a single block is still ablated at the line level directly. |

**AC:** Round-trip tests on five fixture prompts (headings, bullets, paragraphs, mixed, single block); a variant never contains the removed text and never changes any other character.

### F6 — Ablation (core)

| ID | Requirement |
|---|---|
| F6.1 | **Plan.** Stage one: baseline plus one variant per block. Stage two: one variant per line inside every block whose verdict is red. `AblationPlanner` returns the list of variants per stage and the number of calls each stage needs. |
| F6.2 | **Budget.** Before the first call, `BudgetPlanner.estimate()` computes calls × (prompt tokens + mean input tokens + expected output tokens) × price, for stage one plus an estimate of stage two at 30% of blocks going red. If the estimate exceeds `budget_usd` the CLI prints the estimate, the three cheapest ways under it (fewer repeats, fewer cases by tag, a cheaper target model) and exits 2 without calling anything. During the run, when real spend crosses `budget_usd`, the run stops, writes what was measured, and the report says `stopped: budget`. |
| F6.3 | **Measure.** Every variant runs the full dataset with the same repeats as the baseline, through the cache. Per case, the difference is `mean(variant scores over repeats) − mean(baseline scores over repeats)`. |
| F6.4 | **Interval.** `Bootstrap.mean_ci(differences, resamples=1000, level=0.95)` returns the mean difference and the percentile interval across cases. Seeded for reproducibility. |
| F6.5 | **Verdict.** `VerdictRule(delta)`: red if `ci_high < −delta`; green if `ci_low > +delta`; grey otherwise. The verdict row stores `mean_delta`, `ci_low`, `ci_high`, `n_cases`, so the dashboard can repaint for any `delta` without recomputation. |
| F6.6 | **Cut prompt.** `PromptCutter` removes every grey and green segment. Inside a red block, only red lines stay. If a red block had no stage-two lines (single-line block), the whole block stays. Output is the developer's own text, nothing added. |
| F6.7 | **Confirmation.** The cut prompt runs the full dataset once more (same repeats). The report shows baseline score, cut score, the interval of the difference, tokens before and after. If `cut score < baseline − delta` the report says `cut prompt not confirmed` and still shows it, marked as a suggestion. |
| F6.8 | **Report.** `AblationReport` carries segments with verdicts, the cut prompt, baseline and confirmation scores, tokens removed, cost, duration, and `stopped` (none / budget / error). The CLI prints the prompt with ANSI colours per segment, a legend, the totals, and writes the cut prompt to `<prompt>.cut.md`. |
| F6.9 | **Money saved** = tokens removed × input price per token × `calls_per_month`; `calls_per_month` is a dashboard input, default 100,000, and a CLI flag. Shown in USD and INR at a fixed rate in config (default 84). |

**AC:** On synthetic scores from `FakeProvider` (block A always drops the score by 0.2 when removed, block B never changes it, block C raises it by 0.1), the ablation paints A red, B grey, C green and the cut prompt contains only A; on `examples/support-bot` with real calls, the run finishes inside `budget_usd` and the planner's estimate is within 25% of the bill.

### F7 — API server

| ID | Requirement |
|---|---|
| F7.1 | FastAPI app bound to `127.0.0.1:7331`, JSON under `/api`, the built dashboard served at `/`. |
| F7.2 | Read-only over SQLite except `PUT /api/settings` (non-secret display settings: `calls_per_month`, `inr_rate`). |
| F7.3 | Host header must be `127.0.0.1:7331` or `localhost:7331`; anything else is 403 (DNS rebinding guard). |
| F7.4 | Errors: 404 for unknown ids, 422 for bad input (Pydantic), 500 with details only in the server log. |

**AC:** Every route has a test with an in-memory database; a request with a foreign Host header is refused.

### F8 — Dashboard

| ID | Requirement |
|---|---|
| F8.1 | **Datasets.** One table per dataset hash: input, expected, context, tags. Row click opens the full text in a side panel. A search box filters client-side. |
| F8.2 | **Experiments.** Table of runs: name, kind, model, mean score per scorer, cases, cost, duration, date, status. Click opens the per-case table: input, output, expected, each scorer's score and reason; failures tinted. Two runs can be selected for a side-by-side per-case view. |
| F8.3 | **Ablation.** The prompt rendered in monospace, each segment painted by verdict. Hover: baseline score, score without, `mean_delta`, interval, `n_cases`, tokens. A `delta` slider repaints from stored verdicts. The cut-prompt panel: original and cut side by side, token counts, confirmation score beside baseline, `calls_per_month` input, money saved in USD and INR, a copy button. A banner when `stopped` is not none. |
| F8.4 | **Settings.** Model, judge, `budget_usd`, `delta` as read from the config of the last run; API key status (present / missing, never the key); `calls_per_month` and `inr_rate` editable. |
| F8.5 | Light theme only; every colour carries a word too (the legend and tooltips say red / grey / green and what they mean). |

**AC:** All four screens render against the real API with the support-bot results; the ablation screen shows the painted prompt and the cut prompt.

### F9 — Example project and the mailmoat demo

| ID | Requirement |
|---|---|
| F9.1 | `examples/support-bot/`: a four-block prompt, 10 cases with tags, a config with `budget_usd: 1.00`. Used for the first real run and in the docs. |
| F9.2 | `examples/mailmoat-planner/`: mailmoat's Planner system prompt and 40 cases drawn from its attack lab and benign set (typed facts in, plan JSON out), scorers `json_schema` + `rubric: follows_instructions`. The README's headline numbers come from this run. |
| F9.3 | The README shows the painted prompt (screenshot), the numbers (segments, tokens removed, baseline vs cut score, cost of the run), the install, the config, and cites ProCut. |

**AC:** The mailmoat run completes inside $10 and its report is checked into `examples/mailmoat-planner/report.md`.

---

## 7. Key user flows

### 7.1 First run
`pip install promptgauge` → write `promptgauge.yaml` and `cases.jsonl` → `promptgauge eval` → table in the terminal → `promptgauge ui` → Experiments screen shows the run.

### 7.2 Ablation
`promptgauge ablate` → estimate printed ("~1,240 calls, ≈ $1.60 of $2.00") → progress line → painted prompt in the terminal → `system.cut.md` written → `promptgauge ui` → Ablation screen → slide `delta`, copy the cut prompt.

### 7.3 Over budget
`promptgauge ablate` → "estimate $6.40 exceeds budget $2.00" → three suggestions → exit 2, nothing called.

### 7.4 From code
```python
from promptgauge import evaluate, ablate, scorers

report = ablate(
    dataset="cases.jsonl",
    prompt="prompts/system.md",
    model="claude-sonnet-4-5",
    repeats=3,
    budget_usd=2.0,
    scorers=[scorers.contains(), scorers.rubric("helpful")],
)
print(report.cut_prompt, report.tokens_removed)
```

---

## 8. Screens

| Screen | Route | Content |
|---|---|---|
| Datasets | `/datasets` | Dataset selector (by hash, newest first), case table, side panel |
| Experiments | `/experiments`, `/experiments/:id` | Runs table; per-case table; compare two |
| Ablation | `/ablations/:id` | Painted prompt, hover cards, `delta` slider, cut-prompt panel |
| Settings | `/settings` | Config echo, key status, display settings |

Design rules for all of them: `docs/DESIGN.md`.

---

## 9. Non-functional requirements

| Area | Requirement |
|---|---|
| Privacy | Nothing leaves the machine except calls to Anthropic. No telemetry, no update checks. |
| Cost | The estimate is printed before the first call; the run stops at the budget. The cache makes reruns free. |
| Reproducibility | Bootstrap is seeded; the cache key includes the repeat index, so a rerun reproduces the same numbers. |
| Performance | 1,000 calls with concurrency 8 finish in well under 30 minutes on Haiku; the dashboard renders a 150-segment prompt without lag. |
| Portability | macOS and Linux, Python 3.11 and 3.12. Windows untested in v1. |
| Install | `pip install promptgauge` brings the built dashboard inside the wheel; no Node needed to use it. |

---

## 10. Tech stack

**Language: Python 3.11+.** Type hints everywhere; Pydantic for runtime validation. (Decision: 16 Oct 2026.)

| Layer | Choice | Why |
|---|---|---|
| Package | `uv` + `hatchling`, PyPI as `promptgauge` | Fast, lockfile, one command to build and publish |
| CLI | **Typer** + **rich** | Commands with help for free; tables and the painted prompt |
| Validation | **Pydantic v2** | Config, dataset rows, judge output, API models |
| LLM | **`anthropic`** SDK | Official; retries and timeouts built in |
| Stats | **numpy** | Bootstrap resampling |
| Database | **SQLite** via `sqlite3` (stdlib) | Local, zero setup; one file per project |
| Server | **FastAPI** + **uvicorn** | Small, typed, serves static files |
| Dashboard | **React 19 + Vite + Tailwind 4** | Same shape as contextlab and mailmoat; built into the wheel |
| Tests | **pytest** + `pytest-asyncio`, **httpx** for API tests | Standard |
| Lint/format | **ruff** | One tool |
| Checks | `ruff` and `pytest` run locally before every merge; `pip-audit` before release | No GitHub Actions |

Final versions are pinned in `uv.lock` at B00; any package added later is justified in its block summary.

---

## 11. Architecture and class design

### 11.1 Runtime view

```
 CLI / SDK ─▶ Evaluator ──▶ CallCache ──▶ AnthropicProvider ──▶ Anthropic
                 │              │
                 ▼              ▼
             Scorers        SQLite (call, result, experiment …)
                 ▲
 Ablation ───────┘  (plan → budget → measure → bootstrap → verdicts → cut → confirm)

 Browser (React, 127.0.0.1:7331) ──▶ FastAPI ──▶ repositories ──▶ SQLite   (read only)
```

### 11.2 Classes (OOP) by module

One class per file, snake_case file named after the class.

| Module | Classes | Responsibility |
|---|---|---|
| `core/` | `Logger`, errors (`PromptgaugeError`, `ConfigError`, `DatasetError`, `ProviderError`, `BudgetExceededError`, `ScorerError`) | Cross-cutting |
| `config/` | `Config` (Pydantic model + `load(path)`), `Pricing` | Settings and the price table |
| `dataset/` | `Case` (Pydantic), `DatasetLoader` | Load and hash `cases.jsonl` |
| `prompt/` | `Segment`, `PromptSegmenter`, `VariantBuilder` | Blocks, lines, deletion variants |
| `provider/` | `AnthropicProvider`, `Completion`, `FakeProvider` (tests) | The only network code |
| `cache/` | `CallCache` | Hash, lookup, store |
| `db/` | `Database`, `Migrator`, `ExperimentRepository`, `CaseRepository`, `CallRepository`, `ResultRepository`, `SegmentRepository`, `VerdictRepository` | Data access only |
| `scorers/` | `Scorer` (base), `ScoreResult`, `ContainsScorer`, `ExactScorer`, `JsonSchemaScorer`, `RubricScorer`, `GroundedScorer`, `Judge` | The four scorers and the judge they share |
| `runner/` | `Evaluator`, `EvalResult`, `CaseRun` | Run cases, score, store |
| `ablate/` | `AblationPlanner`, `BudgetPlanner`, `Ablation`, `PromptCutter`, `AblationReport`, `SegmentVerdict` | The product |
| `stats/` | `Bootstrap`, `VerdictRule` | The maths |
| `api/` | `App` (factory), `HostGuard` (middleware), `CasesRoutes`, `ExperimentsRoutes`, `AblationsRoutes`, `SettingsRoutes` | HTTP surface |
| `cli/` | `main.py` (composition root + Typer app), `TerminalPainter`, `EvalTable` | Commands and terminal output |
| `sdk.py` | `evaluate()`, `ablate()` | Public functions; build the composition root and call it |

**Composition root:** `src/promptgauge/cli/main.py` builds all objects once per command and injects through constructors. `sdk.py` uses the same builder so the SDK and the CLI share one wiring.

### 11.3 Dependency rule

`api/` → `db/`. `cli/`, `sdk.py` → `ablate/`, `runner/` → `scorers/`, `cache/`, `prompt/`, `stats/` → `provider/`, `db/` → `config/`, `core/`.
`api/` never imports `provider/`, `runner/` or `ablate/` (the dashboard never calls a model). `prompt/` and `stats/` import nothing from `provider/` (pure code).

---

## 12. Data model

SQLite, one file at `.promptgauge/promptgauge.db` in the project directory (gitignored).

| Table | Key columns |
|---|---|
| `experiment` | `id`, `kind` (`eval` / `ablation`), `name`, `prompt_hash`, `prompt_text`, `dataset_hash`, `model`, `judge`, `config_json`, `status` (`running` / `done` / `partial` / `stopped`), `stopped_reason`, `created_at`, `finished_at` |
| `case` | `id`, `dataset_hash`, `index`, `input`, `expected`, `context`, `tags_json` |
| `call` | `hash` (PK), `model`, `system_hash`, `input_hash`, `temperature`, `repeat_index`, `output`, `input_tokens`, `output_tokens`, `cost_usd`, `cached`, `experiment_id`, `created_at` |
| `result` | `experiment_id`, `case_id`, `repeat_index`, `variant_id` (NULL = baseline), `scorer`, `score` (NULL = judge failed), `reason`, `call_hash` |
| `segment` | `id`, `experiment_id`, `parent_segment_id`, `level`, `index`, `start_offset`, `end_offset`, `text`, `tokens` |
| `verdict` | `experiment_id`, `segment_id`, `mean_delta`, `ci_low`, `ci_high`, `n_cases`, `verdict`, `stage` |
| `ablation` | `experiment_id` (PK), `baseline_score`, `cut_score`, `cut_ci_low`, `cut_ci_high`, `cut_prompt`, `tokens_before`, `tokens_after`, `confirmed` |
| `settings` | `key`, `value` (`calls_per_month`, `inr_rate`) |

Schema changes go through numbered migration files in `db/migrations/`.

---

## 13. Internal API

All routes under `/api`, JSON, bound to `127.0.0.1`, Host header checked.

| Area | Routes |
|---|---|
| Datasets | `GET /datasets` (hashes with case counts and first-seen), `GET /datasets/{hash}/cases` |
| Experiments | `GET /experiments`, `GET /experiments/{id}`, `GET /experiments/{id}/results` (per case, per repeat, per scorer), `GET /experiments/compare?a=&b=` |
| Ablations | `GET /ablations/{id}` (segments with verdicts, the ablation row, totals) |
| Settings | `GET /settings` (config echo, `api_key_present`, display settings), `PUT /settings` (display settings only) |
| System | `GET /health` |

Request and response models are Pydantic classes in `api/models.py`. Typed errors map to 404 and 422; anything else is a 500 whose details stay in the log.

---

## 14. LLM usage

| Role | Default model | Call pattern |
|---|---|---|
| **Target** | from config (`model`); the demo uses `claude-sonnet-4-5` | System = prompt variant, user = case input, `temperature` from config (default 0.7), `max_tokens` 1,024. Through the cache. |
| **Judge** | `claude-haiku-4-5` | System = fixed scorer prompt, user = rubric + input + output (or context + output), temperature 0, JSON answer validated with Pydantic, `max_tokens` 512. Through the cache. |

Rules:
- All calls go through `AnthropicProvider` and `CallCache`; every call is a `call` row with tokens and cost.
- No tools, no streaming, no prefill. Plain text in, plain text out; the judge is asked for JSON and parsed.
- The judge prompts live in `scorers/prompts/` as versioned markdown files. Changing one invalidates the judge cache (the prompt text is part of the hash).
- Model ids and prices live in `config/pricing.py` with the date they were checked; unknown ids fail before any call.

---

## 15. Engineering conventions

These also go into `CLAUDE.md`.

| Topic | Rule |
|---|---|
| Paradigm | **OOP**: one class per file, single responsibility, constructor-injected dependencies, small public methods, single-underscore private helpers. |
| Principles | **KISS**, **YAGNI**, DRY only for correctness-critical logic. |
| Language | Python 3.11+; type hints on public signatures; Pydantic for runtime validation; `ruff` clean. |
| Commits | **Conventional Commits** `type(scope): summary`; scopes `core config dataset prompt provider cache db runner scorers ablate stats api ui docs ci`. Example: `feat(ablate): stop the run when spend crosses the budget`. |
| Branches | **Conventional Branch** `feature/… bugfix/… hotfix/… chore/… release/…`; `main` always works; one branch per PLAN branch, merged via PR. |
| Git | **The user runs every git command.** The AI assistant never runs git and never appears as author or co-author. |
| Tests | Segmenter, verdict rule and budget planner are written test-first; every bug fix adds a regression test; tests never touch the network. |

---

## 16. v1 release criteria

1. All "Must" features F1–F9 meet their acceptance criteria.
2. The synthetic ablation test (F6 AC) passes; segmenter round-trips pass; the budget estimate on support-bot is within 25% of the bill.
3. Local checks green: ruff, pytest, `pip-audit` with no high or critical issues.
4. `pip install promptgauge` on a clean machine, `promptgauge ui` opens the dashboard with the bundled static build.
5. README with install, config, the painted mailmoat prompt, the numbers, and the ProCut citation.
6. The mailmoat Planner ablation report checked in, run inside $10.
7. Tag `v0.1.0` on PyPI.

---

## 17. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Grey everywhere at small sample sizes | Tool looks useless | Say so in the output with `n_cases`; the CLI prints "add cases to narrow the intervals" when more than 80% is grey |
| Judge noise swamps real effects | Wrong verdicts | Judge at temperature 0 and cached; rubric scorers paired with a deterministic scorer in the examples |
| Budget estimate far off | Surprise bill | Estimate checked against the bill on day two and corrected; the hard stop at `budget_usd` caps the damage |
| Segmenter mangles a prompt (code blocks, tables) | Broken variants | Round-trip tests; fenced code blocks are one segment, never split |
| Cut prompt fails confirmation | Credibility | Reported honestly as "not confirmed"; the tool's value is the painted prompt, not the cut |
| Dashboard scope creep | Day three overruns | Four screens; new ideas go to `docs/TODO.md` |
| Anthropic rate limits on concurrency 8 | Slow runs | SDK retries; `concurrency` in config |

---

## 18. Open questions

| # | Question | Proposed default |
|---|---|---|
| Q1 | Sentence splitting inside paragraphs: regex or a small library? | Regex (`[.?!]\s+(?=[A-Z]|$)`); revisit if fixtures break |
| Q2 | Should stage two run on green blocks too, to find a red line inside a harmful block? | No in v1; whole green blocks are cut |
| Q3 | Token counts: provider tokenizer call per segment, or `len/4`? | Provider count once per segment at ablation start (cheap, one request per segment) |
| Q4 | Port | `7331`, configurable with `--port` |
| Q5 | Licence | MIT |

---

## 19. Future versions

| Version | Candidates |
|---|---|
| v0.2 | Pairwise interaction checks on red lines (HiveMind DAG-Shapley for efficiency); pytest plugin `assert_score(min=…)` for CI gates; promptfoo YAML import |
| v0.3 | OpenAI provider; Braintrust and Langfuse dataset import; a "why does this line matter" card generated from failed cases (GEPA's reflection trick) |
| Later | Tool-description and few-shot ablation; two-model migration mode (ablate against the old and new model side by side); docs site |
