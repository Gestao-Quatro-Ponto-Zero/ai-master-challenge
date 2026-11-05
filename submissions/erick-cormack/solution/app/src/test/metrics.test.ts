import { describe, expect, it } from "vitest";
import { calcIndicadores, pctParado, sortFocar } from "@/lib/metrics";
import { formatPrazo, formatUSD } from "@/lib/format";
import type { Deal } from "@/hooks/useDeals";

const d = (p: Partial<Deal>) => p as Deal;

describe("regras do Lead Scorer", () => {
  it("focar ordena por score desc e desempata pelo menor prazo", () => {
    const list = [d({ score: 50, dias_ate_limite: 10 }), d({ score: 80, dias_ate_limite: 30 }), d({ score: 50, dias_ate_limite: 2 })];
    expect(list.sort(sortFocar).map((x) => x.dias_ate_limite)).toEqual([30, 2, 10]);
  });
  it("valor parado soma o preço de lista dos deals a requalificar", () => {
    const ind = calcIndicadores([d({ fila: "requalificar", sales_price: 1000 }), d({ fila: "requalificar", sales_price: 500 }), d({ fila: "focar", valor_esperado: 200, momento: "reta final" })]);
    expect(ind.valorParado).toBe(1500);
    expect(ind.retaFinal).toBe(1);
  });
  it("% parado = requalificar ÷ (focar + requalificar + prospectar)", () => {
    expect(pctParado(10, 30, 10)).toBe(0.6);
  });
  it("prazo 0 vira 'hoje' e dinheiro sai sem centavos", () => {
    expect(formatPrazo(0)).toBe("hoje");
    expect(formatUSD(4386.4)).toBe("US$ 4.386");
  });
});

import { buildCurvaPontos } from "@/components/lead/CurvaChart";
describe("curva de ganho", () => {
  it("ignora p_ganho nulo e estende o último valor confiável até o ciclo máximo", () => {
    const curva = [
      { idade: 0, p_ganho: 0.6, n_sobreviventes: 500 },
      { idade: 1, p_ganho: 0.8, n_sobreviventes: 100 },
      { idade: 2, p_ganho: 0.95, n_sobreviventes: 20 },
      { idade: 3, p_ganho: null as unknown as number, n_sobreviventes: 0 },
    ];
    const p = buildCurvaPontos(curva, 100, 3);
    expect(p.map((x) => x.solida)).toEqual([60, 80, null]);
    expect(p.at(-1)).toEqual({ idade: 3, solida: null, tracejada: 80 });
  });
});
