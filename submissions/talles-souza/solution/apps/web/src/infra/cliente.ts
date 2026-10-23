import type { ServicosLeadScorer } from '@lead-scorer/dominio/aplicacao';

/**
 * Versão assíncrona dos casos de uso do domínio: a mesma interface atende a API (HTTP) e o
 * modo local (o domínio rodando no navegador sobre `/dados/deals.json`).
 */
export type ClienteLeadScorer = {
  [K in keyof ServicosLeadScorer]: (
    ...args: Parameters<ServicosLeadScorer[K]>
  ) => Promise<ReturnType<ServicosLeadScorer[K]>>;
};

/** Nome de cada operação do cliente. */
export type Operacao = keyof ClienteLeadScorer;

/**
 * Operações que podem repetir sem efeito colateral. Todas são leitura (GET) ou cálculo puro
 * (POST que classifica sem gravar nada no servidor), então todas são idempotentes.
 */
export const IDEMPOTENTE: Record<Operacao, boolean> = {
  resumo: true,
  deals: true,
  deal: true,
  organizacao: true,
  metodo: true,
  politica: true,
  textos: true,
  chance: true,
  pontos: true,
  motor: true,
  avaliar: true,
  item: true,
  fila: true,
  painel: true,
};

export const OPERACOES = Object.keys(IDEMPOTENTE) as Operacao[];
