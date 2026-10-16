# Competitors and adjacent projects: prompt ablation engine

Written 6 Oct 2026. Overlap with existing work is acceptable for this project; this file exists so we know exactly what each one does and where ours differs. Sources at the end.

## Summary table

| Project | Type | What it does | Closest overlap with us |
|---|---|---|---|
| ProCut (EMNLP 2025 Industry) | Research paper | Segment-level attribution of a prompt via leave-one-out, Shapley, and an LLM-driven estimator; removes 30–40% of tokens with comparable performance on production prompts | Highest. Same core idea. No public tool found. |
| Claude Code's manual ablation | Playbook | Team removed ~80% of system prompt for Opus 5 by hand, bringing lines back only on measurable failure | Same method, done by hand |
| LLMLingua / LLMLingua-2 (Microsoft) | Open source library | Token-level compression using a small model's perplexity; up to 20x on long contexts | Different unit (tokens, not instructions); different goal (compress any text) |
| DSPy GEPA / MIPROv2 | Open source optimizer | Rewrites prompts to maximise a metric; GEPA produces prompts ~9x shorter and +10–14% over MIPROv2 | Different: rewrite, not explain |
| Opik Agent Optimizer (Comet) | Open source platform | Six optimizers (GEPA, evolutionary, few-shot Bayesian, HRPO, meta-prompt, parameter) on logged datasets | Different: optimize, not attribute |
| promptfoo (OpenAI, MIT) | Open source eval runner | YAML matrix of prompts x providers x tests; assertions; CI gates | Our eval runner could import its config; no ablation |
| Braintrust / Langfuse / LangSmith | Platforms | Datasets, experiments, per-row diffs, prompt versioning, regression scores | Data sources for us; no automatic ablation |
| Anthropic prompt improver, OpenAI prompt optimizer | Vendor consoles | Rewrite a prompt using best practices; no measurement | Different: unmeasured rewrite |
| HiveMind DAG-Shapley (Dec 2025) | Research | Efficient Shapley attribution across agent DAGs, 80% fewer LLM calls | Algorithm we can borrow for interaction checks |
| Web "prompt compressors" / token reducers | Hobby tools | Rewrite prompt text shorter, show token count | Toy; no evals, no evidence |

## Detail by project

### ProCut: LLM Prompt Compression via Attribution Estimation

Published at EMNLP 2025 Industry Track by Zhentao Xu, Fengyi Li, Albert Chen and Xiaofeng Wang, from an industry team (the company name was not legible in the PDF extraction). It is the closest thing to our project that exists.

How it works: the prompt is split into segments, meaning contiguous sentences or paragraphs, not tokens. Each segment's contribution is estimated with one of three methods: leave-one-out (remove one segment, measure the drop), Shapley values (average contribution across all subsets, which is exponential and impractical at full scale), or an LLM-driven estimator that queries the target model with progressively trimmed prompts to approximate importance with far fewer runs. Low-attribution segments are cut.

Results: about 30 to 40 percent of prompt tokens removed while task performance stayed comparable, validated on real production prompts at the authors' company.

Limits: no code or tool released that we could find. It is a method paper, not a product. It does not describe a developer workflow, a report, an import path from existing eval tools, or a cost-capped planner. Nondeterminism is handled by sampling and aggregation, but the paper does not frame it as a user-facing confidence interval.

What we do differently: ship the method as a tool a developer runs from their repo, import their existing evals, show confidence intervals per line, check pairwise interactions, run two models side by side, and output a pull-request-ready report with money saved.

### Claude Code's ablation playbook (Boris Cherny)

Not a tool, a process. The Claude Code team removed about 80 percent of their system prompt for Opus 5. Protocol: freeze a baseline (model, prompt, tools, settings), build a representative eval set (easy tasks, hard tasks, known regressions, risky actions, ambiguous requests, one long job), define the score (accepted output, test pass rate, corrections, unsafe attempts, turns, tokens, cost), remove everything optional, then add lines back one by one only when a measurable failure justifies them.

