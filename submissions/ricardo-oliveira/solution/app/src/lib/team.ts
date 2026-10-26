import type { Row } from "./types";
import { K } from "./types";
import { num, str } from "./parse";

// Taxa de fechamento do time = ganhos do time / fechados do time (14 meses + o que o app registrou).
export function taxaTime(kpis: Row[]): number {
  const g = kpis.reduce((a, r) => a + num(r[K.ganhos]), 0);
  const f = kpis.reduce((a, r) => a + num(r[K.fechados]), 0);
  return f ? g / f : 0;
}

export function pontos(delta: number): string {
  const p = Math.round(delta * 1000) / 10;
  return `${p > 0 ? "+" : ""}${p.toFixed(1).replace(".", ",")} pontos`;
}

// Posição do vendedor no time pela taxa de fechamento (1 = melhor), só entre quem tem deals fechados.
export function posicaoNoTime(kpis: Row[], nome: string): { pos: number; de: number } | null {
  const comDeals = kpis.filter((r) => num(r[K.fechados]) > 0).sort((a, b) => num(b[K.taxa]) - num(a[K.taxa]));
  const i = comDeals.findIndex((r) => str(r[K.vendedor]) === nome);
  return i < 0 ? null : { pos: i + 1, de: comDeals.length };
}
