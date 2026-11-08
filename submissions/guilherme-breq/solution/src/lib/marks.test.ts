import { describe, expect, it } from "vitest";
import { isResolved, MARKS_KEY, parseMarks, serializeMarks, withMark } from "./marks";

describe("parseMarks", () => {
  it("sem nada salvo, devolve vazio", () => {
    expect(parseMarks(null)).toEqual({});
    expect(parseMarks("")).toEqual({});
  });

  it("JSON inválido não quebra: devolve vazio", () => {
    expect(parseMarks("{não é json")).toEqual({});
    expect(parseMarks("undefined")).toEqual({});
  });

  it("formato fora do esperado (array, número, versão antiga ou futura) é ignorado", () => {
    expect(parseMarks("[]")).toEqual({});
    expect(parseMarks("42")).toEqual({});
    expect(parseMarks('{"v":2,"marks":{"a":"feito"}}')).toEqual({});
    expect(parseMarks('{"marks":{"a":"feito"}}')).toEqual({});
    expect(parseMarks('{"v":1,"marks":[1,2]}')).toEqual({});
  });

  it("lê as marcações válidas e descarta as inválidas", () => {
    const raw = '{"v":1,"marks":{"a":"feito","b":"adiado","c":"morto","d":"xyz","e":3,"f":null}}';
    expect(parseMarks(raw)).toEqual({ a: "feito", b: "adiado", c: "morto" });
  });

  it("chaves perigosas não poluem o objeto", () => {
    const m = parseMarks('{"v":1,"marks":{"__proto__":"feito","a":"feito"}}');
    expect(Object.keys(m)).toEqual(["a"]);
    expect(({} as Record<string, unknown>).feito).toBeUndefined();
  });
});

describe("serializeMarks", () => {
  it("vai e volta sem perder nada", () => {
    const m = { a: "feito", b: "adiado", c: "morto" } as const;
    expect(parseMarks(serializeMarks(m))).toEqual(m);
  });

  it("a chave de armazenamento é versionada", () => {
    expect(MARKS_KEY).toMatch(/:v1$/);
  });
});

describe("withMark", () => {
  it("marca sem mexer no objeto original", () => {
    const base = { a: "feito" } as const;
    const next = withMark(base, "b", "adiado");
    expect(next).toEqual({ a: "feito", b: "adiado" });
    expect(base).toEqual({ a: "feito" });
  });

  it("trocar a marcação substitui a anterior e null remove (desfazer)", () => {
    expect(withMark({ a: "adiado" }, "a", "feito")).toEqual({ a: "feito" });
    expect(withMark({ a: "feito", b: "feito" }, "a", null)).toEqual({ b: "feito" });
  });
});

describe("isResolved", () => {
  it("feito e 'não está vivo' resolvem o deal; adiado e sem marca não", () => {
    expect(isResolved("feito")).toBe(true);
    expect(isResolved("morto")).toBe(true);
    expect(isResolved("adiado")).toBe(false);
    expect(isResolved(undefined)).toBe(false);
  });
});
