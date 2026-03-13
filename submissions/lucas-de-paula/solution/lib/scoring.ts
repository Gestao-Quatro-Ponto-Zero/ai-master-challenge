/**
 * scoring.ts — Lead score calculation (0–100 pts)
 *
 * Four components calibrated against the real dataset (2016-2017 B2B pipeline):
 *
 * A. Stage + Momentum   30 pts  ← most important for daily prioritization
 * B. Product / Ticket   25 pts  ← GTK 500 = 486x MG Special; huge spread
 * C. Account Quality    25 pts  ← penalizes deals with no account identified
 * D. Agent Win Rate     20 pts  ← real historical data, not a rule of thumb
 *
 * Key insight: "zombie" Engaging deals (>180 days) score near-zero in
 * component A, surfacing them as low-priority without hiding them entirely.
 */

import { type Deal } from "./data";

// ─── Score breakdown (one entry per component) ────────────────────────────────

export interface ScoreComponent {
  label: string;       // Short name, e.g. "Stage + Momentum"
  maxPts: number;      // Weight in the total score
  pts: number;         // Points earned
  detail: string;      // Human-readable explanation for the UI
}

export interface ScoredDeal extends Deal {
  score: number;
  components: ScoreComponent[];
}

// ─── A. Stage + Momentum (30 pts) ────────────────────────────────────────────

function scoreStage(deal: Deal): ScoreComponent {
  const days = deal.days_in_stage;
  const hasAccount = !!deal.account;
  let pts = 0;
  let detail = "";

  if (deal.deal_stage === "Engaging") {
    if (days <= 30) {
      pts = 30;
      detail = `Engaging há ${days} dias — deal quente ✅ (≤30d = pontuação máxima)`;
    } else if (days <= 60) {
      pts = 22;
      detail = `Engaging há ${days} dias — esfriando ⚠️ (31–60d = 22pts; contato urgente)`;
    } else if (days <= 90) {
      pts = 12;
      detail = `Engaging há ${days} dias — ciclo longo 🔶 (61–90d = 12pts; risco aumentado)`;
    } else {
      pts = 4;
      detail = `Engaging há ${days} dias — deal ZUMBI 💀 (+90d = 4pts; revisar ou encerrar)`;
    }
  } else if (deal.deal_stage === "Prospecting") {
    if (hasAccount) {
      pts = 10;
      detail = `Prospecting com conta identificada (10pts — avanço esperado para Engaging)`;
    } else {
      pts = 2;
      detail = `Prospecting sem conta identificada (2pts — qualifique a conta antes de avançar)`;
    }
  }

  return {
    label: "Stage + Momentum",
    maxPts: 30,
    pts,
    detail,
  };
}

// ─── B. Product / Ticket (25 pts) ────────────────────────────────────────────
// Fixed mapping derived from products.csv prices.
// GTK 500 ($26,768) is 486× MG Special ($55) — weighting this heavily
// is correct: one GTK deal = hundreds of MG deals in revenue impact.

const PRODUCT_SCORES: Record<string, number> = {
  "GTK 500": 25,
  "GTX Plus Pro": 22,
  "GTX Pro": 20,
  GTXPro: 20, // pipeline typo variant
  "MG Advanced": 16,
  "GTX Plus Basic": 12,
  "GTX Basic": 8,
  "MG Special": 3,
};

function scoreProduct(deal: Deal): ScoreComponent {
  const pts = PRODUCT_SCORES[deal.product] ?? 8; // default: GTX Basic tier
  const price = deal.product_price
    ? `$${deal.product_price.toLocaleString()}`
    : "preço desconhecido";

  // Product tier label for context
  const tierLabel =
    pts === 25 ? "produto premium (topo de linha)" :
    pts === 22 ? "2º produto mais caro" :
    pts === 20 ? "3º produto — ticket alto" :
    pts === 16 ? "ticket médio-alto" :
    pts === 12 ? "ticket médio" :
    pts === 8  ? "ticket básico" : "ticket de entrada";

  return {
    label: "Produto / Ticket",
    maxPts: 25,
    pts,
    detail: `${deal.product} (${price}) — ${tierLabel} → ${pts}/25pts`,
  };
}

