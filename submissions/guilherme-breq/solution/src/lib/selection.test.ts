import { describe, expect, it } from "vitest";
import type { AgentInfo, Deal } from "./data";
import { agentOptions, filterDeals, summarize, teamRows } from "./selection";

const agents: AgentInfo[] = [
  { name: "Ana", manager: "M1", region: "East", winRate: 0.6, closedDeals: 100 },
  { name: "Bia", manager: "M1", region: "East", winRate: 0.7, closedDeals: 100 },
  { name: "Caio", manager: "M2", region: "West", winRate: null, closedDeals: 0 },
];

function deal(p: Partial<Deal>): Deal {
  return {
    id: "x", agent: "Ana", product: "GTX Pro", account: "Acme", status: "ativo", ageDays: 50, daysLeft: 88,
    daysOverCycle: null, price: 1000, pDecide: 0.5, valuePts: 30, momentumPts: 20, score: 50, reasons: [],
    action: "", manager: "M1", region: "East", sector: null, ...p,
  };
}

const deals = [
  deal({ id: "a1", agent: "Ana", pDecide: 0.5, price: 1000 }),
  deal({ id: "a2", agent: "Ana", daysLeft: 10, pDecide: 1, price: 2000 }),
  deal({ id: "a3", agent: "Ana", status: "zumbi", price: 5000, pDecide: null, daysLeft: 0 }),
  deal({ id: "b1", agent: "Bia", status: "prospeccao", ageDays: null, daysLeft: null, pDecide: null }),
  deal({ id: "c1", agent: "Caio", manager: "M2", region: "West", price: 300 }),
];

describe("filterDeals", () => {
  it("filtra por região, manager e vendedor (vazio = todos)", () => {
    expect(filterDeals(deals, { region: "", manager: "", agent: "" })).toHaveLength(5);
    expect(filterDeals(deals, { region: "West", manager: "", agent: "" }).map((d) => d.id)).toEqual(["c1"]);
    expect(filterDeals(deals, { region: "", manager: "M1", agent: "Bia" }).map((d) => d.id)).toEqual(["b1"]);
  });
});

describe("agentOptions", () => {
  it("mostra só vendedores compatíveis com região e manager escolhidos", () => {
    expect(agentOptions(agents, { region: "East", manager: "", agent: "" }).map((a) => a.name)).toEqual(["Ana", "Bia"]);
    expect(agentOptions(agents, { region: "", manager: "M2", agent: "" }).map((a) => a.name)).toEqual(["Caio"]);
  });
});

describe("summarize", () => {
  it("conta vivos, janela fechando, zumbis e prospecção, e estima o que se decide em 30 dias", () => {
    const s = summarize(deals.filter((d) => d.agent === "Ana"));
    expect(s.live).toBe(2);
    expect(s.windowClosing).toBe(1);
    expect(s.zombies).toBe(1);
    expect(s.zombieValue).toBe(5000);
    expect(s.prospects).toBe(0);
    expect(s.decide30Count).toBeCloseTo(1.5);
    expect(s.decide30Value).toBeCloseTo(0.5 * 1000 + 1 * 2000);
    expect(s.zombieShare).toBeCloseTo(1 / 3);
  });
});

describe("teamRows", () => {
  it("agrega por vendedor e ordena pelo valor em decisão no mês", () => {
    const rows = teamRows(deals, agents);
    expect(rows.map((r) => r.name)).toEqual(["Ana", "Caio", "Bia"]);
    expect(rows[0].summary.zombies).toBe(1);
    expect(rows[0].topDeal?.id).toBe("a1");
  });
});
