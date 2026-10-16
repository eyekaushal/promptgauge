# How users get and run promptgauge

Decided 17 Oct 2026. Plain-language record of how promptgauge reaches users, and why it costs **$0** to distribute.
Expected audience: developers with an Anthropic key, a system prompt and some test cases. If adoption ever needs a hosted version, read "If we ever grow" at the bottom.

## The short version

| Topic | Decision | Cost |
|---|---|---|
| Install | `pip install promptgauge` from PyPI; the wheel includes the built dashboard | $0 |
| Model access | Each user brings their own Anthropic API key in `ANTHROPIC_API_KEY` | user pays their own usage |
| Dashboard | Runs locally at `127.0.0.1:7331`, started by `promptgauge ui`; no Node needed to use it | $0 |
| Data | One SQLite file in the user's project directory; nothing leaves the machine except calls to Anthropic | $0 |
| Docs | README on GitHub; a GitHub Pages site later (v0.2) | $0 |
| Source | GitHub `eyekaushal/promptgauge`, MIT | $0 |

**v0.1 (now):** PyPI package, bring-your-own-key, local dashboard, README as the docs.
**v0.2:** docs site on GitHub Pages, pytest plugin, promptfoo import.

---

## 1. PyPI: how the package ships

### What the user runs
```bash
pip install promptgauge          # or: uv add promptgauge
export ANTHROPIC_API_KEY=sk-ant-…
promptgauge eval                 # reads ./promptgauge.yaml
promptgauge ablate
promptgauge ui                   # opens http://127.0.0.1:7331
```

### What is inside the wheel
The Python package plus `promptgauge/api/static/`, which is the dashboard built once by Kaushal with `npm run build` before `uv build`. Users never install Node. The static files are a few hundred kilobytes.

### Kaushal's one-time setup
1. PyPI account with 2FA on. Reserve the name by publishing `0.1.0`; the name was free on 16 Oct 2026.
2. An API token scoped to the project, stored in `~/.pypirc` or passed to `uv publish --token`. Never in the repo.
3. Optional later: GitHub Actions trusted publishing so a tag publishes automatically. Not needed for v0.1.

### Release steps (PLAN.md §3.4)
```bash
cd dashboard && npm ci && npm run build && cd ..
uv build                         # dist/promptgauge-0.1.0-py3-none-any.whl + .tar.gz
uv publish                       # prompts for the token
```
Then in a clean virtualenv elsewhere: `pip install promptgauge && promptgauge --help`.

### Versioning
Semantic versioning from `0.1.0`. Fixes bump the patch; anything in PRD §19 bumps the minor. The version lives in one place, `pyproject.toml`, and `promptgauge --version` reads it from package metadata.

---

## 2. Anthropic: users bring their own key

There is no promptgauge server, so there is nothing to bill users through and no key to share. Each user sets `ANTHROPIC_API_KEY`. If it is missing, every command exits with one line saying so and a link to the Console's API keys page.

Why not run calls through our key? That needs a server, users' prompts and test cases would leave their machines, and we would pay for everyone. Different product; not doing it.

### What it costs a user
The budget planner prints an estimate before the first call. For reference, from the examples:

| Run | Target | Judge | Cases × repeats | Rough cost |
|---|---|---|---|---|
| `support-bot` eval | Sonnet | Haiku | 10 × 3 | a few cents |
| `support-bot` ablate (4 blocks, ~12 lines) | Sonnet | Haiku | 10 × 3 | under $1 |
| `mailmoat-planner` ablate (~30 blocks) | Sonnet | Haiku | 40 × 3 | $5 to $10 |

Reruns with an unchanged prompt cost $0 because of the cache.

---

## 3. Dashboard: local only

`promptgauge ui` starts uvicorn on `127.0.0.1:7331` and opens the browser. It reads the SQLite file in the current directory. Nothing is exposed on the network; a foreign Host header is refused. There is no login because there is no one else.

---

## 4. Docs

v0.1: the README is the documentation. It has install, the config reference, the four scorers, how ablation works in six sentences, the painted mailmoat prompt, the numbers, limits, and the ProCut citation.

v0.2: a GitHub Pages site (free) with the same content split into pages, generated from `docs/site/` with a static generator. Not before the tool has users asking for it.

---

## If we ever grow

- A hosted version (team dashboards, shared datasets) would need auth, a server and a billing story. None of that is planned. The local tool stays free and open.
- PyPI, GitHub and GitHub Pages stay free at any size.
