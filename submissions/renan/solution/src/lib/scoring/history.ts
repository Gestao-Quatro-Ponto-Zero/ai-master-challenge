import type { Deal } from "@/domain/types";
import { daysBetween, quantile, shrinkRates, type GroupCount, type ShrunkRate } from "./stats";

export type FactorKey = "agent" | "product" | "sector" | "companySize";

export const FACTOR_KEYS: readonly FactorKey[] = ["agent", "product", "sector", "companySize"];

/** Faixas de porte da conta por número de funcionários. */
export function companySizeBand(employees: number | null): string | null {
  if (employees === null) return null;
  if (employees < 1_000) return "até 1 mil funcionários";
  if (employees < 5_000) return "1–5 mil funcionários";
  return "5 mil+ funcionários";
}

export function factorValue(deal: Deal, key: FactorKey): string | null {
  switch (key) {
    case "agent":
      return deal.agent;
    case "product":
      return deal.product;
    case "sector":
      return deal.sector;
    case "companySize":
      return companySizeBand(deal.accountEmployees);
  }
}

/** Menor amostra aceita para um ponto da curva de sobrevivência. */
const MIN_SURVIVAL_SAMPLE = 50;

export interface History {
  closedDeals: number;
  baseRate: number;
  /** survival[t] = P(vitória | deal ainda aberto após t dias). */
  survival: number[];
  /** Maior ciclo (engajamento → fechamento) já observado. */
  maxCycle: number;
  /** Mediana do ciclo dos deals perdidos: as perdas acontecem cedo. */
  lostMedianCycle: number;
  /** Percentil 75 do ciclo dos deals ganhos: a partir daqui, reta final. */
  wonP75Cycle: number;
  wonMedianCycle: number;
  factors: Record<FactorKey, Map<string, ShrunkRate>>;
}

/** Estatísticas históricas, calculadas só com deals já fechados. */
export function buildHistory(deals: Deal[]): History {
  const closed = deals.filter(
    (d) => (d.stage === "Won" || d.stage === "Lost") && d.engageDate !== null && d.closeDate !== null,
  );
  if (closed.length === 0) throw new Error("buildHistory: nenhum deal fechado para aprender");

  const wins = closed.filter((d) => d.stage === "Won").length;
  const baseRate = wins / closed.length;

  const cycles = closed.map((d) => ({ won: d.stage === "Won", days: daysBetween(d.engageDate!, d.closeDate!) }));
  const wonCycles = cycles.filter((c) => c.won).map((c) => c.days).sort((a, b) => a - b);
  const lostCycles = cycles.filter((c) => !c.won).map((c) => c.days).sort((a, b) => a - b);
  const maxCycle = Math.max(...cycles.map((c) => c.days));

  const survival: number[] = [];
  for (let t = 0; t <= maxCycle; t++) {
    const stillOpen = cycles.filter((c) => c.days > t);
    if (stillOpen.length < MIN_SURVIVAL_SAMPLE) {
      survival.push(survival.at(-1) ?? baseRate);
    } else {
      survival.push(stillOpen.filter((c) => c.won).length / stillOpen.length);
    }
  }

  const factors = Object.fromEntries(
    FACTOR_KEYS.map((key) => {
      const groups = new Map<string, GroupCount>();
      for (const deal of closed) {
        const value = factorValue(deal, key);
        if (value === null) continue;
        const g = groups.get(value) ?? { wins: 0, total: 0 };
        g.total += 1;
        if (deal.stage === "Won") g.wins += 1;
        groups.set(value, g);
      }
      return [key, shrinkRates(groups, baseRate)];
    }),
  ) as Record<FactorKey, Map<string, ShrunkRate>>;

  return {
    closedDeals: closed.length,
    baseRate,
    survival,
    maxCycle,
    lostMedianCycle: quantile(lostCycles, 0.5),
    wonP75Cycle: quantile(wonCycles, 0.75),
    wonMedianCycle: quantile(wonCycles, 0.5),
    factors,
  };
}
