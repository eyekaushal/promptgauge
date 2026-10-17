import { CaretDown, CaretUp } from "@phosphor-icons/react";
import { useMemo, useState } from "react";

/**
 * Hairline rows, sm headers with a type glyph, numbers right-aligned, sort by header click, row
 * click selects (DESIGN.md §7).
 * columns: [{ key, label, icon?, align?: "right", render?(row), sortValue?(row), width?, muted? }]
 * `rowHeight` is 36 on run lists and 40 on per-case tables; `numbered` adds a muted row-number
 * column (1-based after sorting).
 */
export default function Table({
  columns,
  rows,
  rowKey,
  onRowClick = null,
  selectedKey = null,
  rowClass = null,
  rowTitle = null,
  defaultSort = null,
  rowHeight = 36,
  numbered = false,
}) {
  const [sort, setSort] = useState(defaultSort);
  const sorted = useMemo(() => {
    if (!sort) return rows;
    const column = columns.find((c) => c.key === sort.key);
    if (!column) return rows;
    const value = column.sortValue ?? ((row) => row[column.key]);
    const direction = sort.direction === "asc" ? 1 : -1;
    return [...rows].sort((a, b) => compare(value(a), value(b)) * direction);
  }, [rows, columns, sort]);

  const toggle = (key) =>
    setSort((s) =>
      s?.key === key
        ? { key, direction: s.direction === "asc" ? "desc" : "asc" }
        : { key, direction: "asc" },
    );
  const rowClassName = rowHeight === 40 ? "h-10" : "h-9";

  return (
    <div className="min-h-0 flex-1 overflow-auto">
      <table className="w-full border-collapse whitespace-nowrap">
        <thead className="sticky top-0 z-10 bg-panel">
          <tr className="h-8 border-b border-line text-left text-sm font-medium text-secondary">
            {numbered && <th className="w-10 px-3" aria-label="row" />}
            {columns.map((column) => {
              const Icon = column.icon ?? null;
              return (
                <th
                  key={column.key}
                  style={column.width ? { width: column.width } : undefined}
                  className={`px-3 ${column.align === "right" ? "text-right" : ""}`}
                >
                  <button
                    type="button"
                    onClick={() => toggle(column.key)}
                    className="inline-flex items-center gap-1 rounded-sm hover:text-ink"
                  >
                    {Icon && <Icon size={12} className="shrink-0" aria-hidden="true" />}
                    {column.label}
                    {sort?.key === column.key &&
                      (sort.direction === "asc" ? <CaretUp size={10} /> : <CaretDown size={10} />)}
                  </button>
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row, position) => {
            const key = rowKey(row);
            const selected = selectedKey != null && key === selectedKey;
            return (
              <tr
                key={key}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                title={rowTitle ? (rowTitle(row) ?? undefined) : undefined}
                className={
                  `relative ${rowClassName} border-b border-line transition-colors duration-120 ease-out ` +
                  (onRowClick ? "cursor-pointer hover:bg-surface-2 " : "") +
                  (selected ? "bg-accent-soft " : "") +
                  (rowClass ? rowClass(row) : "")
                }
              >
                {numbered && (
                  <td
                    className={`px-3 text-right text-sm text-tertiary ${
                      selected ? "shadow-[inset_2px_0_0_0_var(--color-accent)]" : ""
                    }`}
                  >
                    {position + 1}
                  </td>
                )}
                {columns.map((column, i) => (
                  <td
                    key={column.key}
                    className={`max-w-[420px] truncate px-3 ${
                      column.align === "right" ? "text-right" : ""
                    } ${column.muted ? "text-tertiary" : ""} ${
                      selected && i === 0 && !numbered
                        ? "shadow-[inset_2px_0_0_0_var(--color-accent)]"
                        : ""
                    }`}
                  >
                    {column.render ? column.render(row) : row[column.key]}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function compare(a, b) {
  // Nulls sort last whichever way the column goes.
  if (a == null && b == null) return 0;
  if (a == null) return 1;
  if (b == null) return -1;
  if (typeof a === "number" && typeof b === "number") return a - b;
  return String(a).localeCompare(String(b));
}
