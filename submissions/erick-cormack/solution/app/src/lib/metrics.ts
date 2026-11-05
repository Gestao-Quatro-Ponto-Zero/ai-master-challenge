import type { Deal } from "@/hooks/useDeals";

export type Indicadores = {
  focar: number;
  valorEsperadoFocar: number;
  retaFinal: number;
  requalificar: number;
  valorParado: number;
  prospectar: number;
  semConta: number;
};

export function calcIndicadores(deals: Deal[]): Indicadores {
  const r: Indicadores = {
    focar: 0, valorEsperadoFocar: 0, retaFinal: 0, requalificar: 0, valorParado: 0, prospectar: 0, semConta: 0,
  };
  for (const d of deals) {
    if (d.sem_conta) r.semConta++;
    if (d.fila === "focar") {
      r.focar++;
      r.valorEsperadoFocar += d.valor_esperado ?? 0;
      if (d.momento === "reta final") r.retaFinal++;
    } else if (d.fila === "requalificar") {
      r.requalificar++;
      r.valorParado += d.sales_price ?? 0;
    } else if (d.fila === "prospectar") r.prospectar++;
  }
  return r;
}

export function sortFocar(a: Deal, b: Deal) {
  return (b.score ?? 0) - (a.score ?? 0) || (a.dias_ate_limite ?? 999) - (b.dias_ate_limite ?? 999);
}
export function sortRequalificar(a: Deal, b: Deal) {
  return (b.sales_price ?? 0) - (a.sales_price ?? 0);
}
export function sortProspectar(a: Deal, b: Deal) {
  return (b.score ?? 0) - (a.score ?? 0);
}

/** requalificar ÷ (focar + requalificar + prospectar) */
export function pctParado(focar: number, requalificar: number, prospectar: number): number {
  const total = focar + requalificar + prospectar;
  return total === 0 ? 0 : requalificar / total;
}
