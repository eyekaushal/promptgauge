import { useCallback, useEffect, useMemo, useState } from "react";

const PREFIX = "promptgauge.columns.";

/**
 * Which columns of a table are shown. Hidden keys live in localStorage under
 * `promptgauge.columns.<screen>`; columns marked `fixed` can never be hidden. Returns the visible
 * columns for `Table` and what `ColumnPicker` needs.
 */
export function useColumns(screen, columns) {
  const storageKey = PREFIX + screen;
  const [hidden, setHidden] = useState(() => read(storageKey));
  useEffect(() => {
    setHidden(read(storageKey));
  }, [storageKey]);

  const toggle = useCallback(
    (key) =>
      setHidden((h) => {
        const next = h.includes(key) ? h.filter((k) => k !== key) : [...h, key];
        write(storageKey, next);
        return next;
      }),
    [storageKey],
  );
  const reset = useCallback(() => {
    write(storageKey, []);
    setHidden([]);
  }, [storageKey]);

  const visible = useMemo(
    () => columns.filter((c) => c.fixed || !hidden.includes(c.key)),
    [columns, hidden],
  );
  const hideable = useMemo(() => columns.filter((c) => !c.fixed), [columns]);
  return { visible, hideable, hidden, toggle, reset };
}

function read(key) {
  try {
    const raw = globalThis.localStorage?.getItem(key);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.filter((k) => typeof k === "string") : [];
  } catch {
    return [];
  }
}

function write(key, hidden) {
  try {
    globalThis.localStorage?.setItem(key, JSON.stringify(hidden));
  } catch {
    // Private windows and blocked storage: the choice lasts for the page only.
  }
}
