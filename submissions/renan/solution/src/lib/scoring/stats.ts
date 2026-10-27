export const logit = (p: number): number => Math.log(p / (1 - p));
export const sigmoid = (x: number): number => 1 / (1 + Math.exp(-x));

export function daysBetween(fromIso: string, toIso: string): number {
  return Math.round((Date.parse(toIso) - Date.parse(fromIso)) / 86_400_000);
}

/** Quantil por "nearest rank" sobre um array já ordenado. */
export function quantile(sorted: number[], p: number): number {
  if (sorted.length === 0) throw new Error("quantile de array vazio");
  return sorted[Math.floor((sorted.length - 1) * p)];
}

export interface GroupCount {
  wins: number;
  total: number;
}

export interface ShrunkRate {
  /** Taxa observada, sem ajuste. */
  raw: number;
  /** Taxa após encolhimento em direção à média geral. */
  shrunk: number;
  total: number;
}

/**
 * Bayes empírico (método dos momentos) para taxas de vitória por grupo.
 *
 * Estima quanto da variação entre grupos é real (tau²) descontando o ruído
 * binomial esperado de cada grupo. Se a variação observada cabe no ruído,
 * tau² = 0 e todos os grupos voltam para a média: o fator deixa de pesar.
 * Assim o próprio dado decide o peso de cada fator, sem pesos inventados.
 */
export function shrinkRates(groups: Map<string, GroupCount>, baseRate: number): Map<string, ShrunkRate> {
  const entries = [...groups.entries()].filter(([, g]) => g.total > 0);
  const noise = (n: number) => (baseRate * (1 - baseRate)) / n;

  let tau2 = 0;
  if (entries.length > 1) {
    const observedVariance =
      entries.reduce((sum, [, g]) => sum + (g.wins / g.total - baseRate) ** 2, 0) / (entries.length - 1);
    const meanNoise = entries.reduce((sum, [, g]) => sum + noise(g.total), 0) / entries.length;
    tau2 = Math.max(0, observedVariance - meanNoise);
  }

  return new Map(
    entries.map(([key, g]) => {
      const raw = g.wins / g.total;
      const weight = tau2 / (tau2 + noise(g.total));
      return [key, { raw, shrunk: baseRate + weight * (raw - baseRate), total: g.total }];
    }),
  );
}