Why it matters to us: it is the strongest public proof that the ablation approach works at the highest level, and it was done by hand. Our product is this playbook automated.

### LLMLingua and LLMLingua-2 (Microsoft Research)

Open source Python library. A small model (GPT-2 or LLaMA-7B class) scores each token's perplexity; low-information tokens are dropped. A budget controller allocates compression differently to instructions versus examples. LLMLingua-2 reformulates this as token classification trained via data distillation, which is faster and task-agnostic. Reported up to 20x compression with under 2 percent quality loss on long-context benchmarks.

Where it differs: the unit is the token, so the output is a mangled-looking prompt that still works, not a readable prompt with whole instructions removed. It is built for long retrieved contexts and few-shot demos, not for explaining a hand-written system prompt. It gives no verdict on which instruction matters. A 2026 paper, "Token Reduction Is Not Cost Reduction", also notes that compressed prompts can change output behaviour in benchmark-dependent ways. We could offer LLMLingua as an optional final pass on grey text, but it is not a substitute.

### DSPy optimizers: MIPROv2 and GEPA

MIPROv2 proposes candidate instructions and few-shot sets and runs a Bayesian search over combinations against a training set. GEPA (Genetic-Pareto, ICLR 2026 oral) has an LLM read failed trajectories, reflect in natural language on what went wrong, propose revised instructions, and keep the best on a Pareto frontier. Reported: GEPA beats MIPROv2 by 10 to 14 percent with prompts about 9x shorter, and beats RL-based GRPO by 6 percent on average with up to 35x fewer rollouts. Available as dspy.GEPA and as a standalone pip package.

Where it differs: optimizers rewrite. The output is a new prompt the developer did not write and may not understand. Our tool explains the prompt the developer already has. The two are complementary: ablate first to understand, optimize later if wanted. GEPA's trick of using an LLM to reflect on failures is worth borrowing for the "why does this line matter" explanation next to each red line.

### Opik Agent Optimizer (Comet)

Apache 2.0, fully self-hostable platform with tracing, datasets, experiments, prompt management and an optimizer SDK shipping six algorithms: EvolutionaryOptimizer, FewShotBayesianOptimizer, GepaOptimizer, HRPO (hierarchical root-cause analysis of failures), MetaPromptOptimizer, ParameterOptimizer. Works on datasets and traces already logged to Opik. Vendors describe it as the only open-source observability platform with built-in multi-algorithm prompt optimization.

Where it differs: same as DSPy, it optimizes rather than attributes, and it assumes you live inside Opik. We should import Opik datasets so Opik users can run us too.

### promptfoo

Open source CLI and library, MIT, owned by OpenAI since March 2026. One YAML file declares prompts, providers and tests; it runs the full matrix and renders a side-by-side view. Assertions include equals, contains, similarity, javascript, python, llm-rubric, g-eval, classifier, latency and cost. Runs as a CI gate. Prompts and tests live in the repo, so git is the version history.

Where it differs: it compares prompt versions you wrote. It will not generate the removed-line variants, plan the ablation, repeat runs for confidence, or paint a heatmap. It is the most likely eval setup our first users already have, so reading promptfooconfig.yaml directly is a requirement, not a feature.

### Braintrust, Langfuse, LangSmith

All three offer datasets, experiments that run a task function against a dataset with scorers, per-row diffs and regression views, prompt versioning with environments, and tracing. Langfuse is open source (MIT, about 29,000 stars, self-hostable on Postgres, ClickHouse, Redis). Braintrust is closed source, eval-first, with a free tier of 10,000 scores then $2.50 per 1,000. LangSmith is trace-first, 5,000 free traces then $2.50 per 1,000. Langfuse supports LLM-as-judge and CI regression tests via GitHub Actions.

Where they differ: they are the system of record for datasets and scores. None runs an automatic ablation. They are import sources and, later, places to push our results back to as an experiment.

### Anthropic Console prompt improver and OpenAI prompt optimizer

