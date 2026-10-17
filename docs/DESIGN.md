# promptgauge design system (v1)

v0 was written 17 Oct 2026 before any UI existed. This v1 was written the same day at block B14, after the backend (B02–B13) landed, against the real API shapes in `src/promptgauge/api/models.py`. It is the law for `dashboard/`. Change the rule here first, then the code. The UI polish pass (`docs/UI_POLISH.md`, P1 on 17 Oct 2026) moved the palette to neutral zinc with an indigo accent and gave the chrome Braintrust's shape; the rows below marked P1 are that pass.

The bar is Linear and Braintrust's experiment tables: light, dense, quiet, one accent, tables that read at a glance, monospace where text is code. The painted prompt is the one loud thing on the screen and everything else gets out of its way.

## 0. Decisions made at v1

| Question left open in v0 | Decision | Why |
|---|---|---|
| Logo and wordmark | Three 6 px discs (red, grey, green strong colours) in a row, then the word `promptgauge` in mono 13 / 500 `ink`. No image file. | The product is three colours and a word; drawing it in CSS keeps the wheel free of assets. |
| Sidebar collapse | Does not collapse. Fixed 220 px (200 px before P1). Below 720 px the page scrolls horizontally. | Local tool on a laptop; one less state. |
| Hover-card layout | See §7 `HoverCard`: verdict word first, then baseline → without, delta, interval, n cases, tokens, level. | Follows the order a reader asks: what is it, how much, how sure. |
| Cut prompt: diff or two columns | Two columns. Left: the original with removed segments painted red-soft and struck through. Right: the cut prompt as plain mono. | Deletion only (invariant 2) means the right column is the left column minus the painted runs; a diff view would say the same thing with more noise. |
| Empty-state illustrations | None. A 20 px Phosphor icon on a `surface-2` disc. | Illustrations age; the icon set is already bundled. |
| Language | JavaScript (`.jsx`), no TypeScript. | PLAN §8 file tree; the API models are the contract and are typed on the Python side. |
| Stack pins | Vite 6 (Node 20.9 in the dev shell), React 19, Tailwind 4 via `@tailwindcss/vite`, `react-router` 7, `@phosphor-icons/react`, `@fontsource-variable/inter` and `@fontsource-variable/jetbrains-mono`. Radix (`radix-ui`) is added at B16 when the hover card, slider and tooltip arrive. | Each added at the block that needs it (YAGNI). |

## 1. Colour tokens

Defined once in `dashboard/src/styles.css` under Tailwind's `@theme` as `--color-*` so every token is a utility (`bg-canvas`, `text-secondary`, `border-line`). Light only. No dark theme, no `prefers-color-scheme` handling.

### Canvas, panels, ink

Neutral zinc (P1). The warm `#f5f4f0` of v1.0 read as paper; the references read as a tool. One accent, indigo, and it appears only on the primary button, links, the focus ring, the slider thumb and the selected table row. Never on the navigation.

| Token | Value | Use |
|---|---|---|
| `canvas` | `#fafafa` | Page background, sidebar |
| `panel` | `#ffffff` | Main column, side panels, cards, secondary buttons |
| `surface-2` | `#f4f4f5` | Hover rows, input backgrounds, quiet chips, empty-state disc, the spend card |
| `surface-3` | `#e4e4e7` | Pressed rows, the active sidebar item, progress-bar tracks |
| `line` | `#e4e4e7` | Hairlines between table rows, under headers, panel edges |
| `line-strong` | `#d4d4d8` | Input and secondary-button borders, slider track |
| `ink` | `#18181b` | Body text, titles, numbers |
| `secondary` | `#71717a` | Metadata, hints, inactive sidebar items, table headers, breadcrumb parents |
| `tertiary` | `#a1a1aa` | Timestamps, placeholders |
| `accent` | `#4f46e5` | Primary button, links, focus ring, slider thumb, selected-row bar |
| `accent-soft` | `rgba(79,70,229,0.10)` | Selected table row background |
| `accent-fg` | `#ffffff` | Text on `accent` |

### Verdict colours (the product)

Each verdict has a strong colour for swatches, the legend and the hover card, and a soft colour for painting prompt text. Text on a soft colour is always `ink`, never the strong colour, so a long red block stays readable.

