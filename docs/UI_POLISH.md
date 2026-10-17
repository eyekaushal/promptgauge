# UI polish plan (from the reference screenshots)

Written 17 Oct 2026 after B17, from the fifteen screenshots in `docs/reference_screenshots/` (ten of Braintrust, five of promptfoo). This is a plan, not law: each item below that is accepted gets folded into `docs/DESIGN.md` at the block that builds it. Nothing here touches the invariants (every colour carries a word, no toasts, one accent, the painted prompt is the loudest thing on screen, the dashboard never calls a model).

## 1. What the screenshots show

### Braintrust (braintrust_001–010)

| Aspect | Observed |
|---|---|
| Palette | Neutral zinc, not warm. Sidebar ≈ `#f7f7f8`, main `#ffffff`, ink ≈ `#18181b`, secondary ≈ `#71717a`, hairlines ≈ `#e4e4e7`. One accent, a bright indigo ≈ `#4f46e5`, used only for the primary button (Run, Create, Import, Save), links and the focus ring. Status is mostly **words with icons** ("✓ Configured", "Not configured" in grey), not coloured pills. Green appears only on the toast check and the active-filter chip border. |
| Type | Inter-like sans. Body and cells 13–14 px / 400; table headers 12 px grey; page titles ≈ 20 px semibold; dialog titles ≈ 18 px semibold. Mono (12 px, grey) for identifiers under names (`OPENAI_API_KEY`), for `{{input}}` template tokens (purple), and for the YAML metadata block with line numbers. |
| Icons | Thin 16 px line icons (Phosphor/Lucide weight), one per sidebar item, one before every page title, small type glyphs in table headers (`↘ Input`, `= Expected`, `⌂ Tags`, `{} Metadata`, `% scorer`). |
| Chrome | Top bar: workspace switcher left, breadcrumb (`SupportChatbot_Demo › Playgrounds`), right-side icon cluster. Below it a page-title row: icon · name · `…` menu, actions on the right with one filled primary (`▷ Run`). Sidebar ≈ 230 px with a small grey section label ("Project"), items as 32 px rows with a **neutral grey pill** for the active item (no accent), "Recent projects" list, and a **usage card** pinned at the bottom with two mini progress bars. |
| Tables | Hairline rows ≈ 40 px, a muted row-number column, truncation with an ellipsis, `–` for empty, name cells with an icon, a leading checkbox column for selection. Cells in the playground grid carry a small label line (`↗ Output`) and a metadata strip of icon + value chips (`⏱ 16.3s · 1025 tok · 0.00`), and a skeleton bar while a scorer runs. |
| Detail views | Three panes (009): a **left metadata column** (Comparisons picker, Prompt, Dataset, "Scorers and distribution" with a tiny 0/50/100 histogram per scorer, Metadata as YAML with line numbers, Tags, Description); the table; a **right trace panel** with tabs (Trace, Timeline, Thread, Custom), a bold span title, a row of quiet action buttons, then collapsible sections (`Metrics`, `Scores`, `Input`, `Output`) each with a 12 px grey label **above** its value in a 3-column grid, and a `Pretty ⌄` format picker on text sections. |
| Dialogs and empty states | Dialog: 20 px title, X top-right, radius ≈ 12, soft shadow, backdrop dimmed, primary button beside the input. Empty state (002): centred grey icon, grey title, a two-line paragraph, one primary button, then "starter" cards (title + description, hairline, radius 8). Toast (004): white card, green check, one line, bottom-right. |
| Controls | Secondary buttons are white with a hairline and an icon + label (`+ Message`, `⚙ Tools`, `Mustache ⌄`); a `Diff` switch; an active-filter chip (`% BrandAlignment ×`) outlined in green; a run progress pill (`90% ▬▬ Stop`). |

### promptfoo (promptfoo_001–005)

