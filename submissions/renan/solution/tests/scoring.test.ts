import { describe, expect, it } from "vitest";
import type { Deal } from "@/domain/types";
import { buildHistory } from "@/lib/scoring/history";
import { rankPipeline, scoreDeal } from "@/lib/scoring/score";
import { shrinkRates } from "@/lib/scoring/stats";
import { auc } from "@/lib/scoring/backtest";

describe("auc", () => {
  it("vale 1 para separação perfeita, 0 para invertida e 0,5 para empate", () => {
    const perfect = [{ score: 0.9, won: true }, { score: 0.1, won: false }];
    expect(auc(perfect)).toBe(1);
    expect(auc(perfect.map((x) => ({ ...x, won: !x.won })))).toBe(0);
    expect(auc([{ score: 0.5, won: true }, { score: 0.5, won: false }])).toBe(0.5);
  });
});

let seq = 0;
function deal(overrides: Partial<Deal> = {}): Deal {
  seq += 1;
  return {
    id: `D${seq}`,
    stage: "Won",
    agent: "Ana",
    manager: "Bia",
    regionalOffice: "East",
    product: "GTX Pro",
    productSeries: "GTX",
    listPrice: 4821,
    account: "Acme",
    sector: "technology",
    accountEmployees: 2000,
    engageDate: "2017-01-01",
    closeDate: "2017-02-01",
    closeValue: 4800,
    ...overrides,
  };
}

/** Histórico sintético: ganhos fecham em 40 dias, perdas em 10, ciclo máximo 60. */
function syntheticHistory() {
  const deals: Deal[] = [];
  for (let i = 0; i < 120; i++) deals.push(deal({ stage: "Won", closeDate: "2017-02-10" }));
  for (let i = 0; i < 60; i++) deals.push(deal({ stage: "Lost", closeDate: "2017-01-11", closeValue: 0 }));
  deals.push(deal({ stage: "Won", closeDate: "2017-03-02" }));
  return buildHistory(deals);
}

describe("shrinkRates", () => {
  it("anula diferenças que cabem no ruído binomial", () => {
    const groups = new Map([
      ["a", { wins: 13, total: 20 }],
      ["b", { wins: 12, total: 20 }],
      ["c", { wins: 13, total: 20 }],
    ]);
    const shrunk = shrinkRates(groups, 0.63);
    for (const r of shrunk.values()) expect(r.shrunk).toBeCloseTo(0.63, 5);
  });

  it("preserva diferenças grandes com amostra grande", () => {
    const groups = new Map([
      ["bom", { wins: 900, total: 1000 }],
      ["ruim", { wins: 300, total: 1000 }],
    ]);
    const shrunk = shrinkRates(groups, 0.6);
    expect(shrunk.get("bom")!.shrunk).toBeGreaterThan(0.85);
    expect(shrunk.get("ruim")!.shrunk).toBeLessThan(0.35);
  });
});

describe("scoreDeal", () => {
  const history = syntheticHistory();

  it("deriva os limites de momento do histórico", () => {
    expect(history.maxCycle).toBe(60);
    expect(history.lostMedianCycle).toBe(10);
  });

  it("os fatores somam exatamente a chance de fechar", () => {
    const s = scoreDeal(deal({ stage: "Engaging", engageDate: "2017-01-01", closeDate: null }), history, "2017-01-21");
    const sum = history.baseRate * 100 + s.factors.reduce((acc, f) => acc + f.points, 0);
    expect(sum).toBeCloseTo(s.winProbability! * 100, 8);
  });

  it("deal que sobreviveu às perdas precoces ganha chance", () => {
    const s = scoreDeal(deal({ stage: "Engaging", closeDate: null }), history, "2017-01-21");
    expect(s.momentum).toBe("progressing");
    expect(s.winProbability!).toBeGreaterThan(history.baseRate);
  });

  it("deal aberto além do maior ciclo histórico fica parado e sem chance", () => {
    const s = scoreDeal(deal({ stage: "Engaging", closeDate: null }), history, "2017-06-01");
    expect(s.momentum).toBe("stalled");
    expect(s.winProbability).toBeNull();
    expect(s.nextAction).toMatch(/Revisar ou desqualificar/);
  });

  it("prospecção sem data usa a taxa geral e sinaliza conta faltando", () => {
    const s = scoreDeal(
      deal({ stage: "Prospecting", engageDate: null, closeDate: null, account: null, sector: null, accountEmployees: null }),
      history,
      "2017-01-21",
    );
    expect(s.momentum).toBe("prospecting");
    expect(s.factors.some((f) => f.key === "time")).toBe(false);
    expect(s.flags).toContain("Conta não informada no CRM");
  });
});

describe("rankPipeline", () => {
  it("ordena por valor esperado e deixa parados sem score no fim", () => {
    const history = syntheticHistory();
    const open = [
      deal({ id: "barato", stage: "Engaging", closeDate: null, product: "MG Special", listPrice: 55 }),
      deal({ id: "parado", stage: "Engaging", closeDate: null, engageDate: "2016-01-01", listPrice: 26768 }),
      deal({ id: "caro", stage: "Engaging", closeDate: null, listPrice: 26768 }),
    ];
    const ranked = rankPipeline([...open, deal()], history, "2017-01-21");
    expect(ranked.map((r) => r.deal.id)).toEqual(["caro", "barato", "parado"]);
    expect(ranked[0].score).toBeGreaterThan(ranked[1].score!);
    expect(ranked[2].score).toBeNull();
  });
});