| Verdict (`VerdictOut.verdict`) | Strong | Soft | Word shown |
|---|---|---|---|
| `red` | `#c0392b` | `#fbe4e1` | load-bearing: removing it hurts |
| `grey` | `#7a7a80` | `#ececee` | no measurable effect at this sample size |
| `green` | `#2e7d4f` | `#dff2e6` | removing it helped |
| unmeasured (`verdict: null`) | `#a0a0a6` | transparent | not measured (a line inside a non-red block, or the run stopped first) |

The grey wording is invariant 4 and comes from the API (`AblationOut.legend`); the UI shows that string, it does not keep its own copy. Verdict colours appear only on prompt segments, the legend, the hover card and the verdict count tiles. Never on buttons, never on panel backgrounds, never as a banner.

### Status

| Token | Value | Soft | Use |
|---|---|---|---|
| `danger` | `#c0392b` | `#fbe4e1` | Failed result cells (`score: null`), `stopped` banner text, "cut prompt not confirmed" |
| `ok` | `#2e7d4f` | `#dff2e6` | `confirmed`, API key present, status `done` |
| `warn` | `#9a6400` | `#fff3d6` | Status `partial` and `stopped`, estimate near budget |

## 2. Type

```
--font-sans: "Inter Variable", -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
--font-mono: "JetBrains Mono Variable", "SF Mono", Menlo, Consolas, monospace;
```

Both variable fonts are imported from `@fontsource-variable/*` in `styles.css` and bundled by Vite, so the dashboard loads nothing from the network.

| Step | Size / line | Weight | Use |
|---|---|---|---|
| `xs` | 11 / 14 | 500 | Tags, legend labels, tooltips |
| `sm` | 12 / 16 | 400 (500 in table headers) | Metadata, timestamps, hover-card rows, table headers, toolbar chips |
| `base` | 13 / 18 | 400 | Tables, menus, buttons, inputs |
| `mono` | 13 / 20 | 400 | The painted prompt, case inputs and outputs, the cut prompt, judge reasons |
| `mono-sm` | 12 / 18 | 400 | Numbered YAML (the run config), line numbers in `tertiary`, keys in `secondary` (P3) |
| `md` | 15 / 22 | 400 | Side-panel body text |
| `lg` | 17 / 24 | 600 (500 for section titles) | Side-panel and dialog titles; Settings section titles |
| `xl` | 20 / 26 | 600 | Page titles ("Ablation · system.md") |

Weight 400 for text, 500 for anything that must stand out, 600 only on page, side-panel and dialog titles (P1: at 500 they disappeared next to the tables). Numbers use `font-variant-numeric: tabular-nums` everywhere (set on `body`).

### Number formats (one helper, `dashboard/src/ui/format.js`)

| Value | Format | Example |
|---|---|---|
| score, mean, ci bound | two decimals | `0.87` |
| delta | sign always, two decimals, true minus sign | `−0.12`, `+0.04` |
| interval | brackets, comma, space | `[−0.18, −0.06]` |
| USD | `$` and two decimals | `$1.62` |
| INR | `₹` and no decimals | `₹136` |
| tokens, cases, calls | thousands separators | `1,284` |
| share (cached) | whole percent, thin space before the sign | `61 %` |
| duration | seconds under 60, else `m s` | `42 s`, `3 m 05 s` |
| `created_at` | local date and time, no seconds | `17 Oct 2026, 14:02` |
| null | an en dash in `tertiary`, plus the word where the null has one (`failed`, `not measured`, `not run`) | `–` |

## 3. Spacing, shape, elevation

- **Spacing** on a 4 px grid: 4, 8, 12, 16, 20, 24, 32, 48. Table rows 36 px on run lists and 40 px on per-case tables (P2: a case row carries input, output and expected, and needs the air); cells 12 px side padding; header row 32 px; panels 20 px; page gutter 16 px.
- **Radii:** 6 (inputs, chips, small buttons), 10 (buttons, cards, sidebar items), 12 (panels, dialogs).
- **Shadows:** `shadow-pop` `0 2px 6px rgba(20,24,40,.08), 0 12px 32px rgba(20,24,40,.12)` for hover cards, menus and dialogs. Panels sit flat on the canvas with a `line` hairline; nothing else casts a shadow.
- **Painted segments:** the soft verdict colour as background on the text run, `border-radius: 3px`, `padding: 1px 2px`, `box-decoration-break: clone` so wrapped lines keep their rounded ends. A 2 px gap between adjacent segments so block boundaries stay visible. Stage-two lines paint over their block: a line span sits inside its block span and its own colour wins.

