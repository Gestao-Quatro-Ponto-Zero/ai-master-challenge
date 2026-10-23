/**
 * Respostas e decisões gravadas no servidor, com o dado real e o armazém em memória (o mesmo
 * contrato do banco): gravar uma resposta, contestar com motivo e encaminhar em lote, uma linha
 * por negócio, com a mesma data e o mesmo motivo.
 */
import { describe, expect, it } from 'vitest';
import type { RespostaPainel } from '@lead-scorer/dominio/priorizacao';
import type { RespostaLote, RespostaRegistros } from '@lead-scorer/dominio/qualificacao';
import { criarApp } from '../src/app';
import { CAMINHO_PADRAO_DEALS, carregarDados } from '../src/carregador';
import { CONFIG_PADRAO } from '../src/infra/config';
import { criarArmazemEmMemoria } from '../src/qualificacao';
import { postJson } from './falsos';

const carga = await carregarDados(CAMINHO_PADRAO_DEALS);
if (!carga.ok) throw new Error(carga.erro.mensagem);
const { servicos, dados } = carga.valor;

function montar() {
  let agora = Date.parse('2026-10-22T12:00:00.000Z');
  const armazem = criarArmazemEmMemoria();
  const app = criarApp({
    servicos,
    saude: { versao: 't', iniciadoEm: '2026-10-22T00:00:00.000Z', dados },
    config: { ...CONFIG_PADRAO, limiteTaxa: { ...CONFIG_PADRAO.limiteTaxa, capacidade: 10_000 } },
    relogio: () => (agora += 1000),
    log: () => {},
    registros: armazem,
  });
  async function json<T>(caminho: string, init?: RequestInit) {
    const r = await app.request(caminho, init);
    return { status: r.status, corpo: (await r.json()) as T };
  }
  return { json, armazem };
}

const fila = servicos.fila({ filtro: {}, respostas: [] });
if (!fila.ok) throw new Error('fila');
const nutricao = fila.valor.blocos.nutricao;
const umFoque = fila.valor.blocos.foque_agora[0]!.deal;

