import type { Deal } from "@/domain/types";
import { FACTOR_KEYS, factorValue, type FactorKey, type History } from "./history";
import { daysBetween, logit, sigmoid } from "./stats";

export type Momentum = "prospecting" | "early" | "progressing" | "closing" | "stalled";

export const MOMENTUM_LABEL: Record<Momentum, string> = {
  prospecting: "Prospecção",
  early: "Início",
  progressing: "Em andamento",
  closing: "Reta final",
  stalled: "Parado",
};

export interface Factor {
  key: "time" | FactorKey;
  label: string;
  /** Pontos percentuais somados à chance de fechar. */
  points: number;
  detail: string;
}

export interface ScoredDeal {
  deal: Deal;
  daysOpen: number | null;
  momentum: Momentum;
  /** Chance de fechar (0–1); null quando o deal está fora de qualquer precedente histórico. */
  winProbability: number | null;
  expectedValue: number;
  factors: Factor[];
  nextAction: string;
  flags: string[];
  /** Prioridade 0–100 (percentil do valor esperado no pipeline ativo); null para deals parados. */
  score: number | null;
}

const FACTOR_LABEL: Record<FactorKey, string> = {
  agent: "Vendedor",
  product: "Produto",
  sector: "Setor da conta",
  companySize: "Porte da conta",
};

const pct = (p: number) => `${Math.round(p * 100)}%`;

function momentumOf(daysOpen: number | null, history: History): Momentum {
  if (daysOpen === null) return "prospecting";
  if (daysOpen > history.maxCycle) return "stalled";
  if (daysOpen > history.wonP75Cycle) return "closing";
  if (daysOpen <= history.lostMedianCycle) return "early";
  return "progressing";
}

function nextActionFor(momentum: Momentum, daysOpen: number | null, history: History): string {
  switch (momentum) {
    case "prospecting":
      return "Agendar o primeiro contato";
    case "early":
      return `Qualificar já: metade das perdas acontece até o ${history.lostMedianCycle}º dia`;
    case "progressing":
      return "Avançar a proposta e confirmar o decisor";
    case "closing":
      return `Empurrar o fechamento: 75% dos ganhos fecham até o ${history.wonP75Cycle}º dia, e nenhum depois do ${history.maxCycle}º`;
    case "stalled":
      return `Revisar ou desqualificar: aberto há ${daysOpen} dias, e nenhum deal fechou depois de ${history.maxCycle}`;
  }
}

/**
 * Chance de fechar decomposta em fatores que somam exatamente.
 * Parte da taxa geral, aplica o tempo no pipeline (curva de sobrevivência) e
 * depois cada fator em log-odds, convertendo cada passo em pontos percentuais.
 */
function explainProbability(deal: Deal, daysOpen: number | null, history: History) {
  const factors: Factor[] = [];
  let current = history.baseRate;
  let logOdds = logit(current);

  if (daysOpen !== null) {
    const survived = history.survival[Math.min(daysOpen, history.survival.length - 1)];
    factors.push({
      key: "time",
      label: "Tempo no pipeline",
      points: (survived - current) * 100,
      detail: `Deals que passam de ${daysOpen} dias abertos fecham ${pct(survived)} das vezes`,
    });
    current = survived;
    logOdds = logit(survived);
  }

  for (const key of FACTOR_KEYS) {
    const value = factorValue(deal, key);
    const rate = value === null ? undefined : history.factors[key].get(value);
    if (value === null || rate === undefined) continue;
    const delta = logit(rate.shrunk) - logit(history.baseRate);
    const next = sigmoid(logOdds + delta);
    factors.push({
      key,
      label: `${FACTOR_LABEL[key]}: ${value}`,
      points: (next - current) * 100,
      detail: `Histórico de ${pct(rate.raw)} em ${rate.total} deals; após descontar o ruído estatístico, ${pct(rate.shrunk)}`,
    });
    logOdds += delta;
    current = next;
  }

  return { probability: current, factors };
}

export function scoreDeal(deal: Deal, history: History, referenceDate: string): Omit<ScoredDeal, "score"> {
  const daysOpen = deal.engageDate === null ? null : daysBetween(deal.engageDate, referenceDate);
  const momentum = momentumOf(daysOpen, history);
  const flags = deal.account === null ? ["Conta não informada no CRM"] : [];
  const nextAction = nextActionFor(momentum, daysOpen, history);

  if (momentum === "stalled") {
    return { deal, daysOpen, momentum, winProbability: null, expectedValue: 0, factors: [], nextAction, flags };
  }

  const { probability, factors } = explainProbability(deal, daysOpen, history);
  return {
    deal,
    daysOpen,
    momentum,
    winProbability: probability,
    expectedValue: probability * deal.listPrice,
    factors,
    nextAction,
    flags,
  };
}

/**
 * Pontua os deals abertos e ordena por valor esperado. O score 0–100 é o
 * percentil do valor esperado entre os deals ativos; parados ficam sem score
 * e vão para a fila de revisão.
 */
export function rankPipeline(deals: Deal[], history: History, referenceDate: string): ScoredDeal[] {
  const scored = deals
    .filter((d) => d.stage === "Prospecting" || d.stage === "Engaging")
    .map((d) => scoreDeal(d, history, referenceDate));

  const activeValues = scored
    .filter((s) => s.winProbability !== null)
    .map((s) => s.expectedValue)
    .sort((a, b) => a - b);

  const percentile = (value: number) => {
    let below = 0;
    while (below < activeValues.length && activeValues[below] < value) below++;
    let equal = below;
    while (equal < activeValues.length && activeValues[equal] === value) equal++;
    return Math.round(((below + (equal - below) / 2) / activeValues.length) * 100);
  };

  return scored
    .map((s) => ({ ...s, score: s.winProbability === null ? null : percentile(s.expectedValue) }))
    .sort((a, b) => b.expectedValue - a.expectedValue || b.deal.listPrice - a.deal.listPrice);
}
