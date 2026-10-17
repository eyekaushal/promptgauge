import Dash from "./Dash.jsx";
import { count, delta as fmtDelta, interval, score } from "./format.js";
import { Swatch, UNMEASURED_WORD } from "./VerdictLegend.jsx";

/** The rows of DESIGN.md §7 HoverCard: word, baseline → without, delta, interval, n, tokens, level. */
export default function SegmentCard({ segment, colour, legend, baseline, blockIndexOf }) {
  const v = segment.verdict;
  const word = colour ? legend[colour] : UNMEASURED_WORD;
  const without = v != null && baseline != null ? baseline + v.mean_delta : null;
  const level =
    segment.level === "block"
      ? `block ${segment.index + 1}`
      : `line ${segment.index + 1} of block ${blockIndexOf(segment.parent_segment_id)}`;
  const rows = [
    ["baseline → without", v ? `${score(baseline) ?? "–"} → ${score(without) ?? "–"}` : null],
    ["delta", v ? fmtDelta(v.mean_delta) : null],
    ["95% interval", v ? interval(v.ci_low, v.ci_high) : null],
    ["n cases", v ? count(v.n_cases) : null],
    ["tokens", count(segment.tokens)],
    ["level", level],
  ];
  return (
    <div className="flex flex-col gap-2 text-sm">
      <div className="flex items-center gap-2">
        <Swatch verdict={colour} word={word} />
        <span className="font-medium">{colour ?? "unmeasured"}</span>
        <span className="text-secondary">{word}</span>
      </div>
      <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1">
        {rows.map(([label, value]) => (
          <div key={label} className="contents">
            <dt className="text-xs font-medium text-secondary">{label}</dt>
            <dd className="text-right">{value ?? <Dash />}</dd>
          </div>
        ))}
      </dl>
      <div className="max-h-24 overflow-hidden rounded-sm bg-surface-2 px-2 py-1 font-mono text-mono whitespace-pre-wrap text-secondary">
        {segment.text}
      </div>
    </div>
  );
}
