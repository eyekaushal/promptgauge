# promptgauge — Build Plan (v1)

> **Status:** v1 · 17 Oct 2026 — 4-day build (Sat 17 Oct → Tue 20 Oct 2026), ~6 h/day with Claude Code (Max plan). Ship Tuesday night as `v0.1.0` on PyPI.
> **Inputs:** `docs/PRD.md` (what), `docs/DESIGN.md` (UI law, v0), `docs/DISTRIBUTION.md` (how it ships).
> **Rule of the road:** Claude writes and tests code; **Kaushal runs every git command by hand.** No AI author or co-author lines anywhere.

---

## Table of contents

1. [How this plan works](#1-how-this-plan-works)
2. [Schedule: 4 days](#2-schedule-4-days)
3. [Branches (5) and git workflow](#3-branches-5-and-git-workflow)
4. [Block checklist](#4-block-checklist)
5. [Token and context strategy](#5-token-and-context-strategy)
6. [Cut list (only if behind schedule)](#6-cut-list-only-if-behind-schedule)
7. [Phase notes](#7-phase-notes)
8. [Final folder structure and file count](#8-final-folder-structure-and-file-count)
9. [Testing strategy](#9-testing-strategy)
10. [Definition of done](#10-definition-of-done)
11. [Progress tracker](#11-progress-tracker)
12. [v0.2 candidates](#12-v02-candidates)

---

## 1. How this plan works

- **21 blocks (B00–B20)** are the units of work, grouped into **5 branches** (plus `main`). One branch = one pull request = roughly one day.
- Each block ends with **one commit** (Conventional Commits). Claude posts exactly one `git add`, one `git commit -m`, one `git push` per block.
- Order follows dependencies: foundation → evaluator (**Milestone 1, end of Day 1: a real eval table**) → ablation core (**Milestone 2, end of Day 2: a painted prompt from real calls**) → API and UI (**Milestone 3, end of Day 3**) → demo, docs, release (Day 4).
- **Working loop per block:**
  1. Claude implements the block and runs its tests.
  2. Claude posts a ≤ 10-line summary: what changed, how to verify, the one commit.
  3. Kaushal reviews and commits (Claude never runs git).
- **End of each branch:** Kaushal pushes, opens the PR, runs `uv run ruff check . && uv run pytest -q` locally, and merges.
- **End of each day:** 20-minute **explain-back** — Kaushal explains the day's classes and data flow in his own words. Anything he cannot explain gets walked through before the next day starts.

> 🎨 **UI rule:** Before the UI blocks start, Claude stops and says: **"We are starting UI now — rewrite DESIGN.md to v1 first, then build."**

---

## 2. Schedule: 4 days

Hours are Claude-Code-paced estimates including review time. **Total ≈ 23 h of 24 h available.** The only buffer is Tuesday afternoon, which is why §6 exists.

| Day | Date | Branches | Hours | End-of-day outcome |
|---|---|---|---|---|
| **1** | Sat 17 Oct | `main` (scaffold) · `feature/foundation-and-evaluator` | ~6 | **Milestone 1:** `promptgauge eval` prints a real table on `examples/support-bot`; second run costs $0 |
| **2** | Sun 18 Oct | `feature/ablation` | ~6 | **Milestone 2:** `promptgauge ablate` paints the support-bot prompt from real calls; estimate within 25% of the bill; `system.cut.md` written |
| **3** | Mon 19 Oct | `feature/api-and-dashboard` 🎨 | ~6 | **Milestone 3:** four screens against the real API; the ablation screen shows the painted prompt |
| **4** | Tue 20 Oct | `chore/demo-docs-and-release` | ~5 (+1 buffer) | **v0.1.0 on PyPI:** mailmoat demo in the README, clean-machine install, tag |

**Things Kaushal does in parallel (not Claude):**
- **Day 1 morning:** create an Anthropic API key with a $15 spend limit; `export ANTHROPIC_API_KEY`; create the GitHub repo `eyekaushal/promptgauge` (empty) and a PyPI account with 2FA.
- **Day 2:** read the ablation output and write down anything that surprised him; that becomes the first README paragraph.
- **Day 4:** copy mailmoat's Planner prompt and 40 cases into `examples/mailmoat-planner/`; record the demo video.

---

## 3. Branches (5) and git workflow

### 3.1 The 5 branches

| # | Branch | Blocks | Day | Merge when |
|---|---|---|---|---|
| 0 | `main` (first commit) | B00 | 1 | Scaffold + docs reviewed |
| 1 | `feature/foundation-and-evaluator` | B01–B07 | 1 | `promptgauge eval` works on support-bot; rerun is free |
| 2 | `feature/ablation` | B08–B12 | 2 | Synthetic ablation test passes; real run on support-bot inside budget |
| 3 | `feature/api-and-dashboard` 🎨 | B13–B17 | 3 | Every route tested; four screens work; Kaushal approves visually |
| 4 | `chore/demo-docs-and-release` | B18–B20 | 4 | mailmoat report checked in; README; clean install; tag `v0.1.0` |

**Naming (Conventional Branch):** `feature/…`, `bugfix/…`, `hotfix/…`, `chore/…`, `release/…`; lowercase, hyphens.
**Commits (Conventional Commits):** `type(scope): summary` — types `feat fix refactor test docs chore ci build perf style`; scopes `core config dataset prompt provider cache db runner scorers ablate stats api ui docs ci`.

### 3.2 Very first commit

```bash
git init && git branch -M main
git status                       # notes/ and .env must NOT appear
git add .
git commit -m "chore(core): initial project scaffold and docs"
git remote add origin git@github.com:eyekaushal/promptgauge.git
git push -u origin main
```
On GitHub (as eyekaushal): **Settings → Branches → rule for `main`** → require a pull request. No GitHub Actions: lint and tests run locally.

### 3.3 Each branch

```bash
git checkout main && git pull
git checkout -b feature/<branch-name>
# per block: Claude implements → you review → you run the one commit Claude posted
git add <files> && git commit -m "feat(scope): …"
git push -u origin feature/<branch-name>
```
Open PR → `uv run ruff check . && uv run pytest -q` green locally → **"Create a merge commit"** (keeps every commit visible) →
```bash
git checkout main && git pull && git branch -d feature/<branch-name>
```

### 3.4 Release

After `chore/demo-docs-and-release` is merged:
```bash
git checkout main && git pull
git tag -a v0.1.0 -m "promptgauge v0.1.0"
git push origin v0.1.0
uv build && uv publish          # see DISTRIBUTION.md §1
```
Fixes after release: `bugfix/<desc>` branches → `v0.1.1`.

---

## 4. Block checklist

| Block | Branch | What gets built | PRD refs | Hrs | Done when |
|---|---|---|---|---|---|
| **B00** | main | `pyproject.toml` (hatchling, deps pinned in `uv.lock`), `ruff` config, `pytest` config, `.gitignore`, `.env.example`, LICENSE, `CLAUDE.md`, README stub, `docs/`, package skeleton with one-class-per-file layout, `examples/support-bot/` | — | 0.5 | `uv sync && uv run pytest` passes (zero tests collected is fine) |
| **B01** | foundation-and-evaluator | ~~CI workflow, PR template~~ **Cut 17 Oct 2026:** no GitHub Actions; lint and tests run locally | §15 | 0 | — |
| **B02** | foundation-and-evaluator | `core/`: `Logger`, errors. `config/`: `Config` (Pydantic, `load()`), `Pricing` (dated table). `db/`: `Database` (sqlite3, WAL), `Migrator`, `migrations/001_init.sql` (all §12 tables), six repositories | F1.1, F1.4, §12 | 1.25 | Config errors name the field; migrations idempotent; repositories round-trip in tests |
| **B03** | foundation-and-evaluator | `dataset/`: `Case`, `DatasetLoader` (hash, line-numbered errors) | F1.2, F1.3 | 0.5 | Bad line → `DatasetError` with the line number; hash stable across runs |
| **B04** | foundation-and-evaluator | `provider/`: `Completion`, `AnthropicProvider` (one `complete()`, SDK retries, cost from `Pricing`), `FakeProvider` (scripted outputs, call log). `cache/`: `CallCache` (hash incl. repeat index; writes `call` rows) | F2.1–F2.6 | 1 | Live smoke call recorded with cost; second identical call hits the cache and costs $0 |
| **B05** | foundation-and-evaluator | `scorers/`: `Scorer` base, `ScoreResult`, `ContainsScorer`, `ExactScorer`, `JsonSchemaScorer` | F3.1, F3.2 | 0.5 | Table tests, ≥ 4 positive and 4 negative each |
| **B06** | foundation-and-evaluator | `scorers/`: `Judge` (fixed prompts in `scorers/prompts/`, temp 0, cached, one retry, `judge_failed`), `RubricScorer` + five rubric files, `GroundedScorer` | F3.3–F3.5, §14 | 1 | Both scorers tested against `FakeProvider` canned JSON; malformed answer → `None` score |
| **B07** | foundation-and-evaluator | `runner/`: `CaseRun`, `EvalResult`, `Evaluator` (asyncio semaphore, partial status). `cli/`: `main.py` composition root, `promptgauge eval`, `EvalTable` (rich), progress line. `sdk.py`: `evaluate()` | F4.1–F4.4, F1.5 | 1 | **Milestone 1:** real table on support-bot; rerun prints `$0.00`, `cached 100%` |
| **B08** | ablation | `prompt/`: `Segment`, `PromptSegmenter` (blocks, lines, fenced code as one segment), `VariantBuilder` | F5.1–F5.5 | 1.25 | Round-trip on five fixture prompts; a variant removes exactly one segment |
| **B09** | ablation | `stats/`: `Bootstrap` (seeded percentile CI), `VerdictRule` | F6.4, F6.5 | 0.5 | Verdict table test passes; CI narrows with more cases in a synthetic test |
| **B10** | ablation | `ablate/`: `AblationPlanner` (two stages, call counts), `BudgetPlanner` (estimate, refuse, running stop) | F6.1, F6.2 | 1 | Over-budget config exits 2 with three suggestions and zero calls; running stop writes `stopped: budget` |
| **B11** | ablation | `ablate/`: `SegmentVerdict`, `PromptCutter`, `AblationReport`, `Ablation` (baseline → stage one → stage two → cut → confirmation; writes `segment`, `verdict`, `ablation` rows). `sdk.py`: `ablate()` | F6.3, F6.6–F6.8 | 1.75 | Synthetic test: A red, B grey, C green, cut prompt = A only; confirmation row written |
| **B12** | ablation | `cli/`: `promptgauge ablate`, `TerminalPainter` (ANSI segments, legend, totals, "no measurable effect at this sample size" wording, >80% grey hint), `--calls-per-month`, writes `<prompt>.cut.md`. **First real run** on support-bot; compare estimate to bill; fix `BudgetPlanner` token estimate | F6.8, F6.9 | 1.5 | **Milestone 2:** painted prompt in the terminal from real calls; estimate within 25% of the bill |
| **B13** | api-and-dashboard | `api/`: `App` factory, `HostGuard`, Pydantic models, `CasesRoutes`, `ExperimentsRoutes` (incl. compare), `AblationsRoutes`, `SettingsRoutes`, `/health`; static mount; `promptgauge ui` (uvicorn, opens the browser) | F7.1–F7.4, §13 | 1.25 | Every route tested with an in-memory DB and httpx; foreign Host → 403 |
| **B14** 🎨 | api-and-dashboard | **Stop: rewrite `DESIGN.md` to v1.** Then `dashboard/`: Vite + React 19 + Tailwind 4 + react-router, `ApiClient`, shell (sidebar with four items, main column), design tokens from DESIGN.md, build into `src/promptgauge/api/static` | §8, DESIGN | 1 | Shell renders from the built static files served by FastAPI |
| **B15** 🎨 | api-and-dashboard | Datasets screen (table, side panel, search) and Experiments screen (runs table, per-case table with reasons, compare two) | F8.1, F8.2 | 1.25 | Both screens show the support-bot runs |
| **B16** 🎨 | api-and-dashboard | Ablation screen: painted prompt (monospace, segment spans), hover cards, `delta` slider repainting from stored verdicts, cut-prompt panel (side by side, tokens, confirmation vs baseline, `calls_per_month`, USD and INR, copy), `stopped` banner | F8.3 | 1.5 | **Milestone 3:** the support-bot ablation renders; slider repaints without a request |
| **B17** 🎨 | api-and-dashboard | Settings screen; empty states; tooltips on every coloured element with the word; screenshot pass for the README | F8.4, F8.5 | 0.75 | Kaushal approves all four screens visually |
| **B18** | demo-docs-and-release | `examples/mailmoat-planner/` (prompt, 40 cases, config with `budget_usd: 10`, scorers `json_schema` + `rubric: follows_instructions`); the real run; `report.md` checked in; fix whatever the run exposes | F9.2 | 1.5 | Run completes inside $10; report has segments, tokens removed, baseline vs cut |
| **B19** | demo-docs-and-release | README (what it does, painted-prompt screenshot, the mailmoat numbers, install, config reference, how it works in six sentences, ProCut citation, limits), CHANGELOG, `docs/TODO.md` cleaned | F9.3, §16 | 1.25 | README reads top to bottom without a gap |
| **B20** | demo-docs-and-release | Clean-machine install (`uv venv` elsewhere, `pip install dist/*.whl`, `promptgauge ui` serves the bundled static), `pip-audit` clean, version bump, three-minute demo video, tag, `uv publish` | §16 | 1.25 | `pip install promptgauge` works from PyPI; `v0.1.0` tagged |

---

## 5. Token and context strategy

The Max plan has rolling usage windows and weekly limits; the context window fills fast. Rules for the four days:

1. **One Claude Code session per branch.** At the end of a branch, run `/clear` and start fresh.
2. **Every new session starts with one line:** *"Read CLAUDE.md and PLAN.md §11; continue with the next unchecked block."* `CLAUDE.md` + the tracker are the hand-off.
3. **Claude updates the tracker (§11)** at the end of every block (a file edit, not git).
4. **Read narrowly.** Only the files a block needs; docs by section.
5. **Quiet test output.** `pytest -q`; only failures in full.
6. **No subagents** unless Kaushal explicitly asks.
7. **Short updates.** End-of-block message ≤ 10 lines.
8. **Schedule heavy work after a usage reset.** The tracker lets the next session resume exactly where it stopped.
9. **API spend is separate:** real runs use the Anthropic API key (dollars), not the Max plan. Cap: $15 on the key, $10 for the mailmoat demo, the rest for support-bot runs.

---

## 6. Cut list (only if behind schedule)

Not a watered-down v1. This is the order in which extras move to v0.1.1 if a day overruns. The ablation core (B08–B12), the painted prompt in the terminal and the Ablation screen are **never** on this list.

| Order | Cut | Moves to |
|---|---|---|
| 1 | Experiments compare-two view (F8.2 second half) | v0.1.1 |
| 2 | Settings screen (F8.4): `calls_per_month` and `inr_rate` become CLI flags only | v0.1.1 |
| 3 | `GroundedScorer` (F3.4) | v0.1.1 |
| 4 | INR display (F6.9): USD only | v0.1.1 |
| 5 | Demo video (B20): README screenshot suffices | after release |
| 6 | Datasets screen side panel and search (F8.1): table only | v0.1.1 |

---

## 7. Phase notes

- **Foundation:** `uv` project, `src/` layout, hatchling; SQLite file at `.promptgauge/promptgauge.db` in the project directory (gitignored), WAL mode. `.gitignore`: `.venv/`, `.env`, `notes/`, `.promptgauge/`, `*.db`, `dist/`, `node_modules/`, `dashboard/dist/`, `src/promptgauge/api/static/`. `ruff` with `E F I UP B` rule sets, line length 100.
- **Provider and cache:** the cache key must include the repeat index or repeats collapse into one call; include the full system prompt text in the hash (not a path) so a variant is a different key. Cost is computed from `Pricing`, not from the SDK response, so `FakeProvider` reports the same way.
- **Scorers:** scorers skip cases that lack the field they need; skipped is not zero. The judge prompt text is part of the judge cache key.
- **Segmentation:** fenced code blocks are one segment; headings belong to the block they open; sentence split only inside paragraphs, never inside list items. Offsets are character offsets into the original string; variants are built by slicing, never by re-joining.
- **Ablation:** stage two only inside red blocks; the baseline is run once and reused through the cache for every variant; the confirmation run is a plain evaluate of the cut prompt. The bootstrap is seeded from the experiment id so reruns reproduce the intervals.
- **Budget:** estimate uses the provider's token count for the prompt and the dataset inputs (one counting pass, free or near-free) and a fixed expected output of 300 tokens for the target and 150 for the judge; day two corrects those constants from the real bill.
- **API server:** read-only over the same SQLite file; bind `127.0.0.1`; Host check; the static build is mounted last so `/api` wins.
- **Dashboard 🎨:** four screens, light only, one accent, monospace for prompt text, every colour paired with a word. `DESIGN.md` v1 is written at B14 before any component.
- **Release:** the wheel ships the dashboard build; `uv build` must be run after `npm run build`; a `MANIFEST`-style include in `pyproject.toml` for `api/static/**`.

---

## 8. Final folder structure and file count

```
promptgauge/
├── CLAUDE.md · README.md · CHANGELOG.md · LICENSE · pyproject.toml · uv.lock · .gitignore · .env.example
├── docs/            PRD.md · PLAN.md · DESIGN.md · DISTRIBUTION.md · HANDOFF.md · PRIOR_ART.md · TODO.md
├── examples/
│   ├── support-bot/        promptgauge.yaml · system.md · cases.jsonl
│   └── mailmoat-planner/   promptgauge.yaml · system.md · cases.jsonl · schema.json · report.md
├── src/promptgauge/
│   ├── __init__.py · sdk.py
│   ├── core/        logger.py · errors.py
│   ├── config/      config.py · pricing.py
│   ├── dataset/     case.py · dataset_loader.py
│   ├── prompt/      segment.py · prompt_segmenter.py · variant_builder.py
│   ├── provider/    completion.py · anthropic_provider.py · fake_provider.py
│   ├── cache/       call_cache.py
│   ├── db/          database.py · migrator.py · migrations/001_init.sql · experiment_repository.py · case_repository.py · call_repository.py · result_repository.py · segment_repository.py · verdict_repository.py
│   ├── scorers/     scorer.py · score_result.py · contains_scorer.py · exact_scorer.py · json_schema_scorer.py · rubric_scorer.py · grounded_scorer.py · judge.py · prompts/rubric.md · prompts/grounded.md
│   ├── rubrics/     helpful.md · concise.md · on_topic.md · tone_professional.md · follows_instructions.md
│   ├── runner/      case_run.py · eval_result.py · evaluator.py
│   ├── stats/       bootstrap.py · verdict_rule.py
│   ├── ablate/      ablation_planner.py · budget_planner.py · segment_verdict.py · prompt_cutter.py · ablation_report.py · ablation.py
│   ├── api/         app.py · host_guard.py · models.py · cases_routes.py · experiments_routes.py · ablations_routes.py · settings_routes.py · static/ (built)
│   └── cli/         main.py · eval_table.py · terminal_painter.py
├── dashboard/       package.json · vite.config.js · index.html · src/{main.jsx, App.jsx, api/ApiClient.js, ui/*, screens/{Datasets,Experiments,Ablation,Settings}.jsx, styles.css}
└── tests/           mirrors src: core config dataset prompt provider cache db scorers runner stats ablate api cli · fixtures/prompts/*.md
```

### 8.1 File count (hand-written; excludes lockfiles and `notes/`)

| Area | Files |
|---|---|
| Root config and docs | 9 |
| `.github/` | 2 |
| `docs/` | 7 |
| `examples/` | 8 |
| `src/promptgauge/` | 52 |
| `dashboard/src/` | ≈ 20 |
| **Source + config + docs total** | **≈ 98** |
| Tests | ≈ 35 files, ≈ 250 tests |

---

## 9. Testing strategy

| Level | Tool | What | Runs |
|---|---|---|---|
| Unit | pytest | Every class in `prompt/`, `stats/`, `ablate/`, `scorers/`, `cache/`, `config/`, `dataset/` | Every commit |
| Integration | pytest | `Evaluator` and `Ablation` end to end with `FakeProvider` and in-memory SQLite; the synthetic A/B/C ablation | Every commit |
| API | pytest + httpx | Every route; Host guard | Every commit |
| Live | CLI on `examples/` | Real Anthropic calls, real bill | End of Day 1 (eval), end of Day 2 (ablate), Day 4 (mailmoat) |
| UI | Manual checklist | Four screens, slider repaint, copy button, tooltips | Day 3 |

Coverage target: **≥ 85%** lines on `prompt/`, `stats/`, `ablate/`.

---

## 10. Definition of done

**Block:** its "Done when" is met; tests for every new class pass; `ruff` clean; tracker (§11) updated; Claude has posted the one commit.
**Branch:** all its blocks done; Kaushal pushed, opened the PR, ruff and pytest green locally, merged.
**Day:** explain-back done; next day's first block identified in §11.

---

## 11. Progress tracker

Claude updates this table at the end of every block. New sessions resume from the first unchecked row.

| Block | Status | Notes |
|---|---|---|
| B00 | ☑ | 17 Oct 2026. Skeleton + tooling; `uv sync && uv run pytest` green (0 tests), ruff clean, wheel builds. Dev deps moved to `[dependency-groups]`; entry point fixed to `cli.main:app`. |
| B01 | ✂ | Cut 17 Oct 2026 (Kaushal's call): no GitHub Actions. `.github/` deleted; lint and tests run locally before every merge. |
| B02 | ☑ | 17 Oct 2026. core (errors, Logger, clock), config (Config, ScorerSpec, Pricing dated 2026-10-17), db (Database, Migrator, 001_init.sql, six repositories). 60 tests. `call.hash` is indexed, not the PK, so a cache hit in a later experiment gets its own `cached=1` row (F2.6). |
| B03 | ☑ | 17 Oct 2026. dataset (`Case`, `DatasetLoader` → `Dataset(path, hash, cases)`). Hash = SHA-256 of canonical JSON per case, so whitespace, key order and blank lines do not change it; content and order do. Bad line → `DatasetError` as `path:line: field: message`. `expected: ""` / `context: ""` become `None` so scorers skip them (F3.1, F3.4). 92 tests. |
| B04 | ☑ | 17 Oct 2026. provider (`Completion`, `Provider` protocol, `AnthropicProvider`, `FakeProvider`), cache (`CallCache`). `CallCache.complete()` is async, owns the `concurrency` semaphore (F2.5; hits never wait), returns a `Completion` with `cached` and `call_hash`; the key ignores `max_tokens` and `experiment_id`. Provider errors propagate without a call row. Refusals are returned as output, not raised. 116 tests. Live smoke (haiku, 1 call + 1 hit) still to be run by Kaushal: no key in the dev shell. |
| B05 | ☑ | 17 Oct 2026. scorers (`ScoreResult`, `Scorer` base, `ContainsScorer`, `ExactScorer`, `JsonSchemaScorer`, factories `contains()/exact()/json_schema()`). `Scorer.score()` is async so judge scorers share one interface at B06; `applies_to(case)` is the skip rule (no row, not a zero). `normalise()` is shared by contains and exact. Schema file is validated at construction (`ScorerError`). `JsonSchemaScorer.key` uses the schema file name. 166 tests. |
| B06 | ☑ | 17 Oct 2026. scorers (`Judge`, `RubricScorer`, `GroundedScorer`, factories `rubric()/grounded()`). `Judge(cache, model, experiment_id, logger)` is built per experiment by the runner and handed to scorers via `Scorer.bind(judge)`, because SDK users build scorers before a run exists. Retry uses repeat index 1 so it cannot hit the cached malformed answer. `parse_json()` (fence-tolerant) moved to `scorer.py`, shared with `JsonSchemaScorer`. Grounded: no claims → 1.0. 209 tests. |
| B07 | ☑ | 17 Oct 2026. runner (`CaseRun`, `EvalResult` + `CaseSummary`, `Evaluator`), cli (`main.py` composition root: `build_provider`, `build_scorers`, `open_database`, `run_evaluation`; `EvalTable`; rich progress line), `sdk.evaluate()` reuses `run_evaluation`. Experiment status `partial` on any failed call; exit 1. Totals from the call table. Judge verdicts are shared across repeats with identical outputs (same cache key). Config now resolves a `rubric:` value to a path when that file sits next to the config. 230 tests. **Milestone 1 live run pending** (no key in the dev shell). |
| B08 | ☑ | 17 Oct 2026. prompt (`Segment`, `PromptSegmenter`, `VariantBuilder`); `PromptError` added to core/errors. Offsets are absolute for blocks and lines alike, so `VariantBuilder(text).without(segment)` is one slice at either level. `PromptSegmenter(count_tokens=None)`: tokenizer injected (prompt/ never imports provider/); default is `max(1, len//4)`. Heading = its own block when followed by a blank line (`# Role` is ablatable); `lines()` always returns ≥ 1, so a block with exactly one line is the "single-line block" of F6.6 (headings, one-sentence paragraphs, fences alike). Fenced code (``` or ~~~) is one block, or one line when glued to text. Indented continuation lines belong to their list item. Sentence split accepts the `e.g. The` false positive. Variant whitespace rule: keep the larger newline count of the two gaps plus the next line's indentation; first/last segment removal strips the gap and keeps the file's final newline. 319 tests. |
| B09 | ☑ | 17 Oct 2026. stats (`MeanInterval`, `Bootstrap`, `VerdictRule`). `Bootstrap(seed=0).mean_ci(diffs, resamples=1000, level=0.95)` returns a `MeanInterval(mean, ci_low, ci_high, n_cases)`; a fresh numpy generator per call, so results do not depend on call order. Interval is clamped to contain the sample mean. `VerdictRule(delta).verdict(ci_low, ci_high)` takes raw bounds so the API can repaint from verdict rows (F6.5); boundaries (`ci_high == -delta`) are grey. Bad arguments raise `ValueError` (programming contract, not a user error). 358 tests. |
| B10 | ☑ | 17 Oct 2026. ablate (`StagePlan`, `AblationPlanner`, `BudgetEstimate`, `BudgetPlanner`). `AblationPlanner(segmenter, cases, repeats)`: `stage_one(text)` = baseline + blocks, or + lines when the prompt has one block (F5.5); `stage_two(red)` = lines of multi-line red blocks only (single-line blocks stay whole, F6.6); `stage_two_candidates(text)` = all such lines, for the estimate. `BudgetPlanner(pricing, budget_usd)`: `estimate(model=, judge=, judge_scorers=, prompt_tokens=, cases=, repeats=, stage_one_variants=, stage_two_candidates=)` prices stage one + ceil(30% of candidates) + 1 confirmation run, target calls at prompt+case+300 output tokens and one judge call per judge scorer per output (400+case+300 in, 150 out); constants tuned at B12. Over budget the estimate carries three suggestions (largest repeats that fits; largest tag subset, else a case count; priciest cheaper model) and `require_within_budget()` raises `BudgetExceededError` with them in the message (CLI exits 2 at B12). `exceeded(spend)` is the running-stop rule; `Ablation` (B11) checks it between variants and writes `stopped: budget`. **Name clash found:** `promptgauge.ablate` is both the `ablate/` subpackage and the SDK function; the first import of the subpackage overwrote the function. Fixed in `promptgauge/__init__.py` by importing the subpackage before binding the SDK names (why-comment there). Renaming the subpackage is the cleaner alternative if Kaushal prefers it. 390 tests. |
| B11 | ☑ | 17 Oct 2026. ablate (`SegmentVerdict`, `PromptCutter`, `AblationReport`, `Ablation`), `run_ablation()` in cli/main.py (shares `_live_provider`/`_build_evaluator` with `run_evaluation`), `sdk.ablate()` (shares `_config_and_scorers` with `evaluate()`). `Evaluator.run()` split into `start(kind=…)` (experiment row, cases, judge binding) + `measure(experiment_id, …, variant_id=, store=, progress=)` + `run()`; result rows carry `variant_id`. One experiment per ablation (`kind='ablation'`); the confirmation run is measured with `store=False` (no segment to label it) and lives in the `ablation` row as `cut_score` + CI. Flow: estimate → `require_within_budget` (before any row or call) → baseline → stage one → stage two → cut → `exceeded()` check between every variant → confirmation. Stops raise `BudgetExceededError` / new `AblationError` (every case failed) and are caught: verdicts so far are written, status `stopped` + `stopped_reason`, ablation row with `cut_score NULL`, `confirmed 0`. Cutter: unmeasured segments stay; a red block whose lines were all grey stays whole; deletions applied last-to-first through `VariantBuilder`. Added `Scorer.uses_judge` (budget counts judge calls) and `PromptSegmenter.tokens()`. Synthetic AC passes: A red, B grey, C green, cut = A only, confirmation row written. 413 tests. |
| B12 | ☑ | 17 Oct 2026. cli (`TerminalPainter`, `promptgauge ablate --config --calls-per-month`), `Config.inr_rate` (default 84, F6.9). Painter: `paint(report)` returns a rich `Text` with each measured segment on its DESIGN.md soft colour (stage-two lines paint over their block; unmeasured text stays plain), `render()` prints header, stopped line, prompt, legend with the word for every colour (grey = "no measurable effect at this sample size"), the >80%-grey hint, the confirmation line (`confirmed` / `cut prompt not confirmed` + "shown as a suggestion"), tokens before → after with USD and INR saved at `calls_per_month`, calls/cached/cost/time. `<prompt>.cut.md` is written only when a confirmation run exists (invariant 5). Exit codes: 2 over budget (`BudgetExceededError`, zero calls), 1 stopped run or other error, 0 done. Offline estimate for support-bot as configured: ~390 calls ≈ $2.51 vs `budget_usd: 1.00`, so the live run exits 2 until the budget is raised or the token constants are tuned. **Milestone 2 live run pending** (no key in the dev shell): compare the `call` table's mean tokens per model to `EXPECTED_OUTPUT_TOKENS` / `JUDGE_*` in budget_planner.py and tune. 424 tests. |
| B13 | ☑ | 17 Oct 2026. api (`App` factory, `HostGuard`, `models.py`, `CasesRoutes`, `ExperimentsRoutes` incl. compare, `AblationsRoutes`, `SettingsRoutes`, `ScoreSummary`, `/api/health`), db (`SettingsRepository`, the seventh repository), cli (`build_app`, `promptgauge ui --config --port --open-browser`). `App(database, config|None, key_present, logger, port=, static_dir=).build()`; `api/` imports only `db/`, `config/`, `core/`, `stats/` (invariant 6). `HostGuard` is pure ASGI: Host must be exactly `127.0.0.1:<port>` or `localhost:<port>` (case-insensitive), else 403 before any route. `/` serves `api/static` when `index.html` exists, else a 404 "dashboard not built" line. `ScoreSummary` recomputes means from baseline result rows the way `EvalResult` does (run score = mean of its non-null scorer values), so the dashboard matches the CLI. `GET /api/ablations/{id}` repaints every colour with `VerdictRule(delta)` from `config_json` (default 0.03) and carries a `legend` whose grey entry is the invariant-4 wording; unmeasured segments have `verdict: null`, a stopped run has `ablation: null`. `GET /api/settings` echoes `Config.model_dump(mode="json")` (null without a config), `api_key_present` from an injected callable (the key never enters the API), `calls_per_month` default 100000 and `inr_rate` default `Config.inr_rate`/84; `PUT` accepts only those two keys (`extra="forbid"` → 422). 500s log method, path and `repr(exc)`; the body is only "internal server error". `ui` loads `promptgauge.yaml` if present (project dir = its folder, else cwd), opens the browser from a `threading.Timer` after uvicorn binds. Smoke-tested live on examples/support-bot. No new dependencies (fastapi, uvicorn, httpx were in pyproject since B00). 465 tests. |
| B14 | ☑ | 17 Oct 2026. `docs/DESIGN.md` rewritten to v1 first: §0 records the decisions (CSS wordmark of three verdict discs, no sidebar collapse, hover-card row order, cut prompt as two columns not a diff, no illustrations, JSX not TS, stack pins), §2 adds the number-format table, §6 the routes (`/` → `/experiments`, `/ablations` lists ablation runs), §7 maps each component to its block, §8 maps every API field to its screen and repeats the verdict rule the slider applies client-side (the one UI/Python duplication; keep in sync with `tests/stats/test_verdict_rule.py`). `dashboard/`: Vite 6.4 (Node 20.9 in the dev shell; Vite 7/8 need 20.19+), React 19.3, Tailwind 4.3 via `@tailwindcss/vite`, `react-router` 7.18, `@phosphor-icons/react`, `@fontsource-variable/inter` + `jetbrains-mono` (bundled, nothing loaded from the network). `src/api/ApiClient.js` (one method per route, throws `ApiError(status, detail)`; 403 → "refused: open the dashboard at 127.0.0.1:7331", 422 bodies flattened to `field: msg`), `App.jsx` (routes, one client), `ui/Sidebar.jsx` (wordmark, four NavLinks, project and db path from `/api/health`), `ui/TitleRow.jsx`, `ui/EmptyState.jsx`; the four screens are title + empty state with the CLI command until B15–B17. `styles.css` holds every DESIGN token under `@theme`. `vite.config.js` builds into `src/promptgauge/api/static` and a 10-line plugin restores `.gitkeep` after `emptyOutDir`; dev proxy to :7331 with `changeOrigin` so HostGuard passes. **API change:** `App._mount_static` now mounts `/assets` and serves `index.html` for every other non-API GET (deep links like `/ablations/3` open the SPA route); unknown `/api/*` stays a JSON 404; a path outside `static/` gets the shell, not the file. Verified: `npm run build` (≈ 290 kB JS, 16 kB CSS, fonts) then `promptgauge ui` serves `/`, `/experiments`, `/ablations/3` as the shell and the hashed assets with the right types. `@vitejs/plugin-react` 5.x prints an EBADENGINE warning on Node 20.9 but builds; upgrading Node to 20.19+ silences it. 465 tests. |
| B15 | ☑ | 17 Oct 2026. dashboard `ui/`: `Table` (sortable headers, nulls last, 36 px rows, row click + selected bar), `Tag`, `StatusTag` (done ok / partial warn / `stopped: reason` warn / running), `SidePanel` (360 px, hidden under 1100 px until the B17 dialog), `CodeBlock` (mono, copy button, danger tone for a failed output), `Panel`, `Dash`, `SearchInput`, `useRequest.js` ({data, error, loading}, stale answers dropped), `format.js` (DESIGN §2 formats). `screens/Datasets.jsx` (F8.1): newest dataset by default, `<select>` to switch, search over input/expected/context/tags, row click → side panel with the full text. `screens/Experiments.jsx` (F8.2): runs table with one column per scorer key (union over runs), cases, calls · cached, cost, duration, date, status; row click → `/experiments/:id` (ablation rows → `/ablations/:id`); two checkboxes → Compare button → `/experiments?a=&b=` (per-scorer and per-case tables, signed deltas coloured ok/danger). Detail: header strip, per-case table grouped by (variant, case, repeat) with output, expected (from the dataset), one cell per scorer; `score: null` → "failed" tag and a tinted row; side panel shows input, output, expected and each scorer's score with the judge reason verbatim, labelled. Ablation runs get a "show variants" toggle (variant rows hidden by default). **API change:** `ExperimentSummary.cases` (distinct baseline cases) and `ExperimentDetail.case_scores` (was `cases`, which the count now takes). Verified offline: a scratch copy of support-bot seeded with FakeProvider (two evals, one ablation of 8 verdicts) through `run_evaluation`/`run_ablation`; every route the screens read returns the expected shape; `npm run build` ≈ 319 kB JS. **Not seen in a browser** (no browser tooling in this session): Kaushal's visual pass is the B17 AC. 465 tests. |
| B16 | ☑ | 17 Oct 2026. **Milestone 3 (offline).** dashboard `ui/`: `verdictRule.js` (the stats rule repeated for the slider; checked against the Python table), `deletions.js` (LCS over word and whitespace tokens → removed runs of the original; deletion only makes the cut a subsequence), `PaintedPrompt` (blocks in document order, lines nested inside their block, own colour wins, unmeasured lines transparent so the block shows through), `SegmentSpan` (Radix HoverCard, click pins), `SegmentCard` (word · baseline → without · delta · 95% interval · n cases · tokens · level, plus the text), `Slider` (Radix, 0–0.20 step 0.01), `VerdictLegend` (word + count per colour at the current delta), `StatTile`, `CutPromptPanel` (two columns, removed runs struck through on red soft; tokens before → after (−n, −%); baseline, cut [lo, hi], `confirmed` / `cut prompt not confirmed` with the CLI's wording; USD and INR at `calls_per_month`, saved through `PUT /api/settings`; primary Copy button). `screens/Ablation.jsx`: `/ablations` lists ablation runs, `/ablations/:id` = title + status + slider, stopped banner (warn soft), six stat tiles, legend, the >80%-grey hint, painted prompt, cut panel; pinned segment in the right panel. Painting and counts follow the slider with no request (F8.3). **API change:** `AblationOut.input_usd_per_million` (from `Pricing`, injected into `AblationsRoutes` and `App`; null for a model no longer priced, tested). `radix-ui` 1.8 added (HoverCard, Slider now; Tooltip, Dialog at B17). DESIGN §6 changed: the cut panel lives under the painted prompt in the main column; the right panel holds the pinned card. Verified in Node against a seeded support-bot ablation (scratch copy, prompt-aware FakeProvider: refund rule red, Style block green, 13 segments with stage-two lines, cut confirmed 0.59 → 0.83, 151 → 21 tokens): rule table 7/7, every segment offset matches `prompt_text`, repainting at the run's delta reproduces every stored colour, the diff's kept tokens equal the cut prompt, slider flips green → grey at 0.20. **Not seen in a browser**; the live support-bot run is B18. `npm run build` ≈ 405 kB JS. 466 tests. |
| B17 | ☑ | 17 Oct 2026. Built; **Kaushal's visual pass over the four screens is still owed** (no browser in the session). `screens/Settings.jsx` (F8.4): key present / missing as a tag with the word, never the key; run config from the newest experiment's `config_json` (else the promptgauge.yaml echo, else an empty state); `calls_per_month` and `inr_rate` inputs with one primary Save (disabled until valid and changed), `PUT /api/settings`, "saved" word. F8.5: `ui/Tooltip.jsx` (Radix, 300 ms) and `TooltipProvider` at the App root; `Tag tip=` and `Swatch word=` carry the word on every coloured element: status tags (done / partial / stopped: reason / running with a sentence each), failed cells, compare deltas (higher / lower under b), confirmation tags, legend and card swatches; tinted rows and the stopped banner use `title`. `SidePanel` renders as a Radix Dialog under 1100 px (`ui/useMediaQuery.js`), so the Datasets, Experiment and Ablation detail views work on a narrow window. Empty states exist on every screen (datasets, runs, ablations, results, settings without a run). README screenshots: not taken (need a browser); they belong with F9.3 once the live support-bot and mailmoat runs exist (B18–B20). `npm run build` ≈ 441 kB JS. 466 tests. |
| P1 | ☑ | 17 Oct 2026. UI polish group 1 (`docs/UI_POLISH.md` items 1, 2, 3, 4, 6, 18). DESIGN.md first: §1 neutral zinc tokens with the indigo accent, §2 titles at 600 and the `61 %` share format, §5/§6 sidebar 220 px with a `surface-3` active pill and the spend card, title row with type icon and breadcrumb (no back arrow), §7 `SpendCard`, `TitleRow`, `StatusTag`, button classes, §8 the sidebar's routes. Code: `styles.css` tokens and `btn` / `btn-primary` / `btn-secondary`; `ui/SpendCard.jsx` (project name, `Spend` + USD, `runs · % cached`, 4 px cached-share bar, database path as tooltip, refetches on every route change); `Sidebar` (220 px, `Project` label, no accent on the nav); `TitleRow` (`Icon`, `crumb`); `StatusTag` icon + word (Check / Warning / Square / CircleDashed); side-panel titles 600; "show variants" is a secondary button; Compare, Save and Copy cut prompt use `btn-primary`. **API change:** `GET /api/summary` → `SummaryOut(runs, calls, cached, cost_usd)` via `SummaryRoutes(ExperimentRepository, CallRepository)`, `CallRepository.grand_totals()`, `ExperimentRepository.count()`; PRD §13 lists it. Items 11 (`…` menu) stays in P4. Verified offline on a reseeded scratch support-bot (budget raised to $5 in the copy, else the planner refuses at $2.51): summary 3 runs · 900 calls · 488 cached · $0.23, SPA deep link 200. **Not seen in a browser**; Kaushal's visual pass is still owed. `npm run build` ≈ 463 kB JS. 469 tests. |
| B18 | ☐ | |
| B19 | ☐ | |
| B20 | ☐ | |

---

## 12. v0.2 candidates

Pairwise interaction checks on red lines; pytest plugin; promptfoo YAML import; OpenAI provider. See PRD §19.
