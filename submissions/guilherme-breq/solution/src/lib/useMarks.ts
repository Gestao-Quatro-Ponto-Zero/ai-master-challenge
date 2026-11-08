"use client";

import { useCallback, useSyncExternalStore } from "react";
import { AGENT_KEY, parseAgent, serializeAgent } from "./lastAgent";
import { MARKS_KEY, parseMarks, serializeMarks, withMark, type Mark, type Marks } from "./marks";
import { createPersistedStore, type PersistedStore } from "./persisted";

/** `window.localStorage` pode lançar (janela privada, política do navegador) ou não existir (SSR). */
function browserStorage() {
  try {
    return typeof window === "undefined" ? null : window.localStorage;
  } catch {
    return null;
  }
}

const marksStore = createPersistedStore<Marks>({ key: MARKS_KEY, empty: {}, parse: parseMarks, serialize: serializeMarks, storage: browserStorage });
const agentStore = createPersistedStore<string>({ key: AGENT_KEY, empty: "", parse: parseAgent, serialize: serializeAgent, storage: browserStorage });

/**
 * Lê o store via useSyncExternalStore: o servidor e a hidratação veem "vazio" (sem divergência) e o
 * cliente atualiza logo depois. Mudanças feitas em outra aba chegam pelo evento `storage`.
 */
function useStore<T>(store: PersistedStore<T>, key: string): T {
  const subscribe = useCallback(
    (onChange: () => void) => {
      const off = store.subscribe(onChange);
      const onStorage = (e: StorageEvent) => {
        if (e.key === key || e.key === null) store.handleExternalChange();
      };
      window.addEventListener("storage", onStorage);
      return () => {
        off();
        window.removeEventListener("storage", onStorage);
      };
    },
    [store, key],
  );
  return useSyncExternalStore(subscribe, store.getSnapshot, () => store.empty);
}

export function useMarks() {
  const marks = useStore(marksStore, MARKS_KEY);
  const setMark = useCallback((id: string, mark: Mark | null) => marksStore.set(withMark(marksStore.getSnapshot(), id, mark)), []);
  return { marks, setMark };
}

/** Último vendedor que abriu o app neste navegador ("" = ninguém). */
export function useLastAgent() {
  const agent = useStore(agentStore, AGENT_KEY);
  const remember = useCallback((name: string) => agentStore.set(name), []);
  const forget = useCallback(() => agentStore.set(""), []);
  return { agent, remember, forget };
}
