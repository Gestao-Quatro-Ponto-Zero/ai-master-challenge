/**
 * scoring.test.ts — Unit tests for the Lead Scorer scoring engine
 *
 * Tests all 4 scoring components via scoreDeals(), plus scoreColor/scoreLabel.
 * Uses vitest. Run with: npm test
 */

import { describe, it, expect } from "vitest";
import { scoreDeals, scoreColor, scoreLabel, type ScoredDeal } from "./scoring";
import { type Deal } from "./data";

// ─── Helpers ─────────────────────────────────────────────────────────────────

function makeDeal(overrides: Partial<Deal> = {}): Deal {
  return {
    opportunity_id: "TEST-001",
    sales_agent: "agent_x",
    manager: "Manager A",
    regional_office: "São Paulo",
    product: "GTX Basic",
    product_price: 550,
    account: "Acme Corp",
    account_sector: "Technology",
    account_country: "Brazil",
    account_revenue: 50, // SMB by default
    account_employees: 100,
    account_has_parent: false,
    deal_stage: "Engaging",
    engage_date: null,
    close_date: null,
    close_value: 0,
    days_in_stage: 15,
    ...overrides,
  };
}

const noWinRates = new Map<string, { winRate: number; won: number; lost: number }>();

function score(deal: Deal, winRates = noWinRates): ScoredDeal {
  return scoreDeals([deal], winRates)[0];
}

function component(deal: ScoredDeal, label: string) {
  return deal.components.find((c) => c.label === label)!;
}

// ─── A. Stage + Momentum (30 pts) ────────────────────────────────────────────

describe("A. Stage + Momentum", () => {
  it("Engaging ≤30d → 30pts (deal quente)", () => {
    const deal = score(makeDeal({ deal_stage: "Engaging", days_in_stage: 15 }));
    expect(component(deal, "Stage + Momentum").pts).toBe(30);
  });

  it("Engaging at exactly 30d → 30pts (boundary)", () => {
    const deal = score(makeDeal({ deal_stage: "Engaging", days_in_stage: 30 }));
    expect(component(deal, "Stage + Momentum").pts).toBe(30);
  });

  it("Engaging 31–60d → 22pts (esfriando)", () => {
    const deal = score(makeDeal({ deal_stage: "Engaging", days_in_stage: 45 }));
    expect(component(deal, "Stage + Momentum").pts).toBe(22);
  });

  it("Engaging at exactly 60d → 22pts (boundary)", () => {
    const deal = score(makeDeal({ deal_stage: "Engaging", days_in_stage: 60 }));
    expect(component(deal, "Stage + Momentum").pts).toBe(22);
  });

  it("Engaging 61–90d → 12pts (ciclo longo)", () => {
    const deal = score(makeDeal({ deal_stage: "Engaging", days_in_stage: 75 }));
    expect(component(deal, "Stage + Momentum").pts).toBe(12);
  });

  it("Engaging at exactly 90d → 12pts (boundary)", () => {
    const deal = score(makeDeal({ deal_stage: "Engaging", days_in_stage: 90 }));
    expect(component(deal, "Stage + Momentum").pts).toBe(12);
  });

  it("Engaging +90d → 4pts (ZUMBI)", () => {
    const deal = score(makeDeal({ deal_stage: "Engaging", days_in_stage: 180 }));
    expect(component(deal, "Stage + Momentum").pts).toBe(4);
  });

  it("Prospecting with account → 10pts", () => {
    const deal = score(makeDeal({ deal_stage: "Prospecting", account: "Some Corp", days_in_stage: 10 }));
    expect(component(deal, "Stage + Momentum").pts).toBe(10);
  });

  it("Prospecting without account → 2pts", () => {
    const deal = score(makeDeal({ deal_stage: "Prospecting", account: "", days_in_stage: 10 }));
    expect(component(deal, "Stage + Momentum").pts).toBe(2);
  });

  it("Stage + Momentum max is 30pts", () => {
    const c = score(makeDeal({ deal_stage: "Engaging", days_in_stage: 1 }));
    expect(component(c, "Stage + Momentum").maxPts).toBe(30);
  });
});

// ─── B. Product / Ticket (25 pts) ────────────────────────────────────────────

