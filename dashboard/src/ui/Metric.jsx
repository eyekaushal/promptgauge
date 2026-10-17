/** One label-above-value cell of a MetricGrid: sm label, md value, optional hint; no background. */
export default function Metric({ label, value, hint = null }) {
  return (
    <div className="flex min-w-[72px] flex-col gap-0.5">
      <span className="text-sm font-medium text-secondary">{label}</span>
      <span className="text-md">{value}</span>
      {hint && <span className="text-sm text-secondary">{hint}</span>}
    </div>
  );
}