describe('respostas e decisões no servidor', () => {
  it('grava a resposta e devolve o estado do negócio; o GET filtra pelo vendedor', async () => {
    const { json } = montar();
    const r = await json<{ respostas: unknown[] }>(
      '/api/qualificacao/responder',
      postJson({ dealId: umFoque.id, perguntaId: 'proximo_passo', valor: 'nao' }),
    );
    expect(r.status).toBe(200);
    expect(r.corpo.respostas).toEqual([
      { perguntaId: 'proximo_passo', valor: 'nao', respondidoEm: expect.any(String) },
    ]);
    const doVendedor = await json<RespostaRegistros>(
      '/api/qualificacao/registros?vendedor=' + encodeURIComponent(umFoque.vendedor),
    );
    expect(doVendedor.corpo.armazenamento).toBe('memoria');
    expect(doVendedor.corpo.registros.map((x) => x.dealId)).toEqual([umFoque.id]);
    const outro = servicos.organizacao().vendedores.find((v) => v.nome !== umFoque.vendedor)!;
    const deOutro = await json<RespostaRegistros>(
      '/api/qualificacao/registros?vendedor=' + encodeURIComponent(outro.nome),
    );
    expect(deOutro.corpo.registros).toEqual([]);
  });

  it('recusa negócio inexistente, pergunta fora do método e contestação sem motivo', async () => {
    const { json, armazem } = montar();
    const inexistente = await json<{ erro: { codigo: string } }>(
      '/api/qualificacao/responder',
      postJson({ dealId: 'ZZZZ9999', perguntaId: 'dor', valor: 'sim' }),
    );
    expect([inexistente.status, inexistente.corpo.erro.codigo]).toEqual([
      404,
      'deal_nao_encontrado',
    ]);
    const pergunta = await json<{ erro: { codigo: string } }>(
      '/api/qualificacao/responder',
      postJson({ dealId: umFoque.id, perguntaId: 'orcamento', valor: 'sim' }),
    );
    expect([pergunta.status, pergunta.corpo.erro.codigo]).toEqual([400, 'pergunta_inexistente']);
    const semMotivo = await json<{ erro: { codigo: string } }>(
      '/api/qualificacao/decidir',
      postJson({ dealId: umFoque.id, acao: 'avancar_hoje', aceita: false }),
    );
    expect([semMotivo.status, semMotivo.corpo.erro.codigo]).toEqual([400, 'motivo_obrigatorio']);
    expect(await armazem.listar()).toEqual({ respostas: [], decisoes: [] });
  });

  it('"Encaminhar os N": uma linha por negócio, mesma data e mesmo motivo', async () => {
    const { json, armazem } = montar();
    const ids = nutricao.slice(0, 5).map((i) => i.deal.id);
    const r = await json<RespostaLote>(
      '/api/qualificacao/decidir-lote',
      postJson({ dealIds: ids, acao: 'encaminhar_para_nutricao', aceita: true }),
    );
    expect(r.status).toBe(200);
    expect(r.corpo).toMatchObject({ armazenamento: 'memoria', registros: 5 });
    const { decisoes } = await armazem.listar();
    expect(decisoes.map((d) => d.dealId)).toEqual(ids);
    expect(new Set(decisoes.map((d) => d.em))).toEqual(new Set([r.corpo.em]));
    expect(new Set(decisoes.map((d) => d.motivo))).toEqual(new Set([null]));
    for (const d of decisoes) expect(d.vendedor).toBe(servicos.deal(d.dealId)?.vendedor);
    // o encaminhado continua na base: o GET devolve a decisão de cada um
    const todos = await json<RespostaRegistros>('/api/qualificacao/registros');
    expect(todos.corpo.registros.map((x) => x.decisao?.acao)).toEqual(
      ids.map(() => 'encaminhar_para_nutricao'),
    );
  });

  it('lote vazio, repetido ou com negócio inexistente não grava nada', async () => {
    const { json, armazem } = montar();
    const [a, b] = nutricao.map((i) => i.deal.id);
    const corpo = { acao: 'encaminhar_para_nutricao', aceita: true };
    const vazio = await json<{ erro: { codigo: string } }>(
      '/api/qualificacao/decidir-lote',
      postJson({ ...corpo, dealIds: [] }),
    );
    expect(vazio.status).toBe(400);
    const repetido = await json<{ erro: { codigo: string } }>(
      '/api/qualificacao/decidir-lote',
      postJson({ ...corpo, dealIds: [a, a] }),
    );
    expect([repetido.status, repetido.corpo.erro.codigo]).toEqual([400, 'lote_repetido']);
    const inexistente = await json<{ erro: { codigo: string } }>(
      '/api/qualificacao/decidir-lote',
      postJson({ ...corpo, dealIds: [b, 'ZZZZ9999'] }),
    );
    expect(inexistente.status).toBe(404);
    expect((await armazem.listar()).decisoes).toEqual([]);
  });
});

describe('painel pela API', () => {
  it('POST /api/priorizacao/painel: sem filtro e por região, os números mudam com o filtro', async () => {
    const { json } = montar();
    const todos = await json<RespostaPainel>('/api/priorizacao/painel', postJson({ filtro: {} }));
    expect(todos.status).toBe(200);
    expect(todos.corpo.total).toBe(2089);
    expect(todos.corpo.foqueSemConversa.n).toBe(33);
    expect(todos.corpo.semInicio.n).toBe(500);
    expect(todos.corpo.vendedores).toHaveLength(35);
    const west = await json<RespostaPainel>(
      '/api/priorizacao/painel',
      postJson({ filtro: { regiao: 'West' } }),
    );
    expect(west.corpo.foqueSemConversa.n).toBe(17);
    expect(west.corpo.vendedores).toHaveLength(12);
    expect(west.corpo.total).toBeLessThan(todos.corpo.total);
  });
});