describe("B. Produto / Ticket", () => {
  const cases: [string, number][] = [
    ["GTK 500", 25],
    ["GTX Plus Pro", 22],
    ["GTX Pro", 20],
    ["GTXPro", 20], // pipeline typo variant
    ["MG Advanced", 16],
    ["GTX Plus Basic", 12],
    ["GTX Basic", 8],
    ["MG Special", 3],
  ];

  for (const [product, expectedPts] of cases) {
    it(`${product} → ${expectedPts}pts`, () => {
      const deal = score(makeDeal({ product }));
      expect(component(deal, "Produto / Ticket").pts).toBe(expectedPts);
    });
  }

  it("Unknown product defaults to 8pts (GTX Basic tier)", () => {
    const deal = score(makeDeal({ product: "PRODUTO DESCONHECIDO" }));
    expect(component(deal, "Produto / Ticket").pts).toBe(8);
  });

  it("Produto / Ticket maxPts is 25", () => {
    const deal = score(makeDeal({ product: "GTK 500" }));
    expect(component(deal, "Produto / Ticket").maxPts).toBe(25);
  });
});

// ─── C. Account Quality (25 pts) ─────────────────────────────────────────────

describe("C. Qualidade da Conta", () => {
  it("No account → 0pts (penalidade máxima)", () => {
    const deal = score(makeDeal({ account: "" }));
    expect(component(deal, "Qualidade da Conta").pts).toBe(0);
  });

  it("Enterprise (rev > 2000M) → 25pts", () => {
    const deal = score(makeDeal({ account: "BigCorp", account_revenue: 5000 }));
    expect(component(deal, "Qualidade da Conta").pts).toBe(25);
  });

  it("Large (rev 500–2000M) → 18pts", () => {
    const deal = score(makeDeal({ account: "MedCorp", account_revenue: 1000 }));
    expect(component(deal, "Qualidade da Conta").pts).toBe(18);
  });

  it("Mid-market (rev 100–500M) → 11pts", () => {
    const deal = score(makeDeal({ account: "MidCorp", account_revenue: 250 }));
    expect(component(deal, "Qualidade da Conta").pts).toBe(11);
  });

  it("SMB (rev < 100M) → 6pts", () => {
    const deal = score(makeDeal({ account: "SmallCo", account_revenue: 30 }));
    expect(component(deal, "Qualidade da Conta").pts).toBe(6);
  });

  it("Subsidiary bonus +3pts for Mid-market (11 + 3 = 14)", () => {
    const deal = score(makeDeal({ account: "SubMid", account_revenue: 250, account_has_parent: true }));
    expect(component(deal, "Qualidade da Conta").pts).toBe(14);
  });

  it("Subsidiary bonus is capped at 25 for Enterprise (25 + 3 = 25, not 28)", () => {
    const deal = score(makeDeal({ account: "SubEnterprise", account_revenue: 5000, account_has_parent: true }));
    expect(component(deal, "Qualidade da Conta").pts).toBe(25);
  });

  it("Revenue boundary: exactly 2000M → Large (not Enterprise)", () => {
    const deal = score(makeDeal({ account: "BoundCorp", account_revenue: 2000 }));
    expect(component(deal, "Qualidade da Conta").pts).toBe(18);
  });

  it("Revenue boundary: exactly 500M → Mid-market (not Large)", () => {
    const deal = score(makeDeal({ account: "BoundMid", account_revenue: 500 }));
    expect(component(deal, "Qualidade da Conta").pts).toBe(11);
  });

  it("Revenue boundary: exactly 100M → SMB (not Mid-market)", () => {
    const deal = score(makeDeal({ account: "BoundSmall", account_revenue: 100 }));
    expect(component(deal, "Qualidade da Conta").pts).toBe(6);
  });

  it("Qualidade da Conta maxPts is 25", () => {
    const deal = score(makeDeal({ account: "Acme", account_revenue: 5000 }));
    expect(component(deal, "Qualidade da Conta").maxPts).toBe(25);
  });
});

// ─── D. Agent Win Rate (20 pts) ───────────────────────────────────────────────

