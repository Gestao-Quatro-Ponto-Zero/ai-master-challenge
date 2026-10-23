/**
 * Integração com o dado real: o mesmo carregador do `servidor.ts` lê `data/deals.json`, confere o
 * checksum e monta o domínio de verdade. Os blocos são achados pela política (a faixa sem teto,
 * o bloco dos sem data e o restante), então o teste não depende do nome interno de cada bloco.
 *
 * Enquanto o domínio ainda lançar "não implementado", o bloco inteiro é pulado (checagem
 * explícita abaixo); qualquer outra falha na carga reprova.
 */
import { copyFileSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { afterAll, describe, expect, it } from 'vitest';
import type { Organizacao } from '@lead-scorer/dominio/organizacao';
import type { Fila, ItemFila, PoliticaPriorizacao } from '@lead-scorer/dominio/priorizacao';
import { criarApp } from '../src/app';
import { CAMINHO_PADRAO_DEALS, carregarDados } from '../src/carregador';
import { CONFIG_PADRAO } from '../src/infra/config';
import { postJson } from './falsos';

async function tentarCarregar() {
  try {
    return { carga: await carregarDados(CAMINHO_PADRAO_DEALS), pendente: null };
  } catch (e) {
    if (e instanceof Error && e.message.startsWith('não implementado'))
      return { carga: null, pendente: e.message };
    throw e;
  }
}

const { carga, pendente } = await tentarCarregar();
if (pendente)
  console.warn('integração com o dado real pulada: o domínio ainda lança "' + pendente + '"');

const temporarias: string[] = [];
afterAll(() => {
  for (const p of temporarias) rmSync(p, { recursive: true, force: true });
});

describe.skipIf(carga === null)('integração com o dado real', () => {
  const app =
    carga?.ok === true
      ? criarApp({
          servicos: carga.valor.servicos,
          saude: {
            versao: 'teste',
            iniciadoEm: '2026-10-22T00:00:00.000Z',
            dados: carga.valor.dados,
          },
          // o teste faz mais pedidos que um vendedor; o limite em si é testado em protecoes.test.ts
          config: {
            ...CONFIG_PADRAO,
            limiteTaxa: { ...CONFIG_PADRAO.limiteTaxa, capacidade: 10_000 },
          },
          log: () => {},
        })
      : null;

  async function json<T>(
    caminho: string,
    init?: RequestInit,
  ): Promise<{ status: number; corpo: T }> {
    if (!app) throw new Error('carga falhou: ' + JSON.stringify(carga));
    const r = await app.request(caminho, init);
    return { status: r.status, corpo: (await r.json()) as T };
  }

  async function blocosDaPolitica() {
    const { corpo: politica } = await json<PoliticaPriorizacao>('/api/priorizacao/politica');
    const semTeto = politica.faixas.find((f) => f.ateDias === null);
    if (!semTeto) throw new Error('a política não tem faixa sem teto');
    // a primeira faixa (a mais nova) é o Siga; a do meio, o Foque; a sem teto, a Nutrição
    const siga = politica.faixas[0]?.bloco;
    const foque = politica.faixas
      .map((f) => f.bloco)
      .find((b) => b !== semTeto.bloco && b !== siga);
    if (!foque || !siga) throw new Error('a política não tem os três blocos por idade');
    return { foque, siga, nutricao: semTeto.bloco };
  }

  function todos(fila: Fila): ItemFila[] {
    return Object.values(fila.blocos).flat();
  }

  it('o carregador confere o checksum e monta os 8.800 deals', () => {
    expect(carga?.ok).toBe(true);
    if (!carga?.ok) return;
    expect(carga.valor.dados.total).toBe(8800);
    const esperado = readFileSync(CAMINHO_PADRAO_DEALS + '.sha256', 'utf8')
      .trim()
      .split(/\s+/)[0];
    expect(carga.valor.dados.checksum).toBe(esperado);
  });

  it('/health mostra o checksum conferido', async () => {
    const { status, corpo } = await json<{ dados: { checksum: string; total: number } }>('/health');
    expect(status).toBe(200);
    expect(corpo.dados.total).toBe(8800);
    expect(corpo.dados.checksum).toMatch(/^[0-9a-f]{64}$/);
  });

  it('a fila sem filtro reproduz a medição: pela idade Foque 30, Siga 27, Aborde primeiro 500, Nutrição 1.532 (1.291 além da janela); na tela, Foque 33 e Siga 24', async () => {
    const inicio = performance.now();
    const { status, corpo: fila } = await json<Fila>(
      '/api/priorizacao/fila',
      postJson({ filtro: {} }),
    );
    const ms = performance.now() - inicio;
    expect(status).toBe(200);
    const { foque, siga, nutricao } = await blocosDaPolitica();
    const itens = todos(fila);
    const doBloco = (b: string) => itens.filter((i) => i.bloco === b);
    expect(itens).toHaveLength(2089);
    expect(fila.contadores.total).toBe(2089);
    expect(doBloco(foque)).toHaveLength(30);
    expect(doBloco(siga)).toHaveLength(27);
    expect(doBloco('sem_inicio')).toHaveLength(500);
    // na tela: com o Foque vazio, o Siga do vendedor sobe para o Foque (3 negócios de 2 vendedores)
    expect(fila.promovidos).toBe(3);
    expect(fila.contadores.porBloco).toEqual({
      foque_agora: 33,
      siga_no_ritmo: 24,
      nutricao: 1532,
      sem_inicio: 500,
    });
    expect(doBloco(nutricao)).toHaveLength(1532);
    expect(doBloco(nutricao).filter((i) => i.avaliacao.situacao === 'alem_da_janela')).toHaveLength(
      1291,
    );
    // o cálculo é síncrono (o timeout não o interrompe): a fila inteira tem de caber folgada no limite
    expect(ms).toBeLessThan(CONFIG_PADRAO.tempoLimiteMs);
  });

  it('a região Central chega sem nenhum deal no foco (limitação do dataset): Foque 0, Siga 0, Aborde primeiro 500, Nutrição 408', async () => {
    const { foque, siga, nutricao } = await blocosDaPolitica();
    const { status, corpo: fila } = await json<Fila>(
      '/api/priorizacao/fila',
      postJson({ filtro: { regiao: 'Central' } }),
    );
    expect(status).toBe(200);
    const itens = todos(fila);
    expect(itens.filter((i) => i.bloco === foque)).toHaveLength(0);
    expect(itens.filter((i) => i.bloco === siga)).toHaveLength(0);
    expect(itens.filter((i) => i.bloco === 'sem_inicio')).toHaveLength(500);
    expect(itens.filter((i) => i.bloco === nutricao)).toHaveLength(408);
  });

  it('a fila de um vendedor real traz os 3 blocos, só com deals dele', async () => {
    const { foque, siga, nutricao } = await blocosDaPolitica();
    const { corpo: org } = await json<Organizacao>('/api/organizacao');
    let achou = false;
    for (const v of org.vendedores) {
      const { corpo: fila } = await json<Fila>(
        '/api/priorizacao/fila',
        postJson({ filtro: { vendedor: v.nome } }),
      );
      const itens = todos(fila);
      const tem = (b: string) => itens.some((i) => i.bloco === b);
      if (!(tem(foque) && tem(siga) && tem(nutricao))) continue;
      expect(itens.every((i) => i.deal.vendedor === v.nome)).toBe(true);
      expect(itens).toHaveLength(v.abertos);
      achou = true;
      break;
    }
    expect(achou).toBe(true);
  });

  it('/api/priorizacao/item de um deal real repete o bloco da fila e explica o porquê', async () => {
    const { foque } = await blocosDaPolitica();
    const { corpo: fila } = await json<Fila>('/api/priorizacao/fila', postJson({ filtro: {} }));
    const primeiro = todos(fila).find((i) => i.bloco === foque);
    if (!primeiro) throw new Error('nenhum deal no bloco de foco');
    const { status, corpo: item } = await json<ItemFila>(
      '/api/priorizacao/item',
      postJson({ dealId: primeiro.deal.id }),
    );
    expect(status).toBe(200);
    expect(item.deal.id).toBe(primeiro.deal.id);
    expect(item.bloco).toBe(foque);
    expect(item.porque.length).toBeGreaterThan(10);
  });

  it('dado adulterado não carrega (checksum divergente)', async () => {
    const pasta = mkdtempSync(join(tmpdir(), 'lead-scorer-dados-'));
    temporarias.push(pasta);
    const copia = join(pasta, 'deals.json');
    copyFileSync(CAMINHO_PADRAO_DEALS, copia);
    writeFileSync(copia + '.sha256', '0'.repeat(64) + '  deals.json\n');
    const r = await carregarDados(copia);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.erro.codigo).toBe('checksum_divergente');
  });
});
