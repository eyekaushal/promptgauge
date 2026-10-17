import { useEffect, useState } from "react";

/**
 * Request state the way DESIGN.md §8 asks for it: { data, error, loading }. `load` is called
 * again whenever `deps` change; a stale answer never overwrites a newer one; `null` from `load`
 * means "nothing to fetch" and leaves the state empty.
 */
export function useRequest(load, deps) {
  const [state, setState] = useState({ data: null, error: null, loading: false });
  useEffect(() => {
    const promise = load();
    if (!promise) {
      setState({ data: null, error: null, loading: false });
      return undefined;
    }
    let alive = true;
    setState((s) => ({ ...s, error: null, loading: true }));
    promise
      .then((data) => alive && setState({ data, error: null, loading: false }))
      .catch((error) => alive && setState((s) => ({ ...s, error, loading: false })));
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return state;
}
