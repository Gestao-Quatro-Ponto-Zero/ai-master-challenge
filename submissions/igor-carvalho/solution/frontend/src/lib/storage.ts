export interface KeyValueStore {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

/** localStorage quando existe e está liberado; senão null (modo privado, SSR, testes sem DOM). */
export function browserStore(): KeyValueStore | null {
  try {
    return typeof window !== 'undefined' ? window.localStorage : null;
  } catch {
    return null;
  }
}

export function readJson<T>(store: KeyValueStore | null, key: string, fallback: T): T {
  if (!store) return fallback;
  try {
    const raw = store.getItem(key);
    return raw === null ? fallback : (JSON.parse(raw) as T);
  } catch {
    return fallback;
  }
}

export function writeJson(store: KeyValueStore | null, key: string, value: unknown): void {
  if (!store) return;
  try {
    store.setItem(key, JSON.stringify(value));
  } catch {
    /* sem espaço ou bloqueado: segue sem persistir */
  }
}
