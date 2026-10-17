/** One fact for the title row: a 12 px icon and sm text on surface-2, never coloured (DESIGN.md §7). */
export default function Chip({ Icon = null, children, title = null }) {
  return (
    <span
      title={title ?? undefined}
      className="inline-flex h-6 shrink-0 items-center gap-1.5 rounded-sm bg-surface-2 px-2 text-sm text-ink"
    >
      {Icon && <Icon size={12} className="text-secondary" aria-hidden="true" />}
      {children}
    </span>
  );
}
