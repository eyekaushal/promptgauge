import { CaretDown, CaretRight } from "@phosphor-icons/react";
import { useState } from "react";

/**
 * A collapsible section of a side panel or header (DESIGN.md §7): 28 px header row with an icon,
 * the name, an optional actions slot and a chevron; the body is whatever the screen puts in it.
 */
export default function Section({
  Icon = null,
  title,
  actions = null,
  defaultOpen = true,
  open: controlled = undefined,
  onOpenChange = null,
  children,
}) {
  const [own, setOwn] = useState(defaultOpen);
  const open = controlled ?? own;
  const setOpen = (next) => {
    if (controlled === undefined) setOwn(next);
    onOpenChange?.(next);
  };
  return (
    <section className="flex flex-col">
      <div className="flex h-7 items-center gap-1.5">
        <button
          type="button"
          onClick={() => setOpen(!open)}
          aria-expanded={open}
          className="flex h-7 min-w-0 flex-1 items-center gap-1.5 rounded-sm text-left text-sm font-medium text-secondary hover:text-ink"
        >
          {open ? (
            <CaretDown size={12} className="shrink-0" aria-hidden="true" />
          ) : (
            <CaretRight size={12} className="shrink-0" aria-hidden="true" />
          )}
          {Icon && <Icon size={12} className="shrink-0" aria-hidden="true" />}
          <span className="truncate">{title}</span>
        </button>
        {actions && <div className="flex shrink-0 items-center gap-1">{actions}</div>}
      </div>
      {open && <div className="flex flex-col gap-2 pt-1">{children}</div>}
    </section>
  );
}
