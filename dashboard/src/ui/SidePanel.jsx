import { X } from "@phosphor-icons/react";

/** The 360 px right column: title, close, scrolling body. Hidden under 1100 px (B17: dialog). */
export default function SidePanel({ title, subtitle = null, onClose, children }) {
  return (
    <aside className="hidden w-[360px] shrink-0 flex-col rounded-lg border border-line bg-panel min-[1100px]:flex">
      <div className="flex h-[52px] items-center gap-2 border-b border-line px-5">
        <div className="min-w-0">
          <div className="truncate text-lg font-medium">{title}</div>
          {subtitle && <div className="truncate text-sm text-secondary">{subtitle}</div>}
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="close"
          className="ml-auto rounded-sm p-1 text-secondary hover:bg-surface-2"
        >
          <X size={16} />
        </button>
      </div>
      <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-5">{children}</div>
    </aside>
  );
}
