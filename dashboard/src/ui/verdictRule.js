// The verdict rule of stats/verdict_rule.py, repeated so the delta slider repaints without a
// request (DESIGN.md §8). Keep identical to the Python: boundaries are grey.
export function verdictFor(ciLow, ciHigh, delta) {
  if (ciHigh < -delta) return "red";
  if (ciLow > delta) return "green";
  return "grey";
}

/** Colour of a segment at `delta`: null stays null (never measured). */
export function colourAt(segment, delta) {
  const v = segment.verdict;
  return v ? verdictFor(v.ci_low, v.ci_high, delta) : null;
}
