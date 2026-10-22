/**
 * Único ponto de comunicação com o backend.
 * Os componentes nunca chamam fetch diretamente: usam as funções abaixo.
 */

import type { DealDetalhe, Filtros, ListaDeals, OpcoesFiltro, RegrasPontuacao, Resumo, Validacao } from "../tipos";

// Em desenvolvimento o Vite repassa /api para o backend (ver vite.config.ts).
const URL_BASE = "/api";

async function buscar<T>(caminho: string): Promise<T> {
  const resposta = await fetch(`${URL_BASE}${caminho}`);
  if (!resposta.ok) {
    throw new Error(`Erro ${resposta.status} ao acessar ${caminho}`);
  }
  return resposta.json() as Promise<T>;
}

/** Monta a query string ignorando filtros vazios. */
function paraQuery(filtros: Filtros): string {
  const parametros = new URLSearchParams();
  Object.entries(filtros).forEach(([chave, valor]) => {
    if (valor) parametros.set(chave, valor);
  });
  const query = parametros.toString();
  return query ? `?${query}` : "";
}

export const api = {
  pipeline: (filtros: Filtros) => buscar<ListaDeals>(`/pipeline${paraQuery(filtros)}`),
  resumo: (filtros: Filtros) => buscar<Resumo>(`/resumo${paraQuery(filtros)}`),
  deal: (id: string) => buscar<DealDetalhe>(`/deals/${encodeURIComponent(id)}`),
  opcoesFiltro: () => buscar<OpcoesFiltro>("/filtros"),
  regras: () => buscar<RegrasPontuacao>("/regras"),
  validacao: () => buscar<Validacao>("/validacao"),
};
