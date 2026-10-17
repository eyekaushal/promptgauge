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
| B07 | ☐ | |
| B08 | ☐ | |
| B09 | ☐ | |
| B10 | ☐ | |
| B11 | ☐ | |
| B12 | ☐ | |
| B13 | ☐ | |
| B14 | ☐ | 🎨 rewrite DESIGN.md to v1 first |
| B15 | ☐ | 🎨 |
| B16 | ☐ | 🎨 |
| B17 | ☐ | 🎨 |
| B18 | ☐ | |
| B19 | ☐ | |
| B20 | ☐ | |

---

## 12. v0.2 candidates

Pairwise interaction checks on red lines; pytest plugin; promptfoo YAML import; OpenAI provider. See PRD §19.
