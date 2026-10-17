// The run config written the way the user wrote promptgauge.yaml (DESIGN.md §7 CodeBlock).

// Config's own field order, so the dashboard and the file read alike.
const ORDER = [
  "prompt",
  "dataset",
  "model",
  "judge",
  "scorers",
  "repeats",
  "temperature",
  "budget_usd",
  "delta",
  "concurrency",
  "inr_rate",
];

/** `{ name, arg }` scorer specs become `- contains` / `- rubric: helpful`; the rest are scalars. */
export function configToYaml(config) {
  if (!config) return "";
  const keys = [...ORDER.filter((k) => k in config), ...Object.keys(config).filter((k) => !ORDER.includes(k))];
  const lines = [];
  for (const key of keys) {
    const value = config[key];
    if (key === "scorers" && Array.isArray(value)) {
      lines.push("scorers:");
      for (const spec of value) {
        if (spec && typeof spec === "object") {
          lines.push(spec.arg ? `  - ${spec.name}: ${scalar(spec.arg)}` : `  - ${spec.name}`);
        } else {
          lines.push(`  - ${scalar(spec)}`);
        }
      }
    } else if (Array.isArray(value)) {
      lines.push(`${key}:`);
      for (const item of value) lines.push(`  - ${scalar(item)}`);
    } else if (value && typeof value === "object") {
      lines.push(`${key}:`);
      for (const [k, v] of Object.entries(value)) lines.push(`  ${k}: ${scalar(v)}`);
    } else {
      lines.push(`${key}: ${scalar(value)}`);
    }
  }
  return lines.join("\n");
}

function scalar(value) {
  if (value == null) return "null";
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  const text = String(value);
  // Quote only what YAML would otherwise misread: empty, leading symbols, or a colon-space.
  return /^[\w./@-][^#]*$/.test(text) && !text.includes(": ") && !/^(true|false|null|yes|no)$/i.test(text)
    ? text
    : JSON.stringify(text);
}