## 4. Motion

`--ease: cubic-bezier(.2,.7,.3,1)`. Hover and press 120 ms; hover cards and menus 150 ms fade with a 4 px slide; the `delta` slider repaints segments with a 150 ms background transition so the eye can follow which segments flip. `prefers-reduced-motion: reduce` removes every transition.

## 5. States

| State | Treatment |
|---|---|
| Hover row | background `surface-2` |
| Selected table row | background `accent-soft`, 2 px `accent` bar on the left |
| Active sidebar item | background `surface-3`, `ink` text, no bar (P1: accent on the nav stole from the painted prompt) |
| Focus (keyboard) | 2 px `accent` ring, 2 px offset; never removed |
| Disabled | opacity 0.45, `cursor: not-allowed` |
| Loading | a 16 px spinner beside the page title; never a full-screen spinner; tables keep their last rows |
| Empty | `EmptyState`: 20 px icon on a `surface-2` disc, a 15 px title, one line of `secondary` text that names the CLI command to run |
| Error (request failed) | one line of `danger` text under the title row with the API's `detail`; never a toast. A 403 says "refused: open the dashboard at 127.0.0.1:7331". |
| Stopped run | one line at the top of the Ablation screen on `warn` soft, e.g. "Stopped: budget. 14 of 22 segments measured; the cut prompt was not confirmed." |

## 6. Layout

```
┌────────┬───────────────────────────────────────────────┬──────────────┐
│ side   │ title row: page title · actions                │ right panel  │
│ bar    │ ──────────────────────────────────────────────│ (ablation:   │
│ 220px  │ content                                        │ hover card / │
│        │                                                │ cut prompt)  │
└────────┴───────────────────────────────────────────────┴──────────────┘
```

