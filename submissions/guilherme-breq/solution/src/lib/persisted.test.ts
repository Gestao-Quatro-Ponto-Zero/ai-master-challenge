import { describe, expect, it } from "vitest";
import { MARKS_KEY, parseMarks, serializeMarks, withMark, type Marks } from "./marks";
import { createPersistedStore } from "./persisted";

/** localStorage de mentira, com falhas ligáveis: cota estourada na gravação e leitura bloqueada. */
function fakeStorage(initial: Record<string, string> = {}) {
  const data = new Map(Object.entries(initial));
  const s = {
    failWrites: false,
    failReads: false,
    data,
    getItem(k: string) {
      if (s.failReads) throw new Error("leitura bloqueada");
      return data.get(k) ?? null;
    },
    setItem(k: string, v: string) {
      if (s.failWrites) throw new DOMException("cota", "QuotaExceededError");
      data.set(k, v);
    },
    removeItem: (k: string) => void data.delete(k),
    clear: () => data.clear(),
  };
  return s;
}

const marksStore = (st: ReturnType<typeof fakeStorage> | null) =>
  createPersistedStore<Marks>({ key: MARKS_KEY, empty: {}, parse: parseMarks, serialize: serializeMarks, storage: () => st });

const mark = (store: ReturnType<typeof marksStore>, id: string, m: "feito" | "adiado") => store.set(withMark(store.getSnapshot(), id, m));
const saved = (id: string, m: string) => serializeMarks({ [id]: m } as Marks);

describe("createPersistedStore · caminho normal", () => {
  it("grava no storage e lê de volta", () => {
    const st = fakeStorage();
    const store = marksStore(st);
    mark(store, "a", "feito");
    expect(store.getSnapshot()).toEqual({ a: "feito" });
    expect(parseMarks(st.data.get(MARKS_KEY) ?? null)).toEqual({ a: "feito" });
  });

  it("começa do que já estava salvo", () => {
    const store = marksStore(fakeStorage({ [MARKS_KEY]: saved("x", "adiado") }));
    expect(store.getSnapshot()).toEqual({ x: "adiado" });
  });

  it("devolve a mesma referência enquanto nada muda (exigência do useSyncExternalStore)", () => {
    const store = marksStore(fakeStorage({ [MARKS_KEY]: saved("x", "adiado") }));
    expect(store.getSnapshot()).toBe(store.getSnapshot());
    const vazio = marksStore(fakeStorage());
    expect(vazio.getSnapshot()).toBe(vazio.getSnapshot());
  });

  it("avisa quem assinou a cada gravação e para depois de cancelar", () => {
    const store = marksStore(fakeStorage());
    let calls = 0;
    const off = store.subscribe(() => calls++);
    mark(store, "a", "feito");
    expect(calls).toBe(1);
    off();
    mark(store, "b", "feito");
    expect(calls).toBe(1);
  });
});

describe("createPersistedStore · cota estourada na gravação", () => {
  it("com valor anterior VÁLIDO no storage, a marcação nova aparece junto com a antiga", () => {
    const st = fakeStorage({ [MARKS_KEY]: saved("old", "adiado") });
    const store = marksStore(st);
    st.failWrites = true;
    mark(store, "new", "feito");
    expect(store.getSnapshot()).toEqual({ old: "adiado", new: "feito" });
  });

  it("com valor anterior CORROMPIDO no storage, a marcação nova aparece (a corrompida não volta)", () => {
    const st = fakeStorage({ [MARKS_KEY]: "{lixo" });
    const store = marksStore(st);
    st.failWrites = true;
    mark(store, "new", "feito");
    expect(store.getSnapshot()).toEqual({ new: "feito" });
  });

  it("o modo em memória dura só enquanto a gravação falha: voltou a gravar, volta a persistir", () => {
    const st = fakeStorage();
    const store = marksStore(st);
    st.failWrites = true;
    mark(store, "a", "feito");
    expect(st.data.has(MARKS_KEY)).toBe(false);
    st.failWrites = false;
    mark(store, "b", "feito");
    expect(parseMarks(st.data.get(MARKS_KEY) ?? null)).toEqual({ a: "feito", b: "feito" });
    // e, de novo no caminho normal, a remoção externa vale
    st.removeItem(MARKS_KEY);
    expect(store.getSnapshot()).toEqual({});
  });
});

describe("createPersistedStore · mudança vinda de outra aba", () => {
  it("chave removida em outra aba = estado vazio, não o que esta aba gravou antes", () => {
    const st = fakeStorage();
    const store = marksStore(st);
    mark(store, "a", "feito");
    st.removeItem(MARKS_KEY);
    store.handleExternalChange();
    expect(store.getSnapshot()).toEqual({});
  });

  it("clear() em outra aba = estado vazio", () => {
    const st = fakeStorage();
    const store = marksStore(st);
    mark(store, "a", "feito");
    mark(store, "b", "adiado");
    st.clear();
    store.handleExternalChange();
    expect(store.getSnapshot()).toEqual({});
  });

  it("depois de limpar, a próxima marcação não ressuscita as antigas", () => {
    const st = fakeStorage();
    const store = marksStore(st);
    mark(store, "a", "feito");
    st.clear();
    store.handleExternalChange();
    mark(store, "b", "feito");
    expect(store.getSnapshot()).toEqual({ b: "feito" });
  });

  it("o evento de outra aba avisa quem assinou", () => {
    const store = marksStore(fakeStorage());
    let calls = 0;
    store.subscribe(() => calls++);
    store.handleExternalChange();
    expect(calls).toBe(1);
  });

  it("a escrita de outra aba vira o estado local, mesmo se esta aba estava em memória", () => {
    const st = fakeStorage();
    const store = marksStore(st);
    st.failWrites = true;
    mark(store, "local", "feito");
    st.failWrites = false;
    st.data.set(MARKS_KEY, saved("outra", "adiado"));
    store.handleExternalChange();
    expect(store.getSnapshot()).toEqual({ outra: "adiado" });
  });
});

describe("createPersistedStore · storage indisponível", () => {
  it("sem storage nenhum (janela privada, política do navegador), segue em memória sem lançar", () => {
    const store = marksStore(null);
    expect(store.getSnapshot()).toEqual({});
    mark(store, "a", "feito");
    expect(store.getSnapshot()).toEqual({ a: "feito" });
  });

  it("leitura bloqueada depois de uma gravação: mantém o que gravou", () => {
    const st = fakeStorage();
    const store = marksStore(st);
    mark(store, "a", "feito");
    st.failReads = true;
    expect(store.getSnapshot()).toEqual({ a: "feito" });
    expect(() => mark(store, "b", "adiado")).not.toThrow();
    expect(store.getSnapshot()).toEqual({ a: "feito", b: "adiado" });
  });
});
