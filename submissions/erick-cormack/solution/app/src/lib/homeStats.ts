import type { Deal } from "@/hooks/useDeals";

export type ResumoExecutivo = {
  abertos: number;
  valorPipeline: number;
  focar: number;
  valorEsperadoFoco: number;
  requalificar: number;
  valorParado: number;
  pctParado: number;
  semConta: number;
};

export function calcResumo(deals: Deal[]): ResumoExecutivo {
  const r: ResumoExecutivo = {
    abertos: deals.length,
    valorPipeline: 0,
    focar: 0,
    valorEsperadoFoco: 0,
    requalificar: 0,
    valorParado: 0,
    pctParado: 0,
    semConta: 0,
  };
  for (const d of deals) {
    r.valorPipeline += d.sales_price ?? 0;
    if (d.sem_conta) r.semConta++;
    if (d.fila === "focar") {
      r.focar++;
      r.valorEsperadoFoco += d.valor_esperado ?? 0;
    } else if (d.fila === "requalificar") {
      r.requalificar++;
      r.valorParado += d.sales_price ?? 0;
    }
  }
  r.pctParado = r.abertos === 0 ? 0 : r.requalificar / r.abertos;
  return r;
}

export type TotalPorFila = { fila: string; label: string; total: number };

const ORDEM_FILAS: { fila: string; label: string }[] = [
  { fila: "focar", label: "Focar agora" },
  { fila: "prospectar", label: "Prospectar" },
  { fila: "requalificar", label: "Requalificar ou encerrar" },
];

export function dealsPorFila(deals: Deal[]): TotalPorFila[] {
  return ORDEM_FILAS.map(({ fila, label }) => ({
    fila,
    label,
    total: deals.filter((d) => d.fila === fila).length,
  }));
}

export type ValorPorRegiao = { regiao: string; valor: number; deals: number };

/** Valor esperado em foco por região, ordenado do maior para o menor. */
export function valorFocoPorRegiao(deals: Deal[]): ValorPorRegiao[] {
  const mapa = new Map<string, ValorPorRegiao>();
  for (const d of deals) {
    if (d.fila !== "focar") continue;
    const regiao = d.regional_office ?? "Sem região";
    const item = mapa.get(regiao) ?? { regiao, valor: 0, deals: 0 };
    item.valor += d.valor_esperado ?? 0;
    item.deals++;
    mapa.set(regiao, item);
  }
  return [...mapa.values()].sort((a, b) => b.valor - a.valor);
}

export type ValorPorManager = { manager: string; valor: number; deals: number };

/** Valor esperado em foco por manager, ordenado do maior para o menor. */
export function valorFocoPorManager(deals: Deal[]): ValorPorManager[] {
  const mapa = new Map<string, ValorPorManager>();
  for (const d of deals) {
    if (d.fila !== "focar") continue;
    const manager = d.manager ?? "Sem manager";
    const item = mapa.get(manager) ?? { manager, valor: 0, deals: 0 };
    item.valor += d.valor_esperado ?? 0;
    item.deals++;
    mapa.set(manager, item);
  }
  return [...mapa.values()].sort((a, b) => b.valor - a.valor);
}

export type FaixaScore = { faixa: string; total: number };

/** Distribuição do score (0–100) dos deals em foco, em faixas de 10. */
export function distScoreFoco(deals: Deal[]): FaixaScore[] {
  const faixas: FaixaScore[] = Array.from({ length: 10 }, (_, i) => ({
    faixa: `${i * 10}–${i * 10 + 9}`,
    total: 0,
  }));
  for (const d of deals) {
    if (d.fila !== "focar" || d.score == null) continue;
    const i = Math.min(9, Math.max(0, Math.floor(d.score / 10)));
    faixas[i]!.total++;
  }
  return faixas;
}
