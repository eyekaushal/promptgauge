import Tag from "./Tag.jsx";

const TONE = { done: "ok", partial: "warn", stopped: "warn", running: "secondary" };
const WORD = {
  done: "done: every call succeeded",
  partial: "partial: some calls failed; their cases have no score",
  running: "running, or the process died before finishing",
};

/** The experiment status as a word: done / partial / stopped: reason / running. */
export default function StatusTag({ status, stoppedReason = null }) {
  const label = status === "stopped" && stoppedReason ? `stopped: ${stoppedReason}` : status;
  const tip =
    status === "stopped"
      ? `stopped before finishing (${stoppedReason ?? "error"}); what was measured is kept`
      : WORD[status] ?? status;
  return (
    <Tag tone={TONE[status] ?? "neutral"} tip={tip}>
      {label}
    </Tag>
  );
}