- **Sidebar** 220 px, `canvas` background, hairline on the right: wordmark at the top (§0); a section label `Project` (`xs`, 500, `secondary`, uppercase tracking); four `NavLink` rows of 32 px with a 16 px Phosphor icon (regular weight) and a label: Datasets, Experiments, Ablations, Settings. The active row is a `surface-3` pill with `ink` text; inactive rows are `secondary`. At the bottom, the **spend card** (`SpendCard`, §7): a `surface-2` card with the project directory name, then `Spend` and the total cost in USD, then `3 runs · 61 % cached` and one 4 px progress bar whose fill is the cached share (`secondary` on `surface-3`; the words beside it carry the meaning). Its numbers come from `GET /api/summary` and refresh on every route change; the database path is the card's tooltip, from `GET /api/health`.
- **Main column:** one `panel` with a 16 px canvas gutter on every side, radius 12, hairline. Title row 52 px, then the screen content. Minimum width 720 px.
- **Title row** (`TitleRow`): the screen's type icon (Phosphor, 18 px, `secondary`) first; then, on a detail page, a breadcrumb whose parent is a link in `secondary` (`Experiments › eval v1`, the `›` in `tertiary`) and whose last part is the `xl` title; on a list page just the title. A spinner while loading, an error line underneath; then the **toolbar chips** (`Chip`, §7): the totals of what the screen shows, `10 cases · 60 calls · $0.12 · 42 s`, quiet `surface-2` chips with a 12 px icon each; actions on the right with at most one filled primary. There is no back arrow: the crumb is the way back. The `…` run menu arrives at P4.
- **Right panel:** 360 px, only on the Ablation screen (the pinned segment card), the Datasets screen (case detail) and the Experiment screen (one result). Hidden under 1100 px; its content then opens in a `Dialog`. The cut-prompt panel is two columns and needs the width, so it sits in the main column under the painted prompt, not in the right panel (changed at B16).
- **Routes** (`react-router`, browser history, served by FastAPI's `html=True` fallback): `/datasets`, `/experiments`, `/experiments/:id`, `/ablations`, `/ablations/:id`, `/settings`. `/` redirects to `/experiments`. The sidebar item "Ablations" lists ablation runs (`GET /api/experiments?kind=ablation`) and each row opens `/ablations/:id`.

## 7. Components (`dashboard/src/ui/`, one file per component, named after it)

Radix primitives (`radix-ui`, from B16) styled with Tailwind; Phosphor icons, regular weight, 16 px.

| Component | Built on | Block | Notes |
|---|---|---|---|
| `Sidebar` | own | B14, P1 | §6: section label, `surface-3` active pill, `SpendCard` at the bottom |
| `SpendCard` | own | P1 | §6: project name, `Spend` + USD, `runs · % cached`, 4 px cached-share bar; tooltip is the database path; `secondary` error line when the summary request fails |
| `TitleRow` | own | B14, P1 | `Icon` (the screen's type icon), optional `crumb={{ label, to }}` rendered as a link before the title, title at `xl` 600, optional spinner, optional `danger` error line, `chips` slot after the title, actions slot on the right |
| `Chip` | own | P2 | 24 px, `surface-2`, radius 6, `sm` text in `ink` with a 12 px `secondary` icon before it; one fact per chip (`10 cases`, `60 calls`, `$0.12`, `42 s`, `151 → 21 tokens`); never coloured |
| `EmptyState` | own | B14 | §5 |
| `Panel` | own | B15 | the main column (§6); every screen renders one, plus an optional `SidePanel` beside it |
| `Dash` | own | B15 | the null value of §2: an en dash in `tertiary` plus the word |
| `SearchInput` | own | B15 | 32 px, leading icon, filters client-side |
| `Table` | own | B15, P2 | `sm` 500 headers in `secondary`, each with a 12 px **type glyph** from the column (`icon`): `#` Hash for indexes, `↘` ArrowDownRight input, `↗` ArrowUpRight output, `=` Equals expected, `⌂` Tag tags, `%` Percent scorers and scores, `$` CurrencyDollar cost, `◷` Clock date, Timer duration, Lightning calls, Cpu model, TextAa name, Stack kind, Pulse status, Rows cases, Repeat repeat, GitBranch variant, TextAlignLeft context, Triangle delta. `rowHeight` 36 (lists) or 40 (per-case). `numbered` adds a leading muted row-number column (1-based after sorting, `tertiary`, 40 px); a column with `muted: true` renders in `tertiary` (the case index). Hairlines, numbers right-aligned in tabular figures, sortable by header click, row click selects. A leading checkbox column exists only on the runs table (the compare picker) |
| `ColumnPicker` | Radix Popover | P2 | a `btn-secondary` reading `Columns (7)` (visible count) that opens a popover of checkboxes, one per hideable column (`fixed: true` columns are not listed), with `Reset`; state from `ui/useColumns.js`, which keeps the hidden keys in `localStorage` under `promptgauge.columns.<screen>` (`runs`, `results`, `datasets`); a hidden column is also dropped from the table's sort |
| `Tag` | own | B15 | 11 px, 500, `surface-2` background with `ink` text; case tags and experiment `kind` |
| `StatusTag` | `Tag` | B15, P1 | icon + word on the soft tint: `✓ done` ok, `△ partial` warn, `■ stopped: reason` warn, `◌ running` secondary (Phosphor Check, Warning, Square, CircleDashed at 11 px) |
| `SidePanel` | own | B15, P3 | the 360 px right column; title, subtitle, close, scrolling body of `Section`s |
| `Section` | own | P3 | collapsible: a 28 px header row with a 12 px icon, the name in `sm` 500 `secondary`, an optional `actions` slot on the right and a chevron; `open` by default unless `defaultOpen={false}`; the body is whatever the screen puts in it. Sections in a side panel: `Input`, `Output` (with the `Pretty / Raw` toggle: pretty wraps, raw is a `pre` that scrolls sideways), `Expected`, `Context`, `Tags`, `Scores` (one row per scorer: key, score or `failed`, the judge reason verbatim underneath). On the Experiment screen a closed `config` section sits under the metric grid |
| `Metric` | own | B16 as `StatTile`, P3 | one label-above-value cell: `sm` 500 `secondary` label, `md` value, optional `sm` `secondary` hint; no background (the old tiles looked like buttons) |
| `MetricGrid` | own | P3 | `groups=[[metric, …], …]`: a flex row of groups, 24 px apart, a `line` hairline between groups, under the title row with a hairline below. The run header (status · kind / model · judge / score · one per scorer / repeats · date) and the Ablation totals (segments measured · red · grey · green at delta / tokens before → after / baseline · cut with confirmed) |
| `VerdictLegend` | own | B16 | four swatches with the word beside each, always visible on the Ablation screen |
| `PaintedPrompt` | own | B16 | the prompt as `pre`; blocks in document order, each block's lines inside it; text outside any segment stays plain |
| `SegmentSpan` | own | B16 | one painted run; `data-verdict`; hover opens the card (Radix HoverCard); click pins it in the right panel, a click on the prompt background unpins |
| `SegmentCard` | own | B16 | the card's content, shared by the hover card and the pinned right panel |
| `HoverCard` | Radix HoverCard | B16 | rows in this order: verdict swatch + word · `baseline → without` (`baseline_score`, `baseline_score + mean_delta`) · delta with sign · `95% interval [lo, hi]` · `n cases` · `tokens` · `block 3` / `line 2 of block 3` |
| `Slider` | Radix Slider | B16 | the `delta` control, 0.00 to 0.20 step 0.01, value shown beside it, starts at the run's `delta` |
| `CutPromptPanel` | own | B16 | two columns (§0): the left marks removed runs found by `ui/deletions.js` (an LCS over word and whitespace tokens; deletion only makes the cut a subsequence of the original), `tokens_before → tokens_after` (−n, −%), `cut_score [lo, hi]` beside `baseline_score`, `confirmed` / `cut prompt not confirmed` word with the CLI's wording, `calls_per_month` input (saved through `PUT /api/settings` on blur or Enter), USD and INR saved, primary "Copy cut prompt" button |
| `Tooltip` | Radix Tooltip | B17 | 300 ms delay, `panel`, 11 px; `Tag tip=`, `Swatch word=`, `StatusTag`, failed cells, compare deltas and the confirmation tags all carry their word through it; the stopped banner and tinted rows use `title` |
| `Dialog` | Radix Dialog | B17 | 480 px, radius 12; `SidePanel` renders as one under 1100 px (`ui/useMediaQuery.js`). The compare picker stayed two checkboxes and a button (B15), so no dialog there |
| `CodeBlock` | own | B15, P3 | mono text, `surface-2`, copy button top-right. `wrap={false}` makes it a sideways-scrolling `pre` (the Raw view). `numbered` adds a `tertiary` line-number gutter and drops to `mono-sm`; `yaml` paints each `key:` in `secondary`. The run config is rendered by `ui/yaml.js` (`configToYaml`), which writes it the way the user did in `promptgauge.yaml` (`- contains`, `- rubric: helpful`), never as the API's `{name, arg}` objects |

Rules for every component:

- Every colour is paired with a word. The legend names each verdict; the hover card says the word; failed cells say "failed"; status tags say the status.
- No AI-generated prose anywhere in the UI. Judge reasons are shown verbatim in `mono` and labelled "judge reason".
- Buttons are two component classes in `styles.css`: `btn btn-primary` (filled `accent`, `accent-fg` text) and `btn btn-secondary` (`panel` background, `line-strong` hairline, `ink` text, an icon before the label). Both 32 px, radius 6, `base` type, 10 px side padding, 120 ms hover. One primary per view: "Compare" on the runs table, "Copy cut prompt" on the Ablation screen, "Save" on Settings; everything else that acts is a secondary ("show variants" is one, with an eye icon). Icon-only controls (close, copy, sort) stay bare.
- Inputs 32 px tall, `line-strong` border, radius 6, `accent` ring on focus.
- Tables never wrap; long inputs and outputs are truncated with an ellipsis and open in the side panel.
- The dashboard never calls a model and never writes anything but `PUT /api/settings` (invariant 6).

## 8. Data → screen (the API is the contract)

All requests go through `dashboard/src/api/ApiClient.js`, one method per route, which throws `ApiError(status, detail)` on anything but 2xx. Screens hold request state as `{ data, error, loading }` through `ui/useRequest.js`; `ui/format.js` holds the §2 formats.

| Screen | Route | Fields used |
|---|---|---|
| Sidebar | `GET /api/health`, `GET /api/summary` | `database` (tooltip, project name = its grandparent directory); `runs`, `calls`, `cached`, `cost_usd` (the spend card; cached share = `cached / calls`, 0 when there are no calls). |
| Datasets | `GET /api/datasets`, `GET /api/datasets/{hash}/cases` | `dataset_hash` (first 8 chars shown, full on hover), `case_count`, `first_seen`; `index`, `input`, `expected`, `context`, `tags`. Search filters `input`, `expected`, `context` and tags client-side. |
| Experiments | `GET /api/experiments` | `name`, `kind`, `model`, `scorer_means` (one column per key), `score`, `cases`, `totals.calls`, `totals.cached`, `totals.cost_usd`, `created_at`, `finished_at` (duration = finished − created), `status`, `stopped_reason`. |
| Experiment | `GET /api/experiments/{id}`, `GET /api/experiments/{id}/results` | header from the detail; the per-case table groups result rows by `case_index` then `repeat_index`: `input` (from `case_scores`), `output`, `expected` (from the dataset), one cell per `scorer` with `score` and `reason`; `score: null` cells are `danger` soft with the word "failed". Rows with `variant_id` not null are hidden behind a "show variants" toggle (ablation runs only). |
| Compare (`/experiments?a=&b=`, reached by ticking two rows) | `GET /api/experiments/compare?a=&b=` | `a`, `b` summaries; `scorers[key].{a,b,delta}`; `cases[].{index,input,a,b,delta}`; deltas signed. |
| Ablations (`/ablations`) | `GET /api/experiments?kind=ablation` | name, model, baseline `score`, cases, calls, cost, date, status; row click opens the run. |
| Ablation (`/ablations/:id`) | `GET /api/ablations/{id}`, `GET /api/settings` | `prompt_text` painted by `segments[].{start_offset,end_offset,level,parent_segment_id,verdict}`; `delta` seeds the slider; `legend` is the words; `input_usd_per_million` (null when the model left the price table: the panel then says so instead of a figure); `ablation.*` fills the cut panel; `totals`; `experiment.status` / `stopped_reason` drive the banner; `calls_per_month` and `inr_rate` from settings. The stat tiles and the legend counts follow the slider. The CLI's "Most segments are grey" hint appears when more than 80% of measured segments are grey. |
| Settings | `GET /api/settings`, `GET /api/experiments` + `GET /api/experiments/{id}` (the newest), `PUT /api/settings` | Run config from the last run's `config` (F8.4), else the `config` echo of the loaded promptgauge.yaml, else an empty state; shown as numbered YAML (`CodeBlock numbered yaml`) in the key order of `Config`: prompt, dataset, model, judge, scorers, repeats, temperature, budget_usd, delta, concurrency, inr_rate. `api_key_present` as a tag (present ok / missing danger, never the key). `calls_per_month` and `inr_rate` inputs with one primary Save, disabled until valid and changed. |

### The verdict rule, repeated client-side

The `delta` slider repaints without a request (F8.3). It applies the same rule as `stats/verdict_rule.py` to each segment's stored `ci_low` and `ci_high`:

```
red   if ci_high < -delta
green if ci_low  >  delta
grey  otherwise            (boundaries are grey)
```

This is the one place UI logic duplicates Python logic; the two must stay identical, and `tests/stats/test_verdict_rule.py`'s table is mirrored in `dashboard/src/ui/verdictRule.test.js` when the dashboard gains tests. Segments with `verdict: null` never change colour.

### Money saved (cut panel)

`tokens_saved = tokens_before − tokens_after`; `usd = tokens_saved × calls_per_month × input_price_per_token(model)`; `inr = usd × inr_rate`. `input_price_per_token = input_usd_per_million / 1e6`, from the API (read from `Pricing`, never typed into the UI). Same formula as `TerminalPainter`.