// ─── C. Account Quality (25 pts) ─────────────────────────────────────────────
// Revenue in millions USD. Breakdown:
// >2000M = enterprise  → 25
// 500-2000M = large    → 18
// 100-500M = mid-market → 11
// <100M = SMB          → 6
// No account           → 0 (penalidade total)
// +3 bonus: has a parent company (subsidiary_of) → signal of larger group

function scoreAccount(deal: Deal): ScoreComponent {
  if (!deal.account) {
    return {
      label: "Qualidade da Conta",
      maxPts: 25,
      pts: 0,
      detail: "Sem conta identificada — penalidade máxima",
    };
  }

  const rev = deal.account_revenue;
  let pts = 0;
  let tier = "";

  if (rev > 2000) {
    pts = 25;
    tier = "Enterprise";
  } else if (rev > 500) {
    pts = 18;
    tier = "Large";
  } else if (rev > 100) {
    pts = 11;
    tier = "Mid-market";
  } else {
    pts = 6;
    tier = "SMB";
  }

  const bonus = deal.account_has_parent ? 3 : 0;
  const totalPts = Math.min(25, pts + bonus);
  const bonusNote = bonus > 0 ? " +3 (subsidiária)" : "";

  return {
    label: "Qualidade da Conta",
    maxPts: 25,
    pts: totalPts,
    detail: `${deal.account} — ${tier} ($${rev.toFixed(0)}M rev${bonusNote})`,
  };
}

// ─── D. Agent Win Rate (20 pts) ───────────────────────────────────────────────
// Win rate calculated from historical Won/Lost deals in sales_pipeline.csv.
// Passed in as a precomputed map to avoid re-reading the file per deal.

function scoreAgent(
  deal: Deal,
  winRates: Map<string, { winRate: number; won: number; lost: number }>
): ScoreComponent {
  const key = deal.sales_agent.toLowerCase();
  const stats = winRates.get(key);

  if (!stats || stats.won + stats.lost === 0) {
    return {
      label: "Win Rate do Vendedor",
      maxPts: 20,
      pts: 10,
      detail: `${deal.sales_agent} — sem histórico suficiente`,
    };
  }

  const wr = stats.winRate;
  let pts = 0;
  if (wr > 0.7) pts = 20;
  else if (wr > 0.5) pts = 15;
  else if (wr > 0.3) pts = 10;
  else pts = 5;

  const pct = (wr * 100).toFixed(0);
  const tierLabel =
    pts === 20 ? "excelente" :
    pts === 15 ? "acima da média" :
    pts === 10 ? "na média" : "abaixo da média";
  return {
    label: "Win Rate do Vendedor",
    maxPts: 20,
    pts,
    detail: `${deal.sales_agent} — ${pct}% de win rate (${stats.won} vitórias / ${stats.lost} derrotas) — ${tierLabel}`,
  };
}

// ─── Main scoring function ────────────────────────────────────────────────────

export function scoreDeals(
  deals: Deal[],
  winRates: Map<string, { winRate: number; won: number; lost: number }>
): ScoredDeal[] {
  return deals.map((deal) => {
    const components: ScoreComponent[] = [
      scoreStage(deal),
      scoreProduct(deal),
      scoreAccount(deal),
      scoreAgent(deal, winRates),
    ];

    const score = components.reduce((sum, c) => sum + c.pts, 0);

    return { ...deal, score, components };
  });
}

// ─── Score badge color ────────────────────────────────────────────────────────

export function scoreColor(score: number): "green" | "yellow" | "red" {
  if (score >= 70) return "green";
  if (score >= 40) return "yellow";
  return "red";
}

export function scoreLabel(score: number): string {
  if (score >= 70) return "Alta prioridade";
  if (score >= 40) return "Média prioridade";
  return "Baixa prioridade";
}
