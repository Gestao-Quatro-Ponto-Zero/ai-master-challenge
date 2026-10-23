/**
 * Cliente HTTP da API: timeout por requisição (AbortController, 4 s), retry com backoff e jitter
 * só em erro transitório de operação idempotente, e cada tentativa passa pelo disjuntor.
 */
import { ROTA_SAUDE, type RespostaSaude } from '@lead-scorer/dominio/aplicacao';
import type { Resultado, RespostaErro } from '@lead-scorer/dominio/compartilhado';
import { ROTA_ORGANIZACAO } from '@lead-scorer/dominio/organizacao';
import {
  ROTA_DEALS,
  ROTA_RESUMO,
  rotaDeal,
  type ConsultaDeals,
  type Deal,
  type RespostaResumo,
} from '@lead-scorer/dominio/pipeline';
import {
  ROTA_FILA,
  ROTA_ITEM,
  ROTA_PAINEL,
  ROTA_POLITICA,
  textosDaTela,
  type PoliticaPriorizacao,
} from '@lead-scorer/dominio/priorizacao';
import { ROTA_METODO } from '@lead-scorer/dominio/qualificacao';
import { ROTA_AVALIAR, ROTA_CHANCE, ROTA_MOTOR, ROTA_PONTOS } from '@lead-scorer/dominio/score';
import { IDEMPOTENTE, type ClienteLeadScorer, type Operacao } from './cliente';
import { criarDisjuntor, type Disjuntor } from './disjuntor';
import { ErroCliente } from './erros';
import { comRetry, type OpcoesRetry } from './retry';
import { temporizadorDoSistema, type Aleatorio, type Dormir, type Temporizador } from './tempo';

export interface OpcoesClienteHttp {
  /** Prefixo das rotas; vazio = mesma origem (o Vite repassa `/api` em dev). */
  base?: string;
  fetch?: typeof fetch;
  timeoutMs?: number;
  retry?: OpcoesRetry;
  disjuntor?: Disjuntor;
  temporizador?: Temporizador;
  dormir?: Dormir;
  aleatorio?: Aleatorio;
}

/** O cliente HTTP também sabe perguntar a saúde da API (a sonda do modo local usa). */
export interface ClienteHttp extends ClienteLeadScorer {
  saude(): Promise<RespostaSaude>;
}

export const TIMEOUT_PADRAO_MS = 4000;

/** Lê `Retry-After` em segundos (o formato que a API manda) e devolve milissegundos. */
export function lerRetryAfter(valor: string | null): number | undefined {
  if (valor === null) return undefined;
  const s = Number(valor);
  return Number.isFinite(s) && s >= 0 ? Math.ceil(s * 1000) : undefined;
}

