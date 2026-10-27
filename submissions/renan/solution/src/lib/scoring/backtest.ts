import type { Deal } from "@/domain/types";
import { buildHistory, factorValue, type History } from "./history";
import { scoreDeal } from "./score";

/** Área sob a curva ROC: chance de um ganho aleatório ter nota maior que uma perda aleatória. */
export function auc(items: { score: number; won: boolean }[]): number {
  const sorted = [...items].sort((a, b) => a.score - b.score);
  let rankSumWins = 0;
  let wins = 0;
  for (let i = 0; i < sorted.length; ) {
    let j = i;
    while (j < sorted.length && sorted[j].score === sorted[i].score) j++;
    const avgRank = (i + j + 1) / 2;
    for (let k = i; k < j; k++) {
      if (sorted[k].won) {
        rankSumWins += avgRank;
        wins++;
      }
    }
    i = j;
  }
  const losses = sorted.length - wins;
  if (wins === 0 || losses === 0) return 0.5;
  return (rankSumWins - (wins * (wins + 1)) / 2) / (wins * losses);
}

export interface StrategyResult {
  name: string;
  auc: number | null;
  /** Receita realizada pelos 20% do pipeline que a estratégia mandaria atacar primeiro. */
  top20Revenue: number;
  top20Share: number;
}

export interface BacktestResult {
  cutoff: string;
  trainedOn: number;
  evaluated: number;
  evaluatedWinRate: number;
  strategies: StrategyResult[];
  stalled: { count: number; winRate: number | null };
}

interface Candidate {
  deal: Deal;
  won: boolean;
  revenue: number;
  probability: number | null;
  timeOnly: number | null;
  rawAgent: number;
  expectedValue: number;
}

/**
 * Simula a ferramenta numa data passada: aprende só com o que tinha fechado
 * até o corte e avalia os deals que estavam abertos naquele dia e fecharam
 * depois, cujo resultado hoje é conhecido.
 */
export function backtest(deals: Deal[], cutoff: string): BacktestResult {
  const known = deals.filter((d) => d.closeDate !== null && d.engageDate !== null);
  const history = buildHistory(known.filter((d) => d.closeDate! <= cutoff));
  const openAtCutoff = known.filter((d) => d.engageDate! <= cutoff && d.closeDate! > cutoff);

  const candidates: Candidate[] = openAtCutoff.map((deal) => {
    const asOpen: Deal = { ...deal, stage: "Engaging", closeDate: null, closeValue: null };
    const scored = scoreDeal(asOpen, history, cutoff);
    const timeOnly =
      scored.daysOpen === null || scored.winProbability === null
        ? null
        : history.survival[Math.min(scored.daysOpen, history.survival.length - 1)];
    return {
      deal,
      won: deal.stage === "Won",
      revenue: deal.closeValue ?? 0,
      probability: scored.winProbability,
      timeOnly,
      rawAgent: rawRate(history, deal),
      expectedValue: scored.expectedValue,
    };
  });

  const active = candidates.filter((c) => c.probability !== null);
  const stalled = candidates.filter((c) => c.probability === null);
  const totalRevenue = candidates.reduce((s, c) => s + c.revenue, 0);

  const top20 = (rank: (c: Candidate) => number) => {
    const n = Math.round(candidates.length * 0.2);
    const revenue = [...candidates]
      .sort((a, b) => rank(b) - rank(a))
      .slice(0, n)
      .reduce((s, c) => s + c.revenue, 0);
    return { top20Revenue: revenue, top20Share: totalRevenue === 0 ? 0 : revenue / totalRevenue };
  };
  const aucOf = (pick: (c: Candidate) => number | null) =>
    auc(active.map((c) => ({ score: pick(c) ?? 0, won: c.won })));

  // Ordem neutra: deal id embaralha sem viés, de forma reproduzível.
  const neutral = (c: Candidate) => hash(c.deal.id);

  const strategies: StrategyResult[] = [
    { name: "Score (valor esperado)", auc: aucOf((c) => c.probability), ...top20((c) => c.expectedValue) },
    { name: "Ordenar por preço do produto", auc: null, ...top20((c) => c.deal.listPrice) },
    { name: "Só tempo no pipeline", auc: aucOf((c) => c.timeOnly), ...top20((c) => c.timeOnly ?? 0) },
    { name: "Taxa bruta do vendedor", auc: aucOf((c) => c.rawAgent), ...top20((c) => c.rawAgent) },
    { name: "Ordem aleatória", auc: aucOf(neutral), ...top20(neutral) },
  ];

  return {
    cutoff,
    trainedOn: history.closedDeals,
    evaluated: candidates.length,
    evaluatedWinRate: candidates.filter((c) => c.won).length / candidates.length,
    strategies,
    stalled: {
      count: stalled.length,
      winRate: stalled.length === 0 ? null : stalled.filter((c) => c.won).length / stalled.length,
    },
  };
}

function rawRate(history: History, deal: Deal): number {
  const value = factorValue(deal, "agent");
  return (value === null ? undefined : history.factors.agent.get(value)?.raw) ?? history.baseRate;
}

function hash(text: string): number {
  let h = 2166136261;
  for (let i = 0; i < text.length; i++) h = Math.imul(h ^ text.charCodeAt(i), 16777619);
  return (h >>> 0) / 2 ** 32;
}
