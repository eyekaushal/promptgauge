// Number and date formats from DESIGN.md §2. One place, so every screen agrees.

const MINUS = "−";

export function score(value) {
  return value == null ? null : value.toFixed(2);
}

export function delta(value) {
  if (value == null) return null;
  const sign = value < 0 ? MINUS : "+";
  return `${sign}${Math.abs(value).toFixed(2)}`;
}

export function interval(low, high) {
  if (low == null || high == null) return null;
  return `[${signed(low)}, ${signed(high)}]`;
}

export function usd(value) {
  return value == null ? null : `$${value.toFixed(2)}`;
}

export function inr(value) {
  return value == null ? null : `₹${Math.round(value).toLocaleString("en-IN")}`;
}

export function count(value) {
  return value == null ? null : value.toLocaleString("en-US");
}

/** A share as a whole percent with a thin space before the sign: `61 %`. */
export function percent(share) {
  return share == null ? null : `${Math.round(share * 100)}\u2009%`;
}

export function duration(createdAt, finishedAt) {
  if (!createdAt || !finishedAt) return null;
  const seconds = Math.round((Date.parse(finishedAt) - Date.parse(createdAt)) / 1000);
  if (Number.isNaN(seconds) || seconds < 0) return null;
  if (seconds < 60) return `${seconds} s`;
  const minutes = Math.floor(seconds / 60);
  return `${minutes} m ${String(seconds % 60).padStart(2, "0")} s`;
}

export function dateTime(iso) {
  if (!iso) return null;
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function shortHash(hash) {
  return hash ? hash.slice(0, 8) : null;
}

function signed(value) {
  return value < 0 ? `${MINUS}${Math.abs(value).toFixed(2)}` : value.toFixed(2);
}
