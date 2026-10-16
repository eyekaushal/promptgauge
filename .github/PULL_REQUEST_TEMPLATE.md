## What

<!-- One or two sentences. Which PLAN.md blocks does this branch cover? -->

## How to verify

```bash
uv sync && uv run ruff check . && uv run pytest -q
```

<!-- Anything beyond the standard commands: a CLI run on examples/support-bot, a screenshot, a report file. -->

## Checklist

- [ ] Conventional Commit messages (`type(scope): summary`)
- [ ] Tests added or updated; none call the network
- [ ] `docs/PLAN.md` §11 tracker updated
- [ ] No API key, `.env` or `notes/` content in the diff
- [ ] Invariants in `CLAUDE.md` still hold
