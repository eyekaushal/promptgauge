// Client-side CSV for "Download results" (DESIGN.md §7 Menu). RFC 4180 quoting; nothing is sent anywhere.

/** columns: [{ key, label, value?(row) }]; every cell is quoted when it holds a comma, quote or newline. */
export function toCsv(columns, rows) {
  const header = columns.map((c) => cell(c.label)).join(",");
  const body = rows.map((row) =>
    columns.map((c) => cell(c.value ? c.value(row) : row[c.key])).join(","),
  );
  return [header, ...body].join("\r\n") + "\r\n";
}

/** Hands the browser a file to save; the object URL is released once the click has fired. */
export function downloadText(filename, text, type = "text/csv;charset=utf-8") {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

function cell(value) {
  if (value == null) return "";
  const text = String(value);
  return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}
