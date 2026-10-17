import { Check, CircleDashed, Square, Warning } from "@phosphor-icons/react";

import Tag from "./Tag.jsx";

const TONE = { done: "ok", partial: "warn", stopped: "warn", running: "secondary" };
const ICON = { done: Check, partial: Warning, stopped: Square, running: CircleDashed };
const WORD = {
  done: "done: every call succeeded",
  partial: "partial: some calls failed; their cases have no score",
  running: "running, or the process died before finishing",
};

/** The experiment status as an icon and a word: ✓ done / △ partial / ■ stopped: reason / ◌ running. */
export default function StatusTag({ status, stoppedReason = null }) {
  const label = status === "stopped" && stoppedReason ? `stopped: ${stoppedReason}` : status;
  const tip =
    status === "stopped"
      ? `stopped before finishing (${stoppedReason ?? "error"}); what was measured is kept`
      : WORD[status] ?? status;
  const Icon = ICON[status] ?? null;
  return (
    <Tag tone={TONE[status] ?? "neutral"} tip={tip}>
      {Icon && (
        <Icon
          size={11}
          weight={status === "stopped" ? "fill" : "bold"}
          className="mr-1 shrink-0"
          aria-hidden="true"
        />
      )}
      {label}
    </Tag>
  );
}