| Aspect | Observed |
|---|---|
| Palette | Material UI. White, blue ≈ `#1976d2`, heavier borders, 14–15 px text. Pass/fail is **loud**: green outlined chip `3 PASS`, red outlined chip `1 FAIL 2 PASS (0.33)`, failure reasons in bold red. Column-header pass rates are chips tinted by the rate (green soft for 100 %, tan for 41 %). |
| Matrix | Rows are test cases, columns are prompts. Column header = `Model A` grey chip + rate chip + the prompt text + a stats line (`Requests: 12 · Asserts: 36/36 passed · Avg latency`). Each cell: verdict chip, output, a `1/2` pager over repeats, a row of actions (zoom, 👍, 👎, #, ✎), `Latency: 1 ms` footer. |
| Toolbar | Outlined selects with floating labels (Zoom, Display, Search), count chip `12 results`, latency chip `⏱ 130ms`, then a second row of text buttons (`Columns (10)`, `Table settings`, `Eval actions ⌄`, `Show charts`). |
| Menus and dialogs | **Display** filter: all / failures only / passes only / errors only / different outputs / highlights only. **Eval actions**: Edit name, Edit and re-run, Compare with another eval, View YAML, Download, Copy, Share, Delete. **Table settings**: two columns of checkboxes with ⓘ, sliders with the value on the right, `Reset to defaults` + `Done`. |
| Charts | Pass-rate bars per prompt, score-distribution histogram, and a **scatter of prompt 1 vs prompt 2 per case** with the diagonal. |

## 2. Decisions

The dashboard keeps its shape (sidebar, one panel, right panel) and its rules. What changes is the surface: neutral palette, Braintrust-style chrome and tables, and a few of promptfoo's working controls. Loud pass/fail chips, MUI floating labels, thumbs ratings and toasts are not taken.

| # | Change | Source | Why | Where |
|---|---|---|---|---|
| 1 | **Neutral palette.** `canvas #fafafa`, `panel #fff`, `line #e4e4e7`, `line-strong #d4d4d8`, `ink #18181b`, `secondary #71717a`, `tertiary #a1a1aa`, `surface-2 #f4f4f5`, `surface-3 #e4e4e7`. Accent → indigo `#4f46e5`, `accent-soft rgba(79,70,229,.10)`. Verdict and status colours unchanged (they stay distinct from indigo). | Braintrust | Our warm `#f5f4f0` reads as "paper"; the references read as "tool". Indigo lifts the one primary button without competing with red/green. | `styles.css`, DESIGN §1 |
| 2 | **Page title 20 px / 600**, dialog and side-panel titles 17 px / 600, everything else stays 400/500. One exception to "600 nowhere". | Braintrust | The references' titles are clearly semibold; our 500 titles disappear next to the tables. | `styles.css`, `TitleRow`, DESIGN §2 |
| 3 | **Sidebar**: 220 px; small grey section label `Project`; active item = neutral `surface-3` pill, no accent bar; icon + label rows 32 px; bottom **spend card** ("Spend  $4.12 · 3 runs · 61 % cached") with one thin progress bar of cached share, replacing the bare db path (path moves to a tooltip on the card). | Braintrust | Accent on the nav steals from the painted prompt; the usage card is the one piece of glanceable state a local tool has. | `Sidebar.jsx`; needs `GET /api/summary` (runs, cost, calls, cached) |
| 4 | **Top bar with breadcrumb** inside the panel title row: `Experiments › eval v1`, type icon before the title, a `…` menu on the right (see #11). Back arrow goes. | Braintrust | Orientation on detail pages; the back arrow is the only thing it replaces. | `TitleRow.jsx`, screens |
| 5 | **Table headers with type glyphs** (`# index`, `↘ input`, `= expected`, `⌂ tags`, `% scorer`, `$ cost`, `◷ date`), 12 px grey; a muted row-number column; rows 40 px on per-case tables, 36 px on run lists; a leading checkbox column only on the runs table. | Braintrust | Cheapest visible step toward the reference tables. | `Table.jsx` (`icon` on columns), screens |
| 6 | **Status as icon + word** (`✓ done`, `△ partial`, `■ stopped: budget`, `◌ running`) keeping the soft tint; failed cells stay a tinted `failed` tag. | Braintrust | Words already there; the icon makes the row scannable without colour. | `StatusTag.jsx` |
| 7 | **Metric grid**: run header and ablation stat tiles become a label-above-value grid (12 px grey label, 15 px value), hairlines between groups, no tile backgrounds. | Braintrust (Metrics section) | Our surface-2 tiles look like buttons; the grid is quieter and holds more. | `RunHeader` in `Experiments.jsx`, `StatTile.jsx` |
| 8 | **Side panel sections**: collapsible `Input`, `Output`, `Expected`, `Scores` with a 12 px header row (icon · name · chevron), judge reasons under each scorer, and a `Pretty / Raw` toggle on output (pretty = wrapped, raw = `pre`). | Braintrust (right trace panel) | Our panel is a stack of code blocks; sections give it rhythm. | `SidePanel.jsx`, new `Section.jsx` |
| 9 | **Config as YAML with line numbers** on Settings and in the run header's "config" section, mono 12 px, keys in secondary. | Braintrust (Metadata) | Matches how the user wrote it (`promptgauge.yaml`). | `CodeBlock.jsx` (`numbered`, `yaml` props), `Settings.jsx` |
| 10 | **Per-scorer mini histogram** (0 / 50 / 100, five bins) beside each scorer mean in the run header and the runs table tooltip. | Braintrust (Scorers and distribution) | Shows spread, which a mean hides; the data is already in `case_scores`. Built with the `dataviz` skill, inline SVG, verdict-neutral grey bars. | new `Histogram.jsx` |
| 11 | **`…` run menu**: Copy prompt, View config, Download results (CSV, client-side), Compare with… (goes to the runs table with `a=` preset), Open ablation (when kind is ablation). | promptfoo (Eval actions) | Four things people do with a run, in one place; all read-only. | `TitleRow` actions, Radix DropdownMenu |
| 12 | **Display filter** on the per-case table (`all · failed only · below 0.5`) and on compare (`all · different only`, threshold = run delta). | promptfoo (Display) | "Different only" is the single most useful control in their viewer. | `Experiments.jsx` |
| 13 | **Toolbar chips** in the title row: `10 cases · 60 calls · $0.12 · 42 s`, quiet surface-2 chips with 12 px icons. | promptfoo (results / latency chips) | Puts the totals where the eye lands first. | `TitleRow` children |
| 14 | **Column picker** (`Columns (7)`) on the runs table and per-case table: a Radix Popover of checkboxes; remembered per screen in `localStorage`. | promptfoo (Columns / Table settings) | Scorer columns multiply fast. | `Table.jsx`, new `ColumnPicker.jsx` |
| 15 | **Compare scatter**: per-case a vs b with the diagonal, points coloured by sign of the delta, hover shows the case input. Below the per-case table. | promptfoo (charts) | The one chart that says more than the table. `dataviz` skill, inline SVG. | `Compare` in `Experiments.jsx`, new `Scatter.jsx` |
| 16 | **Empty states** gain one explanatory sentence and the command as a `CodeBlock` with its copy button; the Experiments empty state also shows two "starter" cards (`eval` and `ablate`) with one line each. | Braintrust (002) | Ours are terse; the cards double as onboarding. | `EmptyState.jsx` |
| 17 | **Active-filter chips** on Datasets: clicking a tag adds `late ×` beside the search; filters compose. | Braintrust (filter chip) | Tags exist for exactly this. | `Datasets.jsx`, `Tag.jsx` (`onRemove`) |
| 18 | **Secondary buttons**: white, hairline, icon + label, 32 px; `Compare`, `Copy cut prompt` and `Save` stay the one filled primary per view. | Braintrust | Our quiet buttons are bare text today. | `styles.css` component class `btn`, screens |

Not taken, and why:

- promptfoo's red/green verdict chips and bold red reasons: too loud next to the painted prompt, and our colours must stay reserved for verdicts and status.
- MUI floating-label inputs, thumbs up/down, "Edit and re-run", "Share": either a different design language or they would write to the database or call a model.
- Braintrust's toast: DESIGN §5 says never; the inline `saved` / `Copied` word stays.
- Braintrust's trace tree: there are no spans in promptgauge.

## 3. Order of work

Grouped so each group is one block-sized commit with a DESIGN.md update and a visual pass.

| Group | Items | Size | Needs |
|---|---|---|---|
| P1 Tokens and chrome | 1, 2, 3, 4, 6, 18 | ~1 day | `GET /api/summary` (one query over `experiment` and `call`) |
| P2 Tables | 5, 13, 14 | ~0.75 day | — |
| P3 Detail panels | 7, 8, 9 | ~0.75 day | — |
| P4 Filters and menu | 11, 12, 17, 16 | ~0.75 day | Radix DropdownMenu, Popover |
| P5 Charts | 10, 15 | ~0.5 day | `dataviz` skill for the palette and marks |

P1–P3 are what make it "look like the references"; P4 is behaviour; P5 is optional. Each group starts by editing DESIGN.md (the law), then the code, then Kaushal's visual pass on the seeded project.

## 4. Decisions (Kaushal, 17 Oct 2026)

1. Neutral zinc palette: **yes** (#1).
2. Indigo accent `#4f46e5`: **yes** (#1).
3. Spend card with the new `GET /api/summary` route: **yes** (#3).
4. Charts (P5): **deferred until after the live runs in B18**; design them against real score spreads.
   - Revised 17 Oct 2026: Kaushal asked for P5 after P4, so it was built against the seeded fake data; recheck the histogram bins and scatter axes against the first live run (B18).

Work order: P1 → P2 → P3 → P4, each as one commit on `feature/api-and-dashboard`, DESIGN.md updated first, visual pass on the seeded scratch project after. P5 waits for B18.
