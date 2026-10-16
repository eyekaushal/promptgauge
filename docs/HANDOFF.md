# promptgauge: build handoff

Written 16 Oct 2026. Builder: Kaushal. Reviewer: Sujay. Ship: Tuesday 20 Oct 2026.
Origin notes, 16 Oct 2026. Superseded by `docs/PRD.md` (what) and `docs/PLAN.md` (how) on 17 Oct 2026; where they differ, the PRD and PLAN win. Kept for the reasoning behind the decisions.

## What it is

A Python tool that tells a developer which lines of their system prompt actually do anything, with measured proof, and hands them a shorter prompt that scores the same.

Three parts in one repo and one PyPI package:

- SDK: `evaluate()` and `ablate()`, importable functions.
- CLI: `promptgauge eval`, `promptgauge ablate`, `promptgauge ui`. Thin wrappers over the SDK.
- Dashboard: React app served locally by FastAPI, reads the results database, never calls a model.

Everything runs on the developer's machine with their own Anthropic key. No hosted service, no telemetry, nothing leaves the laptop.

## Decisions already made

- Language: Python 3.11+. Package on PyPI as `promptgauge`. Dashboard in React 19 with Vite, built once and shipped inside the wheel as static files.
- Storage: one SQLite file, `.promptgauge/promptgauge.db`, in the project directory.
- Models: Anthropic only in v1. The target model is whatever the developer configures. The judge defaults to Claude Haiku.
- Demo budget: $5 to $10 on an Anthropic key, total, for the mailmoat Planner prompt demo.
- Out of scope for v1: OpenAI and other providers, tool-description ablation, few-shot example ablation, hosted anything, auth, teams, prompt versioning UI, more than four scorers.

## Prior art, and what promptgauge takes from each

Read `docs/PRIOR_ART.md` for the full comparison. The short version:

- **ProCut** (Xu, Li, Chen, Wang. "LLM Prompt Compression via Attribution Estimation", EMNLP 2025 Industry Track). The closest work and the method we are implementing. Segment-level attribution of a prompt via leave-one-out, Shapley, or an LLM-driven estimator; 30 to 40% of tokens removed on production prompts with comparable performance. No code released. promptgauge is ProCut's leave-one-out method shipped as a tool, with the pieces the paper does not have: a developer workflow, repeated runs with confidence intervals, a budget planner, a confirmation run, a dashboard, and money saved. Cite it in the README and the docs site. Do not pretend the idea is new; the tool is.
- **Claude Code's ablation playbook** (Boris Cherny). The team cut about 80% of their system prompt by removing lines and bringing them back only on measurable failure, by hand. Public proof the method works at the top. promptgauge automates that playbook.
- **"The load-bearing vocabulary of Claude"** (Show HN, Aug 2026, 710 points). Proof that developers want to know which words matter. Our red/grey/green vocabulary comes from there.
- **LLMLingua / LLMLingua-2** (Microsoft). Token-level compression by perplexity. Different unit, different goal. We cut whole instructions a human can read; it drops tokens.
- **DSPy GEPA and MIPROv2, Opik optimizer.** They rewrite prompts to maximise a metric. We explain the prompt the developer already has. Complementary, and GEPA's trick of having a model explain a failure is worth borrowing later for the "why does this line matter" card.
- **promptfoo, Braintrust, Langfuse, LangSmith, DeepEval, RAGAS.** Eval runners and platforms. None runs an ablation. Their dataset formats are import targets after v1.
- **HiveMind DAG-Shapley** (Dec 2025). Cheaper Shapley attribution. The algorithm to borrow if pairwise interaction checks become a real feature.

## The developer's experience

1. `pip install promptgauge`
2. A dataset file, `cases.jsonl`, one case per line:
   ```json
   {"input": "...", "expected": "...", "context": "...", "tags": ["billing"]}
   ```
   `expected` and `context` are optional. `expected` is for match scorers. `context` is for groundedness.
3. A config file, `promptgauge.yaml`:
   ```yaml
   prompt: prompts/system.md
   dataset: cases.jsonl
   model: claude-sonnet-5-5
   judge: claude-haiku-5-5
   scorers:
     - contains
     - rubric: rubrics/helpful.md
   repeats: 3
   budget_usd: 2.00
   ```
4. `promptgauge eval` runs every case, scores it, stores it, prints a table.
5. `promptgauge ablate` does the full ablation and prints the painted prompt in the terminal plus the cut prompt to a file.
6. `promptgauge ui` opens the dashboard.

