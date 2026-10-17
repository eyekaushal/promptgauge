import { Check, Copy } from "@phosphor-icons/react";
import { useState } from "react";

/** Mono text on surface-2 with a copy button top-right. `label` names what it is. */
export default function CodeBlock({ label, text, tone = null }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard?.writeText(text ?? "").then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    });
  };
  const empty = text == null || text === "";
  return (
    <div>
      {label && <div className="mb-1 text-xs font-medium text-secondary">{label}</div>}
      <div
        className={`relative rounded-sm px-3 py-2 font-mono text-mono whitespace-pre-wrap break-words ${
          tone === "danger" ? "bg-danger-soft" : "bg-surface-2"
        }`}
      >
        {empty ? <span className="text-tertiary">{"–"}</span> : text}
        {!empty && (
          <button
            type="button"
            onClick={copy}
            aria-label={`copy ${label ?? "text"}`}
            className="absolute top-1.5 right-1.5 rounded-sm p-1 text-secondary hover:bg-surface-3"
          >
            {copied ? <Check size={14} /> : <Copy size={14} />}
          </button>
        )}
      </div>
    </div>
  );
}
