import Tag from "./Tag.jsx";

const TONE = { done: "ok", partial: "warn", stopped: "warn", running: "secondary" };

/** The experiment status as a word: done / partial / stopped: reason / running. */
export default function StatusTag({ status, stoppedReason = null }) {
  const label = status === "stopped" && stoppedReason ? `stopped: ${stoppedReason}` : status;
  return <Tag tone={TONE[status] ?? "neutral"}>{label}</Tag>;
}