Anthropic's improver rewrites a prompt using Claude's preferred structure and reports around 30 percent accuracy gains on a classification test. OpenAI's optimizer is a chat interface that rewrites to best practices. OpenAI is shutting its dataset-backed Evals platform: read-only from 31 October 2026, off on 30 November 2026.

Where they differ: unmeasured rewrites. Neither tells you what your current prompt is doing. The OpenAI shutdown is a small opening: teams who used it for prompt experiments need somewhere to go.

### HiveMind DAG-Shapley

Research from December 2025 on contribution-guided prompt optimization in agent systems. Its DAG-Shapley algorithm cuts LLM calls for Shapley attribution by over 80 percent. Useful to us only as an algorithm for the pairwise and interaction step, where naive Shapley is too expensive.

### Hobby compressors

Browser tools that rewrite a prompt shorter and show token counts across providers. No evals, no evidence, no confidence. Not competitors in any serious sense, but they show the demand: people want the before-and-after token number.

## What the gap looks like

Every piece of our project exists somewhere: the method (ProCut, Claude Code's playbook), the eval runners (promptfoo, Braintrust, Langfuse), the judges, the attribution algorithms (Shapley, DAG-Shapley), and the proof that cutting works (80 percent at Claude Code, 30 to 40 percent at ProCut's company). What does not exist is one tool that a developer runs on their own prompt, with their own evals, that paints the prompt with statistically defended verdicts, explains why each red line matters, checks interactions, compares models, and hands back a shorter prompt with a rupee figure. That is the product.

## Requirement implications

- Import formats on day one: promptfoo YAML, Braintrust and Langfuse datasets, plain JSONL, and a raw prompt file with no evals (then bootstrap from traces).
- Ablation unit: segments (blocks, then lines), never tokens. Treat system prompt, tool descriptions and few-shot examples as separate units.
- Statistics: repeated runs, bootstrap confidence intervals, a stated threshold for "real". Make the noise visible in the report.
- Cost planner: estimate before running, hard budget cap, caching of identical calls, cheap judge option (Jev or Haiku).
- Interactions: pairwise on red lines, using a DAG-Shapley style budget rather than full Shapley.
- Explanations: for each red line, show the failing cases from the ablated run (GEPA-style reflection optional).
- Two-model mode for migrations.
- Output: heatmap over the original prompt, before-and-after table with intervals, proposed prompt, tokens and money per month, markdown export for pull requests.
- Optional later: push results back to Braintrust or Langfuse as an experiment; LLMLingua as a final pass on grey text.

## Sources

- https://aclanthology.org/2025.emnlp-industry.20.pdf (ProCut)
- https://www.arxiv.org/pdf/2508.02053v1 (ProCut arXiv)
- https://www.ai.joaoqueiros.com/blog/claude-code-cut-system-prompt-boris-cherny-ablation-playbook
- https://levelup.gitconnected.com/slash-your-llm-costs-by-80-a-deep-dive-into-microsofts-llmlingua-prompt-compression-d993c82009c4
- https://arxiv.org/pdf/2607.12161 (Token Reduction Is Not Cost Reduction)
- https://arxiv.org/pdf/2507.19457 (GEPA)
- https://futureagi.com/blog/dspy-optimizers-explained/
- https://www.morphllm.com/gepa-prompt-optimization
- https://pypi.org/project/opik-optimizer/
- https://github.com/comet-ml/opik
- https://qaskills.sh/blog/promptfoo-llm-testing-guide
- https://arize.com/blog/best-prompt-testing-optimization-tools/
- https://www.morphllm.com/comparisons/braintrust-vs-langsmith
- https://langfuse.com/compare/braintrust
- https://claude.com/blog/prompt-improver
- https://developers.openai.com/api/docs/guides/prompt-optimizer
- https://www.arxiv.org/pdf/2512.06432 (HiveMind DAG-Shapley)
- https://www.kunalganglani.com/tools/prompt-compressor
