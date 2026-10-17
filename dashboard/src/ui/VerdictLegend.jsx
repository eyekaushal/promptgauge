/** Four swatches, each with its word and the count at the current delta (DESIGN.md §1). */
export const UNMEASURED_WORD = "not measured";

export default function VerdictLegend({ legend, counts }) {
  const entries = [
    ["red", legend.red],
    ["grey", legend.grey],
    ["green", legend.green],
    ["unmeasured", UNMEASURED_WORD],
  ];
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs">
      {entries.map(([verdict, word]) => (
        <span key={verdict} className="flex items-center gap-1.5" title={word}>
          <Swatch verdict={verdict} />
          <span className="font-medium">{verdict}</span>
          <span className="text-secondary">{word}</span>
          <span className="text-tertiary">{counts[verdict] ?? 0}</span>
        </span>
      ))}
    </div>
  );
}

const SWATCH = {
  red: "bg-red",
  grey: "bg-grey",
  green: "bg-green",
  unmeasured: "border border-line-strong bg-transparent",
};

export function Swatch({ verdict }) {
  return <span className={`inline-block size-2.5 rounded-sm ${SWATCH[verdict ?? "unmeasured"]}`} />;
}
