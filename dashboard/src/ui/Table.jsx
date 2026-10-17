import { CaretDown, CaretUp } from "@phosphor-icons/react";
import { useMemo, useState } from "react";

/**
 * 36 px rows, xs headers, hairlines, numbers right-aligned, sort by header click, row click.
 * columns: [{ key, label, align?: "right", render?(row), sortValue?(row), width? }]
 */
export default function Table({
  columns,
  rows,
  rowKey,
  onRowClick = null,
  selectedKey = null,
  rowClass = null,
  defaultSort = null,
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

  return (
    <div className="min-h-0 flex-1 overflow-auto">
      <table className="w-full border-collapse whitespace-nowrap">
        <thead className="sticky top-0 z-10 bg-panel">
          <tr className="h-8 border-b border-line text-left text-xs font-medium text-secondary">
            {columns.map((column) => (
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
                  {column.label}
                  {sort?.key === column.key &&
                    (sort.direction === "asc" ? <CaretUp size={10} /> : <CaretDown size={10} />)}
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => {
            const key = rowKey(row);
            const selected = selectedKey != null && key === selectedKey;
            return (
              <tr
                key={key}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                className={
                  "relative h-9 border-b border-line transition-colors duration-120 ease-out " +
                  (onRowClick ? "cursor-pointer hover:bg-surface-2 " : "") +
                  (selected ? "bg-accent-soft " : "") +
                  (rowClass ? rowClass(row) : "")
                }
              >
                {columns.map((column, i) => (
                  <td
                    key={column.key}
                    className={`max-w-[420px] truncate px-3 ${
                      column.align === "right" ? "text-right" : ""
                    } ${selected && i === 0 ? "shadow-[inset_2px_0_0_0_var(--color-accent)]" : ""}`}
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
