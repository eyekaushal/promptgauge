/** One number with an xs label; the totals row of the Ablation screen. */
export default function StatTile({ label, value, hint = null }) {
  return (
    <div className="flex min-w-[96px] flex-col gap-0.5 rounded-md bg-surface-2 px-3 py-2">
      <span className="text-xs font-medium text-secondary">{label}</span>
      <span className="text-lg font-medium">{value}</span>
      {hint && <span className="text-sm text-secondary">{hint}</span>}
    </div>
  );
}
