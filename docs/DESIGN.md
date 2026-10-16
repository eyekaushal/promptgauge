# promptgauge design system (v0)

Written 17 Oct 2026, before any UI exists. This is the starting point. It is rewritten to v1 at block B14, before the first component, once the backend is done and the real data shape is known. Until then, change the rules here first, then the code.

The bar is Linear and Braintrust's experiment tables: light, dense, quiet, one accent, tables that read at a glance, monospace where text is code. The painted prompt is the one loud thing on the screen and everything else gets out of its way.

## 1. Colour tokens

Defined once in `dashboard/src/styles.css` as CSS variables and exposed to Tailwind through `@theme`. Light only. No dark theme, no `prefers-color-scheme` handling in v1.

### Canvas, panels, ink

| Token | Value | Use |
|---|---|---|
| `canvas` | `#f5f4f0` | Page background |
| `panel` | `#ffffff` | Main column, side panels, cards |
| `surface-2` | `rgba(28,28,30,0.04)` | Hover rows, input backgrounds, quiet chips |
| `surface-3` | `rgba(28,28,30,0.07)` | Pressed rows, selected tab underline |
| `line` | `rgba(28,28,30,0.08)` | Hairlines between table rows, under headers |
| `line-strong` | `rgba(28,28,30,0.16)` | Input borders, slider track |
| `ink` | `#1c1c1e` | Body text, titles, numbers |
| `secondary` | `#6b6b70` | Metadata, hints, inactive tabs, table headers |
| `tertiary` | `#a0a0a6` | Timestamps, placeholders |
| `accent` | `#2f5d8a` | Selected sidebar item, primary button, links, focus ring, slider thumb |
| `accent-soft` | `rgba(47,93,138,0.10)` | Selected row and sidebar background |
| `accent-fg` | `#ffffff` | Text on `accent` |

### Verdict colours (the product)

Each verdict has a strong colour for the legend and the hover card, and a soft colour for painting the prompt text background. Text on a soft colour is always `ink`, never the strong colour, so a long red block stays readable.

| Verdict | Strong | Soft | Word shown |
|---|---|---|---|
| `red` | `#c0392b` | `#fbe4e1` | load-bearing |
| `grey` | `#7a7a80` | `#ececee` | no measurable effect at this sample size |
| `green` | `#2e7d4f` | `#dff2e6` | removing it helped |
| `unmeasured` | `#a0a0a6` | transparent | not run (line inside a non-red block) |

Verdict colours appear only on prompt segments, the legend, the hover card and the small verdict count tiles. Never on buttons, never on backgrounds of panels, never as a banner.

### Status

| Token | Value | Soft | Use |
|---|---|---|---|
| `danger` | `#c0392b` | `#fbe4e1` | Failed case cells, `stopped: budget` banner text, `cut prompt not confirmed` |
| `ok` | `#2e7d4f` | `#dff2e6` | `confirmed`, API key present, cached 100% |
| `warn` | `#9a6400` | `#fff3d6` | `partial` status, estimate near budget |

## 2. Type

```
font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Inter Variable", Inter, sans-serif;
font-family-mono: "JetBrains Mono Variable", "SF Mono", Menlo, Consolas, monospace;
```

Inter Variable and JetBrains Mono Variable are bundled from `@fontsource-variable/*` and served by the local server.

| Step | Size / line | Weight | Use |
|---|---|---|---|
| `xs` | 11 / 14 | 500 | Tags, legend labels, tooltips, table headers |
| `sm` | 12 / 16 | 400 | Metadata, timestamps, hover-card rows |
| `base` | 13 / 18 | 400 | Tables, menus, buttons, inputs |
| `mono` | 13 / 20 | 400 | The painted prompt, case inputs and outputs, the cut prompt |
| `md` | 15 / 22 | 400 | Side-panel body text |
| `lg` | 17 / 24 | 500 | Section titles, dialog titles |
| `xl` | 20 / 26 | 500 | Page titles ("Ablation · system.md") |

Weight 400 for text, 500 for anything that must stand out, 600 nowhere. Numbers use `font-variant-numeric: tabular-nums` everywhere. Scores show two decimals (`0.87`), deltas show a sign (`−0.12`), intervals as `[−0.18, −0.06]`, money as `$1.62` and `₹136`.

## 3. Spacing, shape, elevation

