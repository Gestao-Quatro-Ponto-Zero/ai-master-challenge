import { describe, expect, it } from "vitest";
import { calcResumo, dealsPorFila, distScoreFoco, valorFocoPorRegiao } from "@/lib/homeStats";
import type { Deal } from "@/hooks/useDeals";

function deal(parcial: Partial<Deal>): Deal {
  return { fila: null, score: null, sales_price: null, valor_esperado: null, regional_office: null, sem_conta: null, ...parcial } as Deal;
}

describe("calcResumo", () => {
  it("soma pipeline, foco e parados", () => {
    const r = calcResumo([
      deal({ fila: "focar", sales_price: 1000, valor_esperado: 700 }),
      deal({ fila: "focar", sales_price: 2000, valor_esperado: 800 }),
      deal({ fila: "requalificar", sales_price: 5000 }),
      deal({ fila: "prospectar", sales_price: 500, sem_conta: true }),
    ]);
    expect(r.abertos).toBe(4);
    expect(r.valorPipeline).toBe(8500);
    expect(r.focar).toBe(2);
    expect(r.valorEsperadoFoco).toBe(1500);
    expect(r.requalificar).toBe(1);
    expect(r.valorParado).toBe(5000);
    expect(r.pctParado).toBe(0.25);
    expect(r.semConta).toBe(1);
  });

  it("lista vazia não divide por zero", () => {
    const r = calcResumo([]);
    expect(r.pctParado).toBe(0);
    expect(r.abertos).toBe(0);
  });
});

describe("dealsPorFila", () => {
  it("conta por fila na ordem focar, prospectar, requalificar", () => {
    const r = dealsPorFila([
      deal({ fila: "requalificar" }),
      deal({ fila: "focar" }),
      deal({ fila: "focar" }),
      deal({ fila: "prospectar" }),
    ]);
    expect(r.map((x) => x.fila)).toEqual(["focar", "prospectar", "requalificar"]);
    expect(r.map((x) => x.total)).toEqual([2, 1, 1]);
  });
});

describe("valorFocoPorRegiao", () => {
  it("agrupa só deals em foco e ordena pelo valor", () => {
    const r = valorFocoPorRegiao([
      deal({ fila: "focar", regional_office: "Central", valor_esperado: 100 }),
      deal({ fila: "focar", regional_office: "Central", valor_esperado: 50 }),
      deal({ fila: "focar", regional_office: "West", valor_esperado: 300 }),
      deal({ fila: "requalificar", regional_office: "West", valor_esperado: 999 }),
    ]);
    expect(r).toEqual([
      { regiao: "West", valor: 300, deals: 1 },
      { regiao: "Central", valor: 150, deals: 2 },
    ]);
  });
});

describe("distScoreFoco", () => {
  it("distribui em faixas de 10 e ignora fora de foco ou sem score", () => {
    const r = distScoreFoco([
      deal({ fila: "focar", score: 0 }),
      deal({ fila: "focar", score: 95 }),
      deal({ fila: "focar", score: 100 }),
      deal({ fila: "prospectar", score: 50 }),
      deal({ fila: "focar", score: null }),
    ]);
    expect(r[0]!.total).toBe(1);
    expect(r[5]!.total).toBe(0);
    expect(r[9]!.total).toBe(2);
    expect(r.reduce((s, f) => s + f.total, 0)).toBe(3);
  });
});
