/**
 * As respostas e decisões no servidor: baixar as guardadas e enviar as novas. O navegador
 * continua sendo a fonte da tela (o `localStorage`, atrás da porta `RepositorioRespostas`); o
 * servidor, quando tem o banco compartilhado, leva as respostas para os outros aparelhos e para
 * o painel. Falha de rede ou da API não é erro para o vendedor: a resposta fica no navegador e o
 * método devolve null/false. Gravar não é idempotente, então não há retry.
 */
import {
  ROTA_DECIDIR,
  ROTA_DECIDIR_LOTE,
  ROTA_REGISTROS,
  ROTA_RESPONDER,
  type PedidoDecidir,
  type PedidoDecidirLote,
  type PedidoResponder,
  type RespostaRegistros,
} from '@lead-scorer/dominio/qualificacao';
import { TIMEOUT_PADRAO_MS } from './clienteHttp';

export interface RegistrosRemotos {
  /** Os registros guardados no servidor; null se a API não respondeu. */
  baixar(): Promise<RespostaRegistros | null>;
  /** true se o servidor gravou. */
  responder(pedido: PedidoResponder): Promise<boolean>;
  decidir(pedido: PedidoDecidir): Promise<boolean>;
  decidirLote(pedido: PedidoDecidirLote): Promise<boolean>;
}

export interface OpcoesRegistros {
  base?: string;
  fetch?: typeof fetch;
  timeoutMs?: number;
}

/** Cria o cliente dos registros no servidor. */
export function criarRegistrosHttp(opcoes: OpcoesRegistros = {}): RegistrosRemotos {
  const base = opcoes.base ?? '';
  const buscar = opcoes.fetch ?? ((...a: Parameters<typeof fetch>) => globalThis.fetch(...a));
  const timeoutMs = opcoes.timeoutMs ?? TIMEOUT_PADRAO_MS;

  async function chamar(metodo: 'GET' | 'POST', caminho: string, corpo?: unknown) {
    const controle = new AbortController();
    const id = setTimeout(() => controle.abort(), timeoutMs);
    try {
      const r = await buscar(base + caminho, {
        method: metodo,
        signal: controle.signal,
        headers:
          corpo === undefined
            ? { accept: 'application/json' }
            : { accept: 'application/json', 'content-type': 'application/json' },
        ...(corpo === undefined ? {} : { body: JSON.stringify(corpo) }),
      });
      return r.ok ? ((await r.json()) as unknown) : null;
    } catch {
      return null;
    } finally {
      clearTimeout(id);
    }
  }

  return {
    async baixar() {
      const r = (await chamar('GET', ROTA_REGISTROS)) as RespostaRegistros | null;
      return r && Array.isArray(r.registros) ? r : null;
    },
    responder: async (p) => (await chamar('POST', ROTA_RESPONDER, p)) !== null,
    decidir: async (p) => (await chamar('POST', ROTA_DECIDIR, p)) !== null,
    decidirLote: async (p) => (await chamar('POST', ROTA_DECIDIR_LOTE, p)) !== null,
  };
}

/** Sem servidor (testes e modo só local): nada sobe, nada desce. */
export const SEM_REGISTROS_REMOTOS: RegistrosRemotos = {
  baixar: async () => null,
  responder: async () => false,
  decidir: async () => false,
  decidirLote: async () => false,
};