- **Spacing** on a 4 px grid: 4, 8, 12, 16, 20, 24, 32, 48. Table rows 36 px; cells 12 px side padding; panels 20 px; page gutter 16 px.
- **Radii:** 6 (inputs, chips, small buttons), 10 (buttons, cards, sidebar items), 12 (panels, dialogs).
- **Shadows:** `shadow-pop` `0 2px 6px rgba(20,24,40,.08), 0 12px 32px rgba(20,24,40,.12)` for hover cards, menus and dialogs. Panels sit flat on the canvas with a hairline; nothing else casts a shadow.
- **Painted segments:** the soft verdict colour as background on the text run, `border-radius: 3px`, `padding: 1px 2px`, `box-decoration-break: clone` so wrapped lines keep their rounded ends. A 2 px gap between adjacent segments so block boundaries are visible.

## 4. Motion

`--ease: cubic-bezier(.2,.7,.3,1)`. Hover and press 120 ms; hover cards and menus 150 ms fade with a 4 px slide; the `delta` slider repaints segments with a 150 ms background transition so the eye can follow which segments flip. `prefers-reduced-motion: reduce` removes every transition.

## 5. States

| State | Treatment |
|---|---|
| Hover row | background `surface-2` |
| Selected row / sidebar item | background `accent-soft`, 2 px `accent` bar on the left |
| Focus (keyboard) | 2 px `accent` ring, 2 px offset; never removed |
| Disabled | opacity 0.45, `cursor: not-allowed` |
| Loading | a 16 px spinner beside the title; never a full-screen spinner |
| Empty | `EmptyState`: 20 px icon on a `surface-2` disc, a 15 px title, one line of `secondary` text with the CLI command to run |
| Error | one line of `danger` text under the control; never a toast |
| Stopped run | a single line at the top of the Ablation screen in `warn` soft with the word, e.g. "Stopped at the budget ($2.00). 14 of 22 segments measured." |

## 6. Layout

```
┌────────┬───────────────────────────────────────────────┬──────────────┐
│ side   │ title row: page title · actions                │ right panel  │
│ bar    │ ──────────────────────────────────────────────│ (ablation:   │
│ 200px  │ content                                        │ hover card / │
│        │                                                │ cut prompt)  │
└────────┴───────────────────────────────────────────────┴──────────────┘
```

- **Sidebar** 200 px: wordmark at the top, four items with a 16 px icon and a label (Datasets, Experiments, Ablation, Settings), the project directory name and the database path at the bottom in `tertiary`.
- **Main column:** one `panel`, title row 52 px, then the screen. Minimum 720 px.
- **Right panel:** 360 px, only on the Ablation screen (sticky hover card, then the cut-prompt panel) and the Datasets screen (case detail). Hidden under 1100 px.

## 7. Components (`dashboard/src/ui/`, one file per component)

Radix primitives (`radix-ui`) styled with Tailwind; Phosphor icons (`@phosphor-icons/react`), regular weight, 16 px.

| Component | Built on | Notes |
|---|---|---|
| `Table` | own | 36 px rows, `xs` headers in `secondary`, hairlines, right-aligned numbers, sortable by click |
| `Tag` | own | 11 px, 500, soft background with `ink` text; used for tags on cases and `kind` on experiments |
| `VerdictLegend` | own | four swatches with the word beside each; always visible on the Ablation screen |
| `SegmentSpan` | own | one painted run of prompt text; `data-verdict`; hover opens the card; click pins it |
| `HoverCard` | Radix HoverCard | baseline score, score without, delta with sign, interval, `n_cases`, tokens, verdict word |
| `Slider` | Radix Slider | the `delta` control, 0.00 to 0.20 step 0.01, value shown beside it |
| `StatTile` | own | one number with a label, used for the totals row (segments, tokens removed, baseline, cut, cost) |
| `Tooltip` | Radix Tooltip | 300 ms delay, `panel`, 11 px |
| `Dialog` | Radix Dialog | 480 px, radius 12, used only for the copy confirmation and the compare picker |
| `CodeBlock` | own | mono text, soft `surface-2`, copy button top-right |
| `EmptyState` | own | see States |

Rules for every component:

- Every colour is paired with a word. The legend names each verdict; the hover card says the word; failed cells carry "failed".
- No AI-generated prose anywhere in the UI. Judge reasons are shown verbatim in `mono` and labelled "judge reason".
- One primary button per view (`accent`); the rest quiet. "Copy cut prompt" is the primary on the Ablation screen.
- Inputs 32 px tall, `line-strong` border, radius 6, `accent` ring on focus.
- Tables never wrap; long inputs and outputs are truncated with an ellipsis and open in the right panel.

## 8. What v1 will decide (at B14)

Logo and wordmark; whether the sidebar collapses to icons; the exact hover-card layout once real verdict data exists; whether the cut prompt is a diff view or two columns; the empty-state illustrations. Nothing above the component table changes without a reason written here first.
