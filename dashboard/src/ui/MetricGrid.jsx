import Metric from "./Metric.jsx";

/**
 * Groups of metrics in a row with a hairline between groups (DESIGN.md §7).
 * groups: [[{ key?, label, value, hint? }, …], …]
 */
export default function MetricGrid({ groups }) {
  const shown = groups.filter((group) => group.length > 0);
  return (
    <div className="flex flex-wrap border-b border-line px-5 py-3">
      {shown.map((group, i) => (
        <div
          key={i}
          className={`flex flex-wrap gap-x-6 gap-y-2 ${i > 0 ? "ml-6 border-l border-line pl-6" : ""}`}
        >
          {group.map((metric) => (
            <Metric
              key={metric.key ?? metric.label}
              label={metric.label}
              value={metric.value}
              hint={metric.hint}
            />
          ))}
        </div>
      ))}
    </div>
  );
}