The same two things from code:

```python
from promptgauge import evaluate, ablate, scorers

result = evaluate(
    dataset="cases.jsonl",
    prompt="prompts/system.md",
    model="claude-sonnet-5-5",
    scorers=[scorers.contains(), scorers.rubric("rubrics/helpful.md")],
)

report = ablate(
    dataset="cases.jsonl",
    prompt="prompts/system.md",
    model="claude-sonnet-5-5",
    repeats=3,
    budget_usd=2.0,
)
print(report.cut_prompt)
```

## The four scorers

Each scorer takes (input, output, expected, context) and returns a float in [0, 1] plus an optional reason string. No more than these four in v1.

1. `contains`. 1.0 if `expected` appears in `output` (case-insensitive, whitespace-normalised), else 0.0. Variant `exact` for full equality. Deterministic, free.
2. `json_schema`. Parses `output` as JSON, validates against a schema given in the config. 1.0 or 0.0, reason is the first validation error. Deterministic, free.
3. `rubric`. Sends input, output and a rubric file to the judge. Judge returns `{"score": 0..1, "reason": "..."}` as JSON, enforced by a strict response format. Ship five starter rubrics in `promptgauge/rubrics/`: helpful, concise, on_topic, tone_professional, follows_instructions. Every metric in DeepEval's catalogue is one of these with different wording; the tool does not pretend otherwise.
4. `grounded`. Sends output and context to the judge. Score is the fraction of claims in the output supported by the context. Reason lists the unsupported claims. This is the RAG scorer.

Judge calls use a fixed prompt, temperature 0, and the result is cached by hash of (judge model, rubric, input, output).

## The runner

`evaluate()`:

- Loads prompt, dataset, config.
- For each case, for each repeat, calls the target model with the system prompt and the case input. Temperature as configured, default 0.7, because ablation must measure the prompt under the sampling the developer actually uses.
- Caches every model call by hash of (model, system prompt, input, temperature, repeat index). A rerun with an unchanged prompt costs nothing. The same cache is what makes ablation affordable, because the baseline is reused across every variant.
- Concurrency: an asyncio semaphore, default 8 in flight, respects 429 with backoff.
- Scores every output with every configured scorer.
- Writes an `experiment` row and one `result` row per (case, repeat, scorer).
- Returns an object with per-scorer mean, per-case table, total cost, duration.

## The ablation algorithm

This is the project. Get this right before touching the dashboard.

Segmentation, plain code, no model:

- Split the prompt into blocks on blank lines and markdown headings. Each block is a unit.
- Inside a block, lines are units. A bullet is a line. A sentence inside a paragraph is a line, split on sentence boundaries.

Variants, by deletion only:

- Baseline: the full prompt.
- One variant per block: the prompt with that block removed. The text is otherwise untouched.
- Stage two, only for blocks judged red: one variant per line inside that block, the full prompt with that one line removed.

Measurement:

- Run baseline and every variant through the same cases with the same number of repeats.
- For each variant, compute the per-case score difference against baseline (variant score minus baseline score, averaged over repeats and scorers).
- Bootstrap the mean difference across cases, 1,000 resamples, to get a 95% confidence interval.
- Verdict rule, with a threshold `delta` defaulting to 0.03:
  - Red (load-bearing): the whole interval is below `-delta`. Removing it hurts, and the data is good enough to say so.
  - Green (harmful): the whole interval is above `+delta`. Removing it helps.
  - Grey (no measurable effect): everything else, including intervals that straddle zero. Grey means "could not detect a difference at this sample size", and the UI must say that, not "does nothing".

Cut prompt:

- The original prompt minus every grey and green segment. Red blocks keep only their red lines.
- Then one confirmation run of the cut prompt against the cases, reported side by side with the baseline. If the cut prompt scores below baseline minus `delta`, the tool says so and keeps the cut prompt as a suggestion, not a result.

Budget planner, before any call is made:

- Calls = (1 + number of blocks) x cases x repeats for stage one, plus lines-in-red-blocks x cases x repeats for stage two, which is estimated at 30% of blocks going red.
- Cost = estimated tokens x the model's price. Print the estimate and refuse to start if it exceeds `budget_usd`, with the three cheapest ways to get under it: fewer repeats, fewer cases by tag, Haiku as the target.
- Stop mid-run if the running spend crosses the budget, and write what was measured so far.

Interactions, stretch goal: for every pair of red lines in the same block, one variant with both removed. If the pair's drop is much larger than the sum of the two single drops, mark them "paired" in the UI. Skip this if day two runs long.

