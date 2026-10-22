/** Funções de formatação para exibir números e textos de forma amigável. */

import type { Etapa } from "../tipos";

const formatoMoeda = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

/** 5482 -> "US$ 5.482" */
export function formatarMoeda(valor: number): string {
  return formatoMoeda.format(valor);
}

/** 1234567 -> "US$ 1,2 mi" (para os cartões de resumo) */
export function formatarMoedaCompacta(valor: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(valor);
}

/** 0.6315 -> "63%" */
export function formatarPorcentagem(valor: number): string {
  return `${Math.round(valor * 100)}%`;
}

/** Título do negócio: o nome da conta ou, se não houver, o código do negócio. */
export function tituloDeal(deal: { id: string; conta: string; conta_informada: boolean }): string {
  return deal.conta_informada ? deal.conta : `Negócio ${deal.id} (sem conta)`;
}

/** 2089 -> "2.089" */
export function formatarNumero(valor: number): string {
  return valor.toLocaleString("pt-BR");
}

/** Nome da etapa em português. */
export const NOMES_ETAPA: Record<Etapa, string> = {
  Prospecting: "Prospecção",
  Engaging: "Em negociação",
};

/** 1 -> "1 dia", 12 -> "12 dias", null -> "Ainda não iniciado" */
export function formatarDias(dias: number | null): string {
  if (dias === null) return "Ainda não iniciado";
  return dias === 1 ? "1 dia" : `${dias} dias`;
}
