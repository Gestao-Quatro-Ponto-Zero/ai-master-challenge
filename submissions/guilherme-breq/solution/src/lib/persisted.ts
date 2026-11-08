/**
 * Store persistido em localStorage, sem React (testável) e tolerante a storage ruim.
 *
 * Regra do modo "só em memória": ele existe SÓ enquanto a gravação falha (cota estourada, storage
 * bloqueado). Enquanto a gravação funciona, a verdade é o storage: se outra aba removeu a chave ou
 * deu `clear()`, o estado é vazio, nunca o que esta aba gravou antes.
 */
export interface StorageLike {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

export interface PersistedStoreOptions<T> {
  key: string;
  /** Valor de "nada salvo"; a mesma referência a cada leitura vazia. */
  empty: T;
  /** Tolerante: qualquer lixo vira `empty`-equivalente. */
  parse: (raw: string | null) => T;
  serialize: (value: T) => string;
  /** Pode devolver null (SSR, janela privada) ou lançar. */
  storage: () => StorageLike | null;
}

export function createPersistedStore<T>({ key, empty, parse, serialize, storage }: PersistedStoreOptions<T>) {
  let memoryOnly = false;
  let lastRaw: string | null = null;
  let cache: { raw: string | null; value: T } = { raw: null, value: empty };
  const listeners = new Set<() => void>();

  function readRaw(): string | null {
    if (memoryOnly) return lastRaw;
    try {
      return storage()?.getItem(key) ?? null;
    } catch {
      // Leitura bloqueada: o melhor que existe é o que esta aba gravou por último.
      return lastRaw;
    }
  }

  const notify = () => listeners.forEach((l) => l());

  return {
    empty,
    /** Estável: devolve a mesma referência enquanto o texto salvo não muda. */
    getSnapshot(): T {
      const raw = readRaw();
      if (raw !== cache.raw) cache = { raw, value: parse(raw) };
      return cache.value;
    },
    set(next: T) {
      const raw = serialize(next);
      lastRaw = raw;
      try {
        const s = storage();
        if (!s) throw new Error("sem storage");
        s.setItem(key, raw);
        memoryOnly = false;
      } catch {
        memoryOnly = true;
      }
      notify();
    },
    subscribe(onChange: () => void) {
      listeners.add(onChange);
      return () => void listeners.delete(onChange);
    },
    /** Evento `storage` de outra aba: o storage volta a ser a verdade. */
    handleExternalChange() {
      memoryOnly = false;
      notify();
    },
  };
}

export type PersistedStore<T> = ReturnType<typeof createPersistedStore<T>>;
