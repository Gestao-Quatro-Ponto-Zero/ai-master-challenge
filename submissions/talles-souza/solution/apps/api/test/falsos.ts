/**
 * Serviço falso para os testes de contrato: devolve objetos marcados e grava com o que foi
 * chamado. A API é só fronteira, então o teste confere que a entrada validada chega ao domínio
 * e que a saída do domínio sai inteira em JSON; a regra em si é testada no domínio.
 */
import type { ServicosLeadScorer } from '@lead-scorer/dominio/aplicacao';
import { falha, ok } from '@lead-scorer/dominio/compartilhado';
import type { DepsApp } from '../src/app';
import { CONFIG_PADRAO, type ConfigApi } from '../src/infra/config';

/** Os testes de fronteira não montam um `Deal` ou uma `Fila` completos: um marcador basta (cast só aqui). */
function marcador<T>(nome: string, extra: Record<string, unknown> = {}): T {
  return { marcador: nome, ...extra } as unknown as T;
}

/** Deal que existe no serviço falso. */
export const ID_EXISTENTE = 'AAAA1111';
/** Deal que o serviço falso não acha. */
export const ID_INEXISTENTE = 'ZZZZ9999';

export interface Chamadas {
  deals: unknown[];
  fila: unknown[];
  item: unknown[];
  avaliar: unknown[];
}

/** Monta o serviço falso; `troca` substitui métodos (para simular erro do domínio ou exceção). */
export function servicoFalso(troca: Partial<ServicosLeadScorer> = {}): {
  servicos: ServicosLeadScorer;
  chamadas: Chamadas;
} {
  const chamadas: Chamadas = { deals: [], fila: [], item: [], avaliar: [] };
  const servicos: ServicosLeadScorer = {
    resumo: () => marcador('resumo'),
    deals: (consulta) => {
      chamadas.deals.push(consulta);
      return { total: 0, limite: consulta.limite, deslocamento: consulta.deslocamento, deals: [] };
    },
    deal: (id) => (id === ID_EXISTENTE ? marcador('deal', { id }) : null),
    organizacao: () => ({ vendedores: [], managers: [], regioes: ['Central', 'East', 'West'] }),
    metodo: () => marcador('metodo'),
    politica: () => marcador('politica'),
    textos: () => marcador('textos'),
    chance: () => marcador('chance'),
    pontos: () => marcador('pontos'),
    motor: () => marcador('motor'),
    avaliar: (pedido) => {
      chamadas.avaliar.push(pedido);
      if ('dealId' in pedido && pedido.dealId === ID_INEXISTENTE) {
        return falha('deal_nao_encontrado', 'Nenhum deal com esse id.');
      }
      return ok(marcador('avaliacao'));
    },
    item: (pedido) => {
      chamadas.item.push(pedido);
      if ('dealId' in pedido && pedido.dealId === ID_INEXISTENTE) {
        return falha('deal_nao_encontrado', 'Nenhum deal com esse id.');
      }
      if ('lead' in pedido && pedido.lead.vendedor === 'Ninguém') {
        return falha('lead_invalido', 'Vendedor desconhecido.');
      }
      return ok(marcador('item'));
    },
    fila: (pedido) => {
      chamadas.fila.push(pedido);
      return ok(marcador('fila'));
    },
    painel: (pedido) => {
      chamadas.fila.push(pedido);
      return ok(marcador('painel'));
    },
    ...troca,
  };
  return { servicos, chamadas };
}

/** Dependências do app para teste: serviço falso, log mudo e config ajustável. */
export function depsDeTeste(
  opcoes: {
    servicos?: ServicosLeadScorer;
    config?: Partial<ConfigApi>;
    relogio?: () => number;
  } = {},
): DepsApp {
  return {
    servicos: opcoes.servicos ?? servicoFalso().servicos,
    saude: {
      versao: '0.0.0-teste',
      iniciadoEm: '2026-10-22T00:00:00.000Z',
      dados: { total: 8800, referencia: '2017-12-31', checksum: 'abc123' },
    },
    config: { ...CONFIG_PADRAO, ...opcoes.config },
    ...(opcoes.relogio ? { relogio: opcoes.relogio } : {}),
    // nos testes o IP vem de um cabeçalho próprio do teste (não há socket); a API real usa o socket
    ipDe: (c) => c.req.header('x-ip-de-teste') ?? '10.0.0.1',
    log: () => {},
  };
}

/** Corpo JSON de um POST. */
export function postJson(corpo: unknown, cabecalhos: Record<string, string> = {}): RequestInit {
  return {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...cabecalhos },
    body: typeof corpo === 'string' ? corpo : JSON.stringify(corpo),
  };
}
