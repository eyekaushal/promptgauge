import { delta as fmtDelta, score } from "./format.js";
import Tooltip from "./Tooltip.jsx";

const SIZE = 260;
const PAD = { left: 30, bottom: 26, top: 10, right: 12 };
const PLOT = SIZE - PAD.left - PAD.right;
const TICKS = [0, 0.5, 1];

const KINDS = {
  up: { fill: "var(--color-ok)", word: "higher under b" },
  down: { fill: "var(--color-danger)", word: "lower under b" },
  same: { fill: "var(--color-grey)", word: "within" },
};

function kindOf(delta, threshold) {
  if (delta > threshold) return "up";
  if (delta < -threshold) return "down";
  return "same";
}

/**
 * Per case, run a against run b (DESIGN.md §7): diverging on the sign of the delta beyond the
 * run's `delta`, with the shape (▲ ▼ ●) and the legend words carrying what the colour says.
 * points: [{ index, input, a, b, delta }]
 */
export default function Scatter({ points, threshold, nameA, nameB }) {
  const plotted = points.filter((p) => p.a != null && p.b != null);
  const skipped = points.length - plotted.length;
  const x = (v) => PAD.left + v * PLOT;
  const y = (v) => PAD.top + (1 - v) * PLOT;
  const counts = { up: 0, down: 0, same: 0 };
  for (const p of plotted) counts[kindOf(p.delta ?? p.b - p.a, threshold)] += 1;

  return (
    <figure className="flex flex-col gap-2">
      <svg
        width={SIZE}
        height={SIZE}
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        role="img"
        aria-label={`each case's score under ${nameA} against ${nameB}`}
        className="block overflow-visible"
      >
        {TICKS.map((t) => (
          <g key={t}>
            <line x1={x(t)} y1={y(0)} x2={x(t)} y2={y(1)} stroke="var(--color-line)" />
            <line x1={x(0)} y1={y(t)} x2={x(1)} y2={y(t)} stroke="var(--color-line)" />
            <text x={x(t)} y={y(0) + 14} textAnchor="middle" className="fill-tertiary text-[10px]">
              {t}
            </text>
            <text x={x(0) - 6} y={y(t) + 3} textAnchor="end" className="fill-tertiary text-[10px]">
              {t}
            </text>
          </g>
        ))}
        <line x1={x(0)} y1={y(0)} x2={x(1)} y2={y(1)} stroke="var(--color-line-strong)" />
        <text x={x(0.5)} y={SIZE - 2} textAnchor="middle" className="fill-secondary text-[10px]">
          {nameA}
        </text>
        <text
          x={8}
          y={y(0.5)}
          textAnchor="middle"
          transform={`rotate(-90 8 ${y(0.5)})`}
          className="fill-secondary text-[10px]"
        >
          {nameB}
        </text>
        {plotted.map((p) => {
          const d = p.delta ?? p.b - p.a;
          const kind = kindOf(d, threshold);
          const word = kind === "same" ? `within ±${threshold.toFixed(2)}` : KINDS[kind].word;
          const tip = `case ${p.index} · ${score(p.a)} → ${score(p.b)} · ${fmtDelta(d)} ${word}${
            p.input ? ` · ${p.input.length > 60 ? `${p.input.slice(0, 60)}…` : p.input}` : ""
          }`;
          return (
            <Tooltip key={p.index} text={tip}>
              <g className="group cursor-default" tabIndex={0} aria-label={tip}>
                <circle cx={x(p.a)} cy={y(p.b)} r={12} fill="transparent" />
                <Mark kind={kind} cx={x(p.a)} cy={y(p.b)} />
              </g>
            </Tooltip>
          );
        })}
      </svg>
      <figcaption className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-secondary">
        <Key kind="up" word={`higher under b · ${counts.up}`} />
        <Key kind="down" word={`lower under b · ${counts.down}`} />
        <Key kind="same" word={`within ±${threshold.toFixed(2)} · ${counts.same}`} />
        {skipped > 0 && <span>{skipped} without a score on both sides</span>}
      </figcaption>
    </figure>
  );
}

/** ▲ for up, ▼ for down, ● for the same; a 2 px panel ring keeps overlaps legible. */
function Mark({ kind, cx, cy }) {
  const ring = {
    stroke: "var(--color-panel)",
    strokeWidth: 2,
    paintOrder: "stroke",
    fill: KINDS[kind].fill,
    className: "transition-opacity duration-120 group-hover:opacity-70 group-focus-visible:opacity-70",
  };
  if (kind === "same") return <circle cx={cx} cy={cy} r={4} {...ring} />;
  const h = 5;
  const pts =
    kind === "up"
      ? `${cx},${cy - h} ${cx + h},${cy + h} ${cx - h},${cy + h}`
      : `${cx},${cy + h} ${cx + h},${cy - h} ${cx - h},${cy - h}`;
  return <polygon points={pts} {...ring} />;
}

function Key({ kind, word }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <svg width={12} height={12} viewBox="-6 -6 12 12" aria-hidden="true">
        <Mark kind={kind} cx={0} cy={0} />
      </svg>
      {word}
    </span>
  );
}
