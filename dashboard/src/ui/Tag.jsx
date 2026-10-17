import { X } from "@phosphor-icons/react";

import Tooltip from "./Tooltip.jsx";

/** 11 px, 500, soft background with ink text. `tone` picks a status soft colour; `tip` is the
 * word behind the colour, shown as a tooltip (F8.5). `onClick` makes the tag a button (a case tag
 * adds itself to the filter); `onRemove` adds an × (an active filter chip). */
const TONES = {
  neutral: "bg-surface-2 text-ink",
  ok: "bg-ok-soft text-ink",
  warn: "bg-warn-soft text-ink",
  danger: "bg-danger-soft text-ink",
  secondary: "bg-surface-2 text-secondary",
};

export default function Tag({ children, tone = "neutral", tip = null, onClick = null, onRemove = null }) {
  const base = `inline-flex h-5 items-center rounded-sm px-1.5 text-xs font-medium ${TONES[tone]}`;
  if (onClick) {
    return (
      <Tooltip text={tip}>
        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation();
            onClick();
          }}
          className={`${base} hover:bg-surface-3`}
        >
          {children}
        </button>
      </Tooltip>
    );
  }
  return (
    <Tooltip text={tip}>
      <span className={`${base} ${onRemove ? "gap-1 pr-1" : ""}`}>
        {children}
        {onRemove && (
          <button
            type="button"
            onClick={onRemove}
            aria-label={`remove filter ${typeof children === "string" ? children : ""}`.trim()}
            className="flex size-3.5 items-center justify-center rounded-full text-secondary hover:bg-surface-3 hover:text-ink"
          >
            <X size={9} weight="bold" />
          </button>
        )}
      </span>
    </Tooltip>
  );
}
