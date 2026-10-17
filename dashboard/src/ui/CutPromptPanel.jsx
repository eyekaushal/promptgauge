import { Check, Copy } from "@phosphor-icons/react";
import { useMemo, useState } from "react";

import Dash from "./Dash.jsx";
import { deletions } from "./deletions.js";
import { count, delta as fmtDelta, inr, interval, score, usd } from "./format.js";
import Tag from "./Tag.jsx";

/**
 * Original and cut side by side; tokens, confirmation beside baseline, money saved at
 * `callsPerMonth` (F6.9: tokens removed × input price per token × calls), copy button.
 */
export default function CutPromptPanel({
  promptText,
  ablation,
  delta,
  inputUsdPerMillion,
  callsPerMonth,
  inrRate,
  onCallsPerMonth,
  stopped,
}) {
  const [copied, setCopied] = useState(false);
  const [draft, setDraft] = useState(String(callsPerMonth));
  const runs = useMemo(
    () => (ablation ? deletions(promptText, ablation.cut_prompt) : []),
    [promptText, ablation],
  );
  if (!ablation) {
    return (
      <section className="border-t border-line px-5 py-4 text-sm text-secondary">
        The run stopped before a cut prompt was produced; nothing to show here.
      </section>
    );
  }

  const removed = ablation.tokens_before - ablation.tokens_after;
  const share = ablation.tokens_before ? removed / ablation.tokens_before : 0;
  const perToken = inputUsdPerMillion == null ? null : inputUsdPerMillion / 1_000_000;
  const savedUsd = perToken == null ? null : removed * perToken * callsPerMonth;
  const diff = ablation.cut_score == null ? null : ablation.cut_score - ablation.baseline_score;

  const copy = () =>
    navigator.clipboard?.writeText(ablation.cut_prompt).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    });
  const commit = () => {
    const value = Number.parseInt(draft, 10);
    if (Number.isInteger(value) && value >= 1 && value !== callsPerMonth) onCallsPerMonth(value);
    else setDraft(String(callsPerMonth));
  };

  return (
    <section className="flex flex-col gap-3 border-t border-line px-5 py-4">
      <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
        <span className="text-lg font-medium">Cut prompt</span>
        <Confirmation ablation={ablation} diff={diff} delta={delta} stopped={stopped} />
        <span>
          <span className="text-xs font-medium text-secondary">tokens </span>
          {count(ablation.tokens_before)} → {count(ablation.tokens_after)}
          <span className="text-secondary">
            {" "}
            (−{count(removed)}, −{Math.round(share * 100)}%)
          </span>
        </span>
        <button
          type="button"
          onClick={copy}
          className="ml-auto flex h-8 items-center gap-1.5 rounded-md bg-accent px-3 text-base text-accent-fg hover:opacity-90"
        >
          {copied ? <Check size={14} /> : <Copy size={14} />}
          {copied ? "Copied" : "Copy cut prompt"}
        </button>
      </div>
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2 text-sm">
        <span className="text-xs font-medium text-secondary">saves</span>
        {savedUsd == null ? (
          <Dash word="no price for this model" />
        ) : (
          <span>
            <span className="font-medium">{usd(savedUsd)}</span>
            <span className="text-secondary"> / </span>
            <span className="font-medium">{inr(savedUsd * inrRate)}</span>
            <span className="text-secondary"> a month at</span>
          </span>
        )}
        <input
          type="number"
          min={1}
          step={1000}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={commit}
          onKeyDown={(e) => e.key === "Enter" && e.currentTarget.blur()}
          aria-label="calls per month"
          className="h-8 w-32 rounded-sm border border-line-strong bg-panel px-2 text-base"
        />
        <span className="text-secondary">calls, ₹{inrRate} per $</span>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <Column label="original, removed runs struck through">
          {runs.map((run, i) =>
            run.removed ? (
              <del key={i} className="rounded-[3px] bg-red-soft px-0.5 text-secondary line-through">
                {run.text}
              </del>
            ) : (
              <span key={i}>{run.text}</span>
            ),
          )}
        </Column>
        <Column label="cut prompt">{ablation.cut_prompt}</Column>
      </div>
    </section>
  );
}

function Confirmation({ ablation, diff, delta, stopped }) {
  const base = (
    <span>
      <span className="text-xs font-medium text-secondary">baseline </span>
      {score(ablation.baseline_score)}
    </span>
  );
  if (ablation.cut_score == null) {
    return (
      <>
        {base}
        <Tag tone="danger">cut prompt not confirmed</Tag>
        <span className="text-secondary">
          no confirmation run{stopped ? ` (stopped: ${stopped})` : ""}; shown as a suggestion
        </span>
      </>
    );
  }
  return (
    <>
      {base}
      <span>
        <span className="text-xs font-medium text-secondary">cut </span>
        {score(ablation.cut_score)}
        <span className="text-secondary"> {interval(ablation.cut_ci_low, ablation.cut_ci_high)}</span>
      </span>
      {ablation.confirmed ? (
        <Tag tone="ok">confirmed</Tag>
      ) : (
        <Tag tone="danger">cut prompt not confirmed</Tag>
      )}
      <span className="text-secondary">
        {fmtDelta(diff)} vs baseline
        {ablation.confirmed ? "" : ` (below baseline − ${delta.toFixed(2)}); shown as a suggestion`}
      </span>
    </>
  );
}

function Column({ label, children }) {
  return (
    <div className="min-w-0">
      <div className="mb-1 text-xs font-medium text-secondary">{label}</div>
      <pre className="max-h-[480px] overflow-auto rounded-sm bg-surface-2 px-3 py-2 font-mono text-mono whitespace-pre-wrap break-words">
        {children}
      </pre>
    </div>
  );
}