describe("D. Win Rate do Vendedor", () => {
  function winRateMap(agent: string, won: number, lost: number) {
    const total = won + lost;
    const winRate = total > 0 ? won / total : 0;
    return new Map([[agent.toLowerCase(), { winRate, won, lost }]]);
  }

  it("No history → 10pts (default neutro)", () => {
    const deal = score(makeDeal({ sales_agent: "agent_unknown" }), noWinRates);
    expect(component(deal, "Win Rate do Vendedor").pts).toBe(10);
  });

  it("Win rate > 70% → 20pts (excelente)", () => {
    const wr = winRateMap("agent_x", 8, 2); // 80%
    const deal = score(makeDeal({ sales_agent: "agent_x" }), wr);
    expect(component(deal, "Win Rate do Vendedor").pts).toBe(20);
  });

  it("Win rate exactly 70% → 15pts (not above 70%)", () => {
    const wr = winRateMap("agent_x", 7, 3); // 70%
    const deal = score(makeDeal({ sales_agent: "agent_x" }), wr);
    expect(component(deal, "Win Rate do Vendedor").pts).toBe(15);
  });

  it("Win rate 50–70% → 15pts (acima da média)", () => {
    const wr = winRateMap("agent_x", 6, 4); // 60%
    const deal = score(makeDeal({ sales_agent: "agent_x" }), wr);
    expect(component(deal, "Win Rate do Vendedor").pts).toBe(15);
  });

  it("Win rate 30–50% → 10pts (na média)", () => {
    const wr = winRateMap("agent_x", 4, 6); // 40%
    const deal = score(makeDeal({ sales_agent: "agent_x" }), wr);
    expect(component(deal, "Win Rate do Vendedor").pts).toBe(10);
  });

  it("Win rate ≤ 30% → 5pts (abaixo da média)", () => {
    const wr = winRateMap("agent_x", 2, 8); // 20%
    const deal = score(makeDeal({ sales_agent: "agent_x" }), wr);
    expect(component(deal, "Win Rate do Vendedor").pts).toBe(5);
  });

  it("Agent name lookup is case-insensitive", () => {
    const wr = winRateMap("Agent_X", 9, 1); // 90% — stored as "agent_x"
    const deal = score(makeDeal({ sales_agent: "AGENT_X" }), wr);
    expect(component(deal, "Win Rate do Vendedor").pts).toBe(20);
  });

  it("Win Rate maxPts is 20", () => {
    const deal = score(makeDeal());
    expect(component(deal, "Win Rate do Vendedor").maxPts).toBe(20);
  });
});

// ─── scoreDeals — combined score ──────────────────────────────────────────────

describe("scoreDeals — combined score", () => {
  it("Maximum possible score = 100 (Engaging ≤30d + GTK 500 + Enterprise + win rate >70%)", () => {
    const wr = new Map([["top_agent", { winRate: 0.9, won: 9, lost: 1 }]]);
    const deal = score(
      makeDeal({
        sales_agent: "top_agent",
        deal_stage: "Engaging",
        days_in_stage: 10,
        product: "GTK 500",
        account: "MegaCorp",
        account_revenue: 10000,
        account_has_parent: false,
      }),
      wr
    );
    expect(deal.score).toBe(100); // 30 + 25 + 25 + 20
  });

  it("Minimum non-zero score (zombie + MG Special + no account + below avg agent)", () => {
    const wr = new Map([["bad_agent", { winRate: 0.1, won: 1, lost: 9 }]]);
    const deal = score(
      makeDeal({
        sales_agent: "bad_agent",
        deal_stage: "Engaging",
        days_in_stage: 200,
        product: "MG Special",
        account: "",
      }),
      wr
    );
    expect(deal.score).toBe(4 + 3 + 0 + 5); // 12
  });

  it("Returns exactly 4 components", () => {
    const deal = score(makeDeal());
    expect(deal.components).toHaveLength(4);
  });

  it("score equals sum of component pts", () => {
    const deal = score(makeDeal());
    const sum = deal.components.reduce((acc, c) => acc + c.pts, 0);
    expect(deal.score).toBe(sum);
  });

  it("Processes multiple deals independently", () => {
    const wr = new Map([["good_agent", { winRate: 0.8, won: 8, lost: 2 }]]);
    const deals = scoreDeals(
      [
        makeDeal({ opportunity_id: "D1", deal_stage: "Engaging", days_in_stage: 10 }),
        makeDeal({ opportunity_id: "D2", deal_stage: "Engaging", days_in_stage: 200 }),
      ],
      wr
    );
    expect(deals[0].score).toBeGreaterThan(deals[1].score);
  });
});

// ─── scoreColor ───────────────────────────────────────────────────────────────

describe("scoreColor", () => {
  it("≥70 → green", () => expect(scoreColor(70)).toBe("green"));
  it("100 → green", () => expect(scoreColor(100)).toBe("green"));
  it("69 → yellow", () => expect(scoreColor(69)).toBe("yellow"));
  it("40 → yellow", () => expect(scoreColor(40)).toBe("yellow"));
  it("39 → red", () => expect(scoreColor(39)).toBe("red"));
  it("0 → red", () => expect(scoreColor(0)).toBe("red"));
});

// ─── scoreLabel ───────────────────────────────────────────────────────────────

describe("scoreLabel", () => {
  it("≥70 → 'Alta prioridade'", () => expect(scoreLabel(70)).toBe("Alta prioridade"));
  it("40–69 → 'Média prioridade'", () => expect(scoreLabel(55)).toBe("Média prioridade"));
  it("<40 → 'Baixa prioridade'", () => expect(scoreLabel(39)).toBe("Baixa prioridade"));
  it("0 → 'Baixa prioridade'", () => expect(scoreLabel(0)).toBe("Baixa prioridade"));
});