Money saved: tokens removed x price per input token x calls per month, where calls per month is a number the developer types in the dashboard, default 100,000.

## Database

Tables, all in SQLite:

- `experiment`: id, kind (eval or ablation), prompt_hash, prompt_text, model, judge, config_json, created_at, cost_usd, duration_s.
- `case`: id, dataset_hash, input, expected, context, tags_json.
- `call`: hash (primary key), model, system_prompt_hash, input_hash, temperature, repeat_index, output, input_tokens, output_tokens, cost_usd, created_at. This is the cache.
- `result`: experiment_id, case_id, repeat_index, scorer, score, reason, call_hash.
- `segment`: experiment_id, segment_id, parent_segment_id, level (block or line), start_offset, end_offset, text.
- `verdict`: experiment_id, segment_id, mean_delta, ci_low, ci_high, n_cases, verdict (red, grey, green), tokens.

## Dashboard, four screens

Served at `localhost:7331` by FastAPI, reading the SQLite file through a small JSON API. React 19, Vite, Tailwind. Same shape as contextlab's dashboard.

1. Datasets. Table of cases: input, expected, context, tags. Row click opens full text. Search box. Nothing else.
2. Experiments. Table of runs: name, kind, model, mean score per scorer, cost, duration, date. Click one: per-case table with input, output, expected, each scorer's score and reason, red cells for failures. Select two: a diff view showing cases that improved and regressed.
3. Ablation. The prompt as text, every segment painted red, grey or green. Hover shows baseline score, score without this segment, the interval, n cases. A slider for `delta` repaints live from stored verdicts, no recomputation. A "cut prompt" panel: original and cut side by side, token counts, the confirmation run's score next to baseline, a calls-per-month input and the rupees and dollars saved, a copy button.
4. Settings. Model, judge, budget, API key status (present or missing, never the key itself).

The ablation screen is the demo. Build it last but design it first, on paper, before day one ends.

## Build order

Six hours a day. Each day ends with something runnable.

- Friday 16 Oct. Repo, package skeleton, config loading, dataset loading, the `call` cache, the async runner, the four scorers, `evaluate()`, SQLite schema, `promptgauge eval` printing a table. Tests for scorers and the cache. Sketch the four screens on paper.
- Saturday 17 Oct. Segmentation, variants, the two-stage plan, the budget planner, bootstrap intervals, verdicts, cut prompt, confirmation run, `promptgauge ablate` printing the painted prompt in the terminal with ANSI colours. Tests for segmentation and the verdict rule with synthetic scores. Run the first real ablation on a small prompt with 10 cases to check the cost estimate against the real bill.
- Sunday 18 Oct. FastAPI server and JSON API. Dashboard screens 1 and 2, then screen 3. Screen 4 is an hour.
- Monday 19 Oct. The mailmoat Planner prompt ablation, the real demo, inside the $10 budget. Fix whatever that run exposes. README with a GIF of the ablation screen. Docs site: getting started, the four scorers, ablation, config reference. One evening, no more.
- Tuesday 20 Oct. Tests to a respectable count, `pip install` on a clean machine, PyPI publish, three-minute demo video, GitHub release. Update profile, resume, email and LinkedIn bullets.

## The demo

Ablate mailmoat's Planner system prompt with 40 cases drawn from the attack lab and benign set, 3 repeats, Haiku as judge, Sonnet as target. The output sentence we want on the README: "N lines carry the behaviour, M tokens do nothing, here is the cut prompt and it scores the same." If the Planner prompt turns out to be all red, that is also a result, and a good one for mailmoat.

## Things that will go wrong

- Noise. One run per line is noise, which is why repeats and intervals exist. Do not lower repeats below 3 to save money; lower cases instead.
- Grey everywhere. With 10 cases, most intervals straddle zero. The UI must explain this. The fix is more cases, and the tool should say so.
- The cut prompt scoring lower than baseline. Report it honestly. The tool's credibility is the confirmation run.
- Cost drift. Check the planner's estimate against the real bill on Saturday and fix the token estimate before Monday.
- Dashboard scope. Four screens. If a fifth idea appears, write it in a TODO file.

## Stretch goals, in order, only after Tuesday's ship

1. Pairwise interaction checks on red lines.
2. Pytest plugin: `assert_score("cases.jsonl", min=0.85)` so evals gate CI.
3. OpenAI provider.
4. promptfoo YAML import.
