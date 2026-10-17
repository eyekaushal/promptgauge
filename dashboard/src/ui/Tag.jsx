import Tooltip from "./Tooltip.jsx";

/** 11 px, 500, soft background with ink text. `tone` picks a status soft colour; `tip` is the
 * word behind the colour, shown as a tooltip (F8.5). */
const TONES = {
  neutral: "bg-surface-2 text-ink",
  ok: "bg-ok-soft text-ink",
  warn: "bg-warn-soft text-ink",
  danger: "bg-danger-soft text-ink",
  secondary: "bg-surface-2 text-secondary",
};

export default function Tag({ children, tone = "neutral", tip = null }) {
  return (
    <Tooltip text={tip}>
      <span
        className={`inline-flex h-5 items-center rounded-sm px-1.5 text-xs font-medium ${TONES[tone]}`}
      >
        {children}
      </span>
    </Tooltip>
  );
}
