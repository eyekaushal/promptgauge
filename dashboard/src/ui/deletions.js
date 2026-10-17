// Which runs of the original prompt are missing from the cut prompt. Deletion only (invariant 2)
// means the cut is a subsequence of the original, so a longest-common-subsequence over word and
// whitespace tokens finds the removed runs exactly; the prompts are short, so O(n·m) is fine.

/** → [{ text, removed }] in original order. */
export function deletions(original, cut) {
  const a = tokens(original);
  const b = tokens(cut);
  const n = a.length;
  const m = b.length;
  const table = new Uint32Array((n + 1) * (m + 1));
  const at = (i, j) => i * (m + 1) + j;
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      table[at(i, j)] =
        a[i] === b[j] ? table[at(i + 1, j + 1)] + 1 : Math.max(table[at(i + 1, j)], table[at(i, j + 1)]);
    }
  }
  const runs = [];
  let i = 0;
  let j = 0;
  const push = (text, removed) => {
    const last = runs[runs.length - 1];
    if (last && last.removed === removed) last.text += text;
    else runs.push({ text, removed });
  };
  while (i < n) {
    if (j < m && a[i] === b[j]) {
      push(a[i], false);
      i++;
      j++;
    } else if (j < m && table[at(i, j + 1)] >= table[at(i + 1, j)]) {
      // A token only the cut has: whitespace reshaped by the variant builder. Nothing to show.
      j++;
    } else {
      push(a[i], true);
      i++;
    }
  }
  return runs;
}

function tokens(text) {
  return text.split(/(\s+)/).filter((t) => t !== "");
}
