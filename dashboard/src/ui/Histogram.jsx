import Tooltip from "./Tooltip.jsx";

const BINS = [
  [0, 0.2],
  [0.2, 0.4],
  [0.4, 0.6],
  [0.6, 0.8],
  [0.8, 1.0001],
];
const BAR = 8;
const GAP = 2;
const HEIGHT = 16;
const WIDTH = BINS.length * BAR + (BINS.length - 1) * GAP;

/** Five bins over 0–1 of a scorer's per-case scores (DESIGN.md §7). Nulls are dropped. */
export function binScores(values) {
  const counts = BINS.map(() => 0);
  let n = 0;
  for (const value of values) {
    if (value == null || Number.isNaN(value)) continue;
    n += 1;
    const i = BINS.findIndex(([lo, hi]) => value >= lo && value < hi);
    counts[i === -1 ? BINS.length - 1 : i] += 1;
  }
  return { counts, n };
}

function binLabel(i) {
  const [lo, hi] = BINS[i];
  return `${lo.toFixed(2)}–${Math.min(hi, 1).toFixed(2)}`;
}

/** The tiny spread figure beside a scorer mean: grey bars, `0 · 50 · 100` underneath, one tooltip. */
export default function Histogram({ values, label }) {
  const { counts, n } = binScores(values);
  const max = Math.max(1, ...counts);
  const tip =
    n === 0
      ? `${label}: no scored cases`
      : `${label}: ${n} ${n === 1 ? "case" : "cases"} · ` +
        counts.map((c, i) => `${c} at ${binLabel(i)}`).join(" · ");
  return (
    <Tooltip text={tip}>
      <span className="inline-flex flex-col items-stretch" style={{ width: WIDTH }}>
        <svg
          width={WIDTH}
          height={HEIGHT}
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          role="img"
          aria-label={tip}
          className="block overflow-visible"
        >
          {counts.map((c, i) => {
            const h = c === 0 ? 0 : Math.max(1, Math.round((c / max) * HEIGHT));
            return (
              <g key={i}>
                <title>{`${c} ${c === 1 ? "case" : "cases"} scored ${binLabel(i)}`}</title>
                <rect x={i * (BAR + GAP)} y={0} width={BAR} height={HEIGHT} fill="transparent" />
                {h > 0 && (
                  <rect
                    x={i * (BAR + GAP)}
                    y={HEIGHT - h}
                    width={BAR}
                    height={h}
                    rx={h >= 4 ? 2 : 0}
                    fill="var(--color-secondary)"
                  />
                )}
              </g>
            );
          })}
          <line x1={0} y1={HEIGHT - 0.5} x2={WIDTH} y2={HEIGHT - 0.5} stroke="var(--color-line)" />
        </svg>
        <span className="flex justify-between text-[9px] leading-[10px] text-tertiary" aria-hidden="true">
          <span>0</span>
          <span>50</span>
          <span>100</span>
        </span>
      </span>
    </Tooltip>
  );
}
