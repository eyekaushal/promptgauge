import { Columns } from "@phosphor-icons/react";
import { Popover } from "radix-ui";

/** `Columns (7)` secondary button; a popover of checkboxes, one per hideable column, and Reset. */
export default function ColumnPicker({ columns }) {
  const { visible, hideable, hidden, toggle, reset } = columns;
  if (hideable.length === 0) return null;
  return (
    <Popover.Root>
      <Popover.Trigger asChild>
        <button type="button" className="btn btn-secondary">
          <Columns size={14} />
          Columns ({visible.length})
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          align="end"
          sideOffset={6}
          collisionPadding={8}
          className="pop z-30 flex w-56 flex-col gap-0.5 rounded-md border border-line bg-panel p-2 shadow-pop"
        >
          <div className="px-2 pb-1 text-xs font-medium text-secondary">Columns</div>
          {hideable.map((column) => {
            const Icon = column.icon ?? null;
            const on = !hidden.includes(column.key);
            return (
              <label
                key={column.key}
                className="flex h-7 cursor-pointer items-center gap-2 rounded-sm px-2 text-base hover:bg-surface-2"
              >
                <input
                  type="checkbox"
                  checked={on}
                  onChange={() => toggle(column.key)}
                  className="accent-accent"
                />
                {Icon && <Icon size={12} className="text-secondary" aria-hidden="true" />}
                <span className="truncate">{column.label}</span>
              </label>
            );
          })}
          <button
            type="button"
            onClick={reset}
            disabled={hidden.length === 0}
            className="mt-1 h-7 rounded-sm px-2 text-left text-sm text-secondary hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-45"
          >
            Reset to all columns
          </button>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}
