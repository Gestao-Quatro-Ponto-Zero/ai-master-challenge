import { useEffect, useRef, useState } from "react";
import { ApiError } from "../api";

interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  status: number | null;
}

/** Executa `fetcher` sempre que `deps` mudar, ignorando respostas de
 * requisições obsoletas (evita race condition ao trocar filtros rápido). */
export function useAsync<T>(fetcher: () => Promise<T>, deps: unknown[]): AsyncState<T> {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    loading: true,
    error: null,
    status: null,
  });
  const requestId = useRef(0);

  useEffect(() => {
    const id = ++requestId.current;
    setState((prev) => ({ ...prev, loading: true, error: null }));

    fetcher()
      .then((data) => {
        if (requestId.current === id) setState({ data, loading: false, error: null, status: null });
      })
      .catch((err: unknown) => {
        if (requestId.current === id) {
          const message = err instanceof Error ? err.message : "erro desconhecido";
          const status = err instanceof ApiError ? err.status : null;
          setState({ data: null, loading: false, error: message, status });
        }
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return state;
}
