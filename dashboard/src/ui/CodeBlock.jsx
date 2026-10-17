import { Check, Copy } from "@phosphor-icons/react";
import { useState } from "react";

/**
 * Mono text on surface-2 with a copy button top-right. `label` names what it is. `wrap={false}`
 * is the Raw view (a pre that scrolls sideways); `numbered` adds a line-number gutter at mono-sm;
 * `yaml` paints each `key:` in secondary.
 */
export default function CodeBlock({
  label,
  text,
  tone = null,
  wrap = true,
  numbered = false,
  yaml = false,
}) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard?.writeText(text ?? "").then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    });
  };
  const empty = text == null || text === "";
  const lines = numbered && !empty ? text.split("\n") : null;
  return (
    <div>
      {label && <div className="mb-1 text-xs font-medium text-secondary">{label}</div>}
      <div
        className={`relative rounded-sm px-3 py-2 font-mono ${
          numbered ? "text-sm leading-[18px]" : "text-mono"
        } ${wrap ? "whitespace-pre-wrap break-words" : "overflow-x-auto whitespace-pre"} ${
          tone === "danger" ? "bg-danger-soft" : "bg-surface-2"
        }`}
      >
        {empty ? (
          <span className="text-tertiary">{"–"}</span>
        ) : lines ? (
          <ol className="m-0 list-none p-0">
            {lines.map((line, i) => (
              <li key={i} className="flex gap-3">
                <span className="w-6 shrink-0 text-right text-tertiary select-none" aria-hidden="true">
                  {i + 1}
                </span>
                <span className="min-w-0 flex-1">{yaml ? <YamlLine line={line} /> : line}</span>
              </li>
            ))}
          </ol>
        ) : (
          text
        )}
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

const KEY = /^(\s*(?:- )?)([\w.-]+)(:)(\s.*|$)/;

/** One YAML line: the key in secondary, the value in ink. */
function YamlLine({ line }) {
  const match = KEY.exec(line);
  if (!match) return line || " ";
  const [, lead, key, colon, rest] = match;
  return (
    <>
      {lead}
      <span className="text-secondary">
        {key}
        {colon}
      </span>
      {rest}
    </>
  );
}
