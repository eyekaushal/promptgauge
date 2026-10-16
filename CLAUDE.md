# CLAUDE.md — promptgauge

promptgauge is a local Python tool that tells a developer which lines of their system prompt actually do anything, with measured proof, and hands them a shorter prompt that scores the same. An eval runner (`evaluate`) underneath, a deletion-based ablation (`ablate`) on top, a FastAPI + React dashboard that reads the results. The method is ProCut's (EMNLP 2025); the tool is ours.

## Source of truth (in this order)
1. `docs/PRD.md` — what: features F1–F9, classes, data model, API, LLM usage.
2. `docs/PLAN.md` — how: blocks, branches, schedule; **§11 is the progress tracker**.
3. `docs/DESIGN.md` — the UI law (v0 now; rewritten at the start of the UI branch).
4. `docs/DISTRIBUTION.md` — PyPI, bring-your-own-key, docs site; all $0.
5. `docs/HANDOFF.md`, `docs/PRIOR_ART.md` — origin notes and the competitor comparison; cite ProCut in README and docs.
Read docs by section when a block needs them; do not re-read them in full.

## Session routine
- Start: read `docs/PLAN.md §11`, continue with the first unchecked block (confirm with the user if unclear).
- Per block: implement → run tests → update the §11 tracker row → post a summary of **≤ 10 lines**: what changed, how to verify, and exactly **one `git add`, one `git commit` (Conventional Commit message), then `git push`** for the user to run. Never split a block into several commit groups.
- Read files narrowly; keep test output quiet; **no subagents** unless the user asks.
- If behind schedule, cut only from `PLAN.md §6`. Never cut the ablation core (B08–B12).

## Git — hard rules
- **Never run any git command** (status, add, commit, branch, checkout, push, tag — nothing) unless the user explicitly asks for that exact command. The user runs all git by hand.
- **Never add AI attribution** anywhere: no `Co-Authored-By`, no "Generated with Claude Code", in commits, PRs, code, or docs. Kaushal is the sole author.
- Commits: Conventional Commits `type(scope): summary`. Types: `feat fix refactor test docs chore ci build perf style`. Scopes: `core config dataset prompt provider cache db runner scorers ablate stats api ui docs ci`.
- Branches: Conventional Branch `feature/… bugfix/… hotfix/… chore/… release/…`, lowercase-hyphenated; `main` is the trunk. Branch list is in `PLAN.md §3.1`.

## Model rule
Before any UI work (`dashboard/`, PLAN blocks marked 🎨) stop and tell the user: **"We are starting UI now — rewrite DESIGN.md to v1 first, then build."**

## Commands
```bash
uv sync                                                        # Python 3.11+, all deps incl. dev
uv run promptgauge eval --config examples/support-bot/promptgauge.yaml
uv run promptgauge ablate --config examples/support-bot/promptgauge.yaml
uv run promptgauge ui                                          # http://127.0.0.1:7331
uv run pytest -q                                               # tests never call the network
uv run ruff check . && uv run ruff format .
cd dashboard && npm install && npm run build                   # → src/promptgauge/api/static
```

## Code style
- **Python 3.11+**, `uv`, `ruff`. Type hints on every public signature; docstrings on public classes and methods. **Pydantic** for all runtime validation (config, dataset rows, judge output, API input).
- **OOP:** one class per file, file named after the class in snake_case (`BudgetPlanner` lives in `budget_planner.py`). Small public methods; private helpers prefixed with a single underscore. Dependencies passed through the **constructor**; objects are wired once in `src/promptgauge/cli/main.py` (composition root). No singletons, no DI framework, no module-level state.
- **KISS, YAGNI:** build only what the current block needs; no speculative options, layers or abstractions. DRY only where duplicated logic must stay in sync for correctness.
- No barrel re-export modules; import from the source file. The one exception is `promptgauge/__init__.py`, which exposes `evaluate`, `ablate` and `scorers` because that is the public SDK surface.
- Comments explain **why**, not what.
- Errors: raise typed errors from `core/errors.py`; never swallow errors silently.
- Logging: use `Logger`; never log API keys. Prompt and case text may be logged only at `debug`.
- New dependencies must be justified in the block summary.

## Invariants — never break these
1. **Only `AnthropicProvider`** talks to the network. Every model call goes through it and through `CallCache`.
2. **Deletion only.** Prompt variants are the original text minus whole segments. No rewriting, no summarising, no model-generated prompt text, ever.
3. **The budget planner runs before the first call** of an ablation and refuses to start over `budget_usd`. A running ablation stops when spend crosses the budget and writes what it measured.
4. **Grey means "no measurable effect at this sample size"**, never "does nothing". That wording appears in CLI output, the dashboard and the docs.
5. **The cut prompt is never reported as a result without its confirmation run** against the baseline.
6. **The dashboard never calls a model.** It reads SQLite through the API; nothing else.
7. **Tests never call live APIs.** `FakeProvider` and recorded fixtures only. Live runs happen through the CLI on the examples.
8. The API key is read from `ANTHROPIC_API_KEY` only, never stored in SQLite or config, never returned by the API (`/api/settings` reports present/missing).

## Testing
- pytest. Tests live in `tests/`, mirroring `src/promptgauge/` (`tests/ablate/test_verdict_rule.py`).
- Every new class gets tests; the verdict rule and the segmenter get a table of positive and negative cases; every bug fix gets a regression test.
- Prefer real objects with small fakes at boundaries (`FakeProvider`, in-memory SQLite).

## Layout
```
src/promptgauge/   the package: core config dataset prompt provider cache db runner scorers ablate stats api cli rubrics
dashboard/         React 19 + Vite + Tailwind (UI branch) → built into src/promptgauge/api/static
examples/          support-bot (10 cases) for the first real runs
tests/             pytest, mirrors src
docs/              PRD, PLAN, DESIGN, DISTRIBUTION, HANDOFF, PRIOR_ART
notes/             private planning — gitignored, never reference in code
```
