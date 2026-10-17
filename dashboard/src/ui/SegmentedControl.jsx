import Tooltip from "./Tooltip.jsx";

/**
 * One pressed option out of a few (DESIGN.md §7): the display filters and Pretty / Raw.
 * options: [{ value, label, tip? }]
 */
export default function SegmentedControl({ options, value, onChange, size = "md", label = null }) {
  const small = size === "sm";
  return (
    <div
      role="group"
      aria-label={label ?? undefined}
      className={`inline-flex shrink-0 overflow-hidden rounded-sm border border-line-strong bg-panel ${
        small ? "h-6" : "h-8"
      }`}
    >
      {options.map((option, i) => {
        const on = option.value === value;
        return (
          <Tooltip key={option.value} text={option.tip ?? null}>
            <button
              type="button"
              aria-pressed={on}
              onClick={() => onChange(option.value)}
              className={`${small ? "px-1.5 text-xs" : "px-2.5 text-base"} font-medium transition-colors duration-120 ease-out ${
                i > 0 ? "border-l border-line-strong" : ""
              } ${on ? "bg-surface-3 text-ink" : "text-secondary hover:bg-surface-2 hover:text-ink"}`}
            >
              {option.label}
            </button>
          </Tooltip>
        );
      })}
    </div>
  );
}
