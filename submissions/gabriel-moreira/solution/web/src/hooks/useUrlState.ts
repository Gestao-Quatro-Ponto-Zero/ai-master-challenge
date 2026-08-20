import { useCallback, useEffect, useState } from "react";

/** Sincroniza um objeto de estado simples (aba + filtros) com a URL —
 * exceto identidade, que exige nova seleção (Requirement "Filtros"). */
export function useUrlState<T extends object>(defaults: T) {
  const read = useCallback((): T => {
    const usp = new URLSearchParams(window.location.search);
    const next: Record<string, string | undefined> = { ...(defaults as object) };
    for (const key of Object.keys(defaults)) {
      const value = usp.get(key);
      if (value !== null) next[key] = value;
    }
    return next as T;
  }, [defaults]);

  const [state, setState] = useState<T>(read);

  useEffect(() => {
    const onPopState = () => setState(read());
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, [read]);

  const update = useCallback((patch: Partial<T>) => {
    setState((prev) => {
      const next = { ...prev, ...patch };
      const usp = new URLSearchParams();
      for (const [key, value] of Object.entries(next as object)) {
        if (value) usp.set(key, String(value));
      }
      const query = usp.toString();
      window.history.pushState({}, "", query ? `?${query}` : window.location.pathname);
      return next;
    });
  }, []);

  return [state, update] as const;
}