/** Cria o cliente HTTP. */
export function criarClienteHttp(opcoes: OpcoesClienteHttp = {}): ClienteHttp {
  const base = opcoes.base ?? '';
  const buscar = opcoes.fetch ?? ((...a: Parameters<typeof fetch>) => globalThis.fetch(...a));
  const timeoutMs = opcoes.timeoutMs ?? TIMEOUT_PADRAO_MS;
  const disjuntor = opcoes.disjuntor ?? criarDisjuntor();
  const temporizador = opcoes.temporizador ?? temporizadorDoSistema;

  /** Uma chamada com o corpo já lido: o timeout cobre cabeçalhos e corpo. */
  async function umaTentativa(
    metodo: 'GET' | 'POST',
    caminho: string,
    corpo: unknown,
  ): Promise<RespostaLida> {
    const controle = new AbortController();
    let estourou = false;
    const id = temporizador.definir(() => {
      estourou = true;
      controle.abort();
    }, timeoutMs);
    try {
      const init: RequestInit = {
        method: metodo,
        signal: controle.signal,
        headers: { accept: 'application/json' },
      };
      if (corpo !== undefined) {
        init.body = JSON.stringify(corpo);
        init.headers = { accept: 'application/json', 'content-type': 'application/json' };
      }
      const resposta = await buscar(base + caminho, init);
      const dados = lerJson(await resposta.text());
      if (resposta.status === 429 || resposta.status >= 500) {
        const codigo = codigoDe(dados);
        throw new ErroCliente('http', 'A API respondeu ' + resposta.status, {
          status: resposta.status,
          ...(codigo === undefined ? {} : { codigo }),
          ...retryAfter(resposta),
        });
      }
      return { status: resposta.status, ok: resposta.ok, corpo: dados };
    } catch (e) {
      if (e instanceof ErroCliente) throw e;
      if (estourou) throw new ErroCliente('timeout', 'A API não respondeu em ' + timeoutMs + ' ms');
      throw new ErroCliente('rede', e instanceof Error ? e.message : 'falha de rede');
    } finally {
      temporizador.limpar(id);
    }
  }

  function requisitar(
    op: Operacao | 'saude',
    metodo: 'GET' | 'POST',
    caminho: string,
    corpo?: unknown,
  ) {
    const idempotente = op === 'saude' ? true : IDEMPOTENTE[op];
    return comRetry(() => disjuntor.executar(() => umaTentativa(metodo, caminho, corpo)), {
      idempotente,
      ...(opcoes.retry ? { opcoes: opcoes.retry } : {}),
      ...(opcoes.dormir ? { dormir: opcoes.dormir } : {}),
      ...(opcoes.aleatorio ? { aleatorio: opcoes.aleatorio } : {}),
    });
  }

  /** Resposta 2xx → corpo; 4xx → erro de entrada (não transitório). */
  async function json<T>(
    op: Operacao | 'saude',
    metodo: 'GET' | 'POST',
    caminho: string,
    corpo?: unknown,
  ): Promise<T> {
    const r = await requisitar(op, metodo, caminho, corpo);
    if (!r.ok) {
      const codigo = codigoDe(r.corpo);
      throw new ErroCliente('http', 'A API recusou o pedido (' + r.status + ')', {
        status: r.status,
        ...(codigo === undefined ? {} : { codigo }),
      });
    }
    return r.corpo as T;
  }

  /** Para os casos de uso que devolvem `Resultado`: 4xx com corpo de erro vira `{ ok: false }`. */
  async function resultado<T>(
    op: Operacao,
    caminho: string,
    corpo: unknown,
  ): Promise<Resultado<T>> {
    const r = await requisitar(op, 'POST', caminho, corpo);
    const dados = r.corpo;
    if (r.ok) return { ok: true, valor: dados as T };
    const erro = (dados as Partial<RespostaErro> | null)?.erro;
    if (erro && typeof erro.codigo === 'string') return { ok: false, erro };
    throw new ErroCliente('http', 'A API recusou o pedido (' + r.status + ')', {
      status: r.status,
    });
  }

  return {
    saude: () => json('saude', 'GET', ROTA_SAUDE),
    resumo: () => json('resumo', 'GET', ROTA_RESUMO),
    deals: (consulta: ConsultaDeals) => json('deals', 'GET', ROTA_DEALS + paraQuery(consulta)),
    async deal(id) {
      const r = await requisitar('deal', 'GET', rotaDeal(id));
      const codigo = codigoDe(r.corpo);
      // Só "negócio inexistente" vira null; 404 de rota ausente (API antiga) segue como erro,
      // e o cliente resiliente responde pelo modo local.
      if (r.status === 404 && codigo === 'deal_nao_encontrado') return null;
      if (!r.ok)
        throw new ErroCliente('http', 'A API recusou o pedido (' + r.status + ')', {
          status: r.status,
          ...(codigo === undefined ? {} : { codigo }),
        });
      return r.corpo as Deal;
    },
    organizacao: () => json('organizacao', 'GET', ROTA_ORGANIZACAO),
    metodo: () => json('metodo', 'GET', ROTA_METODO),
    politica: () => json('politica', 'GET', ROTA_POLITICA),
    // Os textos são a política preenchida com a janela: a mesma função pura do domínio, aqui.
    async textos() {
      const [politica, resumo] = await Promise.all([
        json<PoliticaPriorizacao>('politica', 'GET', ROTA_POLITICA),
        json<RespostaResumo>('resumo', 'GET', ROTA_RESUMO),
      ]);
      return textosDaTela(politica, resumo.janela);
    },
    chance: () => json('chance', 'GET', ROTA_CHANCE),
    pontos: () => json('pontos', 'GET', ROTA_PONTOS),
    motor: () => json('motor', 'GET', ROTA_MOTOR),
    avaliar: (pedido) => resultado('avaliar', ROTA_AVALIAR, pedido),
    item: (pedido) => resultado('item', ROTA_ITEM, pedido),
    fila: (pedido) => resultado('fila', ROTA_FILA, pedido),
    painel: (pedido) => resultado('painel', ROTA_PAINEL, pedido),
  };
}

function paraQuery(consulta: ConsultaDeals): string {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(consulta)) if (v !== undefined) q.set(k, String(v));
  const s = q.toString();
  return s === '' ? '' : '?' + s;
}

/** Resposta HTTP com o corpo já lido e interpretado como JSON (null se não for JSON). */
interface RespostaLida {
  status: number;
  ok: boolean;
  corpo: unknown;
}

function lerJson(texto: string): unknown {
  if (texto === '') return null;
  try {
    return JSON.parse(texto) as unknown;
  } catch {
    return null;
  }
}

function codigoDe(corpo: unknown): string | undefined {
  const erro = (corpo as Partial<RespostaErro> | null)?.erro;
  return typeof erro?.codigo === 'string' ? erro.codigo : undefined;
}

function retryAfter(r: Response): { retryAfterMs?: number } {
  const ms = lerRetryAfter(r.headers.get('retry-after'));
  return ms === undefined ? {} : { retryAfterMs: ms };
}
