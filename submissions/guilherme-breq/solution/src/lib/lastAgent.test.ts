import { describe, expect, it } from "vitest";
import { AGENT_KEY, parseAgent, serializeAgent } from "./lastAgent";

describe("parseAgent", () => {
  it("sem nada salvo ou vazio, ninguém lembrado", () => {
    expect(parseAgent(null)).toBe("");
    expect(parseAgent("")).toBe("");
  });

  it("JSON inválido não quebra", () => {
    expect(parseAgent("{lixo")).toBe("");
    expect(parseAgent("Rosalina Dieter")).toBe("");
  });

  it("formato, versão ou tipo errados são ignorados", () => {
    expect(parseAgent("[]")).toBe("");
    expect(parseAgent("42")).toBe("");
    expect(parseAgent('{"agent":"Rosalina Dieter"}')).toBe("");
    expect(parseAgent('{"v":2,"agent":"Rosalina Dieter"}')).toBe("");
    expect(parseAgent('{"v":1,"agent":42}')).toBe("");
    expect(parseAgent('{"v":1,"agent":null}')).toBe("");
  });

  it("nome gigante é descartado (lixo, não nome de vendedor)", () => {
    expect(parseAgent(serializeAgent("x".repeat(500)))).toBe("");
  });

  it("vai e volta, com a chave versionada", () => {
    expect(parseAgent(serializeAgent("Rosalina Dieter"))).toBe("Rosalina Dieter");
    expect(AGENT_KEY).toMatch(/:v1$/);
  });
});
