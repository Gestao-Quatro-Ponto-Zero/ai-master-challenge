import { describe, expect, it, vi } from "vitest";

vi.mock("next/cache", () => ({ cacheLife: () => {} }));

import { getPipeline } from "./data";

// Números conferidos de forma independente na análise em Python (analysis/03 e 05).
describe("getPipeline com os dados reais do CRM", async () => {
  const data = await getPipeline();
  const count = (s: string) => data.deals.filter((d) => d.status === s).length;

  it("usa a última data do CRM como 'hoje' e 138 dias como ciclo máximo", () => {
    expect(data.today).toBe("2017-12-31");
    expect(data.maxCycleDays).toBe(138);
  });

  it("separa o pipeline aberto em vivos, zumbis e prospecção", () => {
    expect(data.deals).toHaveLength(2089);
    expect(count("zumbi")).toBe(1291);
    expect(count("ativo")).toBe(298);
    expect(count("prospeccao")).toBe(500);
  });

  it("normaliza GTXPro e encontra preço para todo deal", () => {
    expect(data.deals.some((d) => d.product === "GTXPro")).toBe(false);
    expect(data.deals.every((d) => d.price > 0)).toBe(true);
  });

  it("liga todo deal a manager e região", () => {
    expect(data.deals.every((d) => d.manager !== "—" && d.region !== "—")).toBe(true);
  });

  it("curva de momento (Kaplan-Meier) bate com analysis/06 e cai depois do pico", () => {
    expect(data.decideCurve[0]).toBeCloseTo(0.381, 2);
    expect(data.decideCurve[90]).toBeCloseTo(0.417, 2);
    expect(data.decideCurve[120]).toBeCloseTo(0.125, 2);
    expect(data.decideCurve[135]).toBeCloseTo(0.017, 2);
  });

  it("taxa global de vitória bate com a análise (63,2%)", () => {
    expect(data.globalWinRate).toBeCloseTo(0.6315, 3);
  });
});
