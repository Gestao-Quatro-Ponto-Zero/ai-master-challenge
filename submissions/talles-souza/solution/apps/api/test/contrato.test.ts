/** Contrato das rotas contra o serviço falso: entrada validada chega ao domínio, saída sai inteira, erros no formato padrão. */
import { describe, expect, it } from 'vitest';
import { falha } from '@lead-scorer/dominio/compartilhado';
import { criarApp } from '../src/app';
import { depsDeTeste, ID_EXISTENTE, ID_INEXISTENTE, postJson, servicoFalso } from './falsos';

function montar(troca: Parameters<typeof servicoFalso>[0] = {}) {
  const { servicos, chamadas } = servicoFalso(troca);
  return { app: criarApp(depsDeTeste({ servicos })), chamadas };
}

describe('saúde', () => {
  it('GET /health devolve status, versão, dados e início', async () => {
    const { app } = montar();
    const r = await app.request('/health');
    expect(r.status).toBe(200);
    expect(await r.json()).toEqual({
      status: 'ok',
      versao: '0.0.0-teste',
      dados: { total: 8800, referencia: '2017-12-31', checksum: 'abc123' },
      iniciadoEm: '2026-10-22T00:00:00.000Z',
    });
  });
});

describe('pipeline', () => {
  it('GET /api/pipeline/resumo repassa o resumo do domínio', async () => {
    const { app } = montar();
    const r = await app.request('/api/pipeline/resumo');
    expect(r.status).toBe(200);
    expect(await r.json()).toEqual({ marcador: 'resumo' });
  });

  it('GET /api/pipeline/deals aplica os padrões do contrato e converte números', async () => {
    const { app, chamadas } = montar();
    const r = await app.request(
      '/api/pipeline/deals?vendedor=Darcel%20Schlecht&aberto=true&limite=10',
    );
    expect(r.status).toBe(200);
    expect(chamadas.deals).toEqual([
      { vendedor: 'Darcel Schlecht', aberto: 'true', limite: 10, deslocamento: 0 },
    ]);
    expect(await r.json()).toMatchObject({ limite: 10, deslocamento: 0 });
  });

  it('query inválida → 400 entrada_invalida com o caminho do problema', async () => {
    const { app, chamadas } = montar();
    const r = await app.request('/api/pipeline/deals?limite=abc');
    expect(r.status).toBe(400);
    const corpo = (await r.json()) as { erro: { codigo: string; detalhes: { caminho: string }[] } };
    expect(corpo.erro.codigo).toBe('entrada_invalida');
    expect(corpo.erro.detalhes.map((d) => d.caminho)).toContain('limite');
    expect(chamadas.deals).toEqual([]);
  });

  it('parâmetro desconhecido na query → 400 (contrato estrito)', async () => {
    const { app } = montar();
    expect((await app.request('/api/pipeline/deals?ordem=valor')).status).toBe(400);
  });

  it('o erro não ecoa o valor recebido', async () => {
    const { app } = montar();
    const valor = 'X'.repeat(81);
    const r = await app.request('/api/pipeline/deals?vendedor=' + valor);
    expect(r.status).toBe(400);
    expect(await r.text()).not.toContain(valor);
  });

  it('GET /api/pipeline/deals/:id devolve o deal; inexistente → 404; id fora do formato → 400', async () => {
    const { app } = montar();
    const achou = await app.request('/api/pipeline/deals/' + ID_EXISTENTE);
    expect(achou.status).toBe(200);
    expect(await achou.json()).toEqual({ marcador: 'deal', id: ID_EXISTENTE });

    const naoAchou = await app.request('/api/pipeline/deals/' + ID_INEXISTENTE);
    expect(naoAchou.status).toBe(404);
    expect(((await naoAchou.json()) as { erro: { codigo: string } }).erro.codigo).toBe(
      'deal_nao_encontrado',
    );

    const torto = await app.request('/api/pipeline/deals/abc');
    expect(torto.status).toBe(400);
    expect(
      ((await torto.json()) as { erro: { detalhes: { caminho: string }[] } }).erro.detalhes[0]
        ?.caminho,
    ).toBe('id');
  });
});

describe('organização, método e política', () => {
  it('GET /api/score/chance, /api/score/pontos e /api/score/motor devolvem o que o domínio mediu', async () => {
    const app = criarApp(depsDeTeste());
    expect(await (await app.request('/api/score/chance')).json()).toEqual({ marcador: 'chance' });
    expect(await (await app.request('/api/score/pontos')).json()).toEqual({ marcador: 'pontos' });
    expect(await (await app.request('/api/score/motor')).json()).toEqual({ marcador: 'motor' });
  });

  it('GET /api/organizacao, /api/qualificacao/metodo e /api/priorizacao/politica', async () => {
    const { app } = montar();
    const org = await app.request('/api/organizacao');
    expect(org.status).toBe(200);
    expect(await org.json()).toEqual({
      vendedores: [],
      managers: [],
      regioes: ['Central', 'East', 'West'],
    });
    expect(await (await app.request('/api/qualificacao/metodo')).json()).toEqual({
      marcador: 'metodo',
    });
    expect(await (await app.request('/api/priorizacao/politica')).json()).toEqual({
      marcador: 'politica',
    });
  });
});

describe('priorização', () => {
  it('POST /api/priorizacao/fila valida o filtro e completa respostas com []', async () => {
    const { app, chamadas } = montar();
    const r = await app.request(
      '/api/priorizacao/fila',
      postJson({ filtro: { vendedor: 'Darcel Schlecht' } }),
    );
    expect(r.status).toBe(200);
    expect(await r.json()).toEqual({ marcador: 'fila' });
    expect(chamadas.fila).toEqual([{ filtro: { vendedor: 'Darcel Schlecht' }, respostas: [] }]);
  });

  it('fila: corpo sem filtro, campo a mais ou JSON malformado → 400', async () => {
    const { app, chamadas } = montar();
    expect((await app.request('/api/priorizacao/fila', postJson({}))).status).toBe(400);
    expect(
      (await app.request('/api/priorizacao/fila', postJson({ filtro: {}, nota: 1 }))).status,
    ).toBe(400);
    const malformado = await app.request('/api/priorizacao/fila', postJson('{"filtro": '));
    expect(malformado.status).toBe(400);
    expect(((await malformado.json()) as { erro: { codigo: string } }).erro.codigo).toBe(
      'entrada_invalida',
    );
    expect((await app.request('/api/priorizacao/fila', postJson(''))).status).toBe(400);
    expect(chamadas.fila).toEqual([]);
  });

  it('fila: respostas_invalidas do domínio → 400 com o código do domínio', async () => {
    const { app } = montar({
      fila: () => falha('respostas_invalidas', 'O método das respostas não é o ativo.'),
    });
    const r = await app.request('/api/priorizacao/fila', postJson({ filtro: {} }));
    expect(r.status).toBe(400);
    expect(await r.json()).toEqual({
      erro: { codigo: 'respostas_invalidas', mensagem: 'O método das respostas não é o ativo.' },
    });
  });

  it('POST /api/priorizacao/item: deal, lead, deal inexistente (404) e lead inválido (400)', async () => {
    const { app, chamadas } = montar();
    const deal = await app.request('/api/priorizacao/item', postJson({ dealId: ID_EXISTENTE }));
    expect(deal.status).toBe(200);
    expect(await deal.json()).toEqual({ marcador: 'item' });

    const lead = { vendedor: 'Darcel Schlecht', produto: 'GTX Pro', dataEngajamento: '2017-12-01' };
    expect(
      (await app.request('/api/priorizacao/item', postJson({ lead, respostas: null }))).status,
    ).toBe(200);

    const inexistente = await app.request(
      '/api/priorizacao/item',
      postJson({ dealId: ID_INEXISTENTE }),
    );
    expect(inexistente.status).toBe(404);

    const invalido = await app.request(
      '/api/priorizacao/item',
      postJson({ lead: { vendedor: 'Ninguém', produto: 'GTX Pro' } }),
    );
    expect(invalido.status).toBe(400);
    expect(((await invalido.json()) as { erro: { codigo: string } }).erro.codigo).toBe(
      'lead_invalido',
    );

    expect(chamadas.item).toHaveLength(4);
  });

  it('item: data em formato errado ou id fora do padrão → 400 sem chamar o domínio', async () => {
    const { app, chamadas } = montar();
    const lead = { vendedor: 'Darcel Schlecht', produto: 'GTX Pro', dataEngajamento: '01/12/2017' };
    expect((await app.request('/api/priorizacao/item', postJson({ lead }))).status).toBe(400);
    expect((await app.request('/api/priorizacao/item', postJson({ dealId: 'abc' }))).status).toBe(
      400,
    );
    expect(chamadas.item).toEqual([]);
  });

  it('item: motivo_obrigatorio do domínio → 400', async () => {
    const { app } = montar({ item: () => falha('motivo_obrigatorio', 'Contestar exige motivo.') });
    expect(
      (await app.request('/api/priorizacao/item', postJson({ dealId: ID_EXISTENTE }))).status,
    ).toBe(400);
  });
});

describe('score', () => {
  it('POST /api/score/avaliar: deal existe → 200; não existe → 404; corpo inválido → 400', async () => {
    const { app } = montar();
    const ok = await app.request('/api/score/avaliar', postJson({ dealId: ID_EXISTENTE }));
    expect(ok.status).toBe(200);
    expect(await ok.json()).toEqual({ marcador: 'avaliacao' });
    expect(
      (await app.request('/api/score/avaliar', postJson({ dealId: ID_INEXISTENTE }))).status,
    ).toBe(404);
    expect(
      (await app.request('/api/score/avaliar', postJson({ dealId: ID_EXISTENTE, lead: {} })))
        .status,
    ).toBe(400);
  });
});

describe('erros gerais', () => {
  it('rota inexistente → 404 nao_encontrado (dentro e fora de /api)', async () => {
    const { app } = montar();
    for (const caminho of ['/api/nada', '/nada']) {
      const r = await app.request(caminho);
      expect(r.status).toBe(404);
      expect(await r.json()).toEqual({
        erro: { codigo: 'nao_encontrado', mensagem: 'Rota inexistente.' },
      });
    }
  });

  it('exceção no domínio → 500 erro_interno sem stack nem mensagem interna', async () => {
    const { app } = montar({
      resumo: () => {
        throw new Error('segredo interno em /c/caminho/arquivo.ts:10');
      },
    });
    const r = await app.request('/api/pipeline/resumo');
    expect(r.status).toBe(500);
    const texto = await r.text();
    expect(JSON.parse(texto)).toEqual({
      erro: { codigo: 'erro_interno', mensagem: 'Erro interno. Tente de novo.' },
    });
    expect(texto).not.toContain('segredo');
    expect(texto).not.toContain('.ts');
  });

  it('o log tem uma linha por requisição, sem query nem corpo', async () => {
    const linhas: string[] = [];
    const app = criarApp({ ...depsDeTeste(), log: (l) => linhas.push(l) });
    await app.request(
      '/api/priorizacao/fila?x=1',
      postJson({ filtro: { vendedor: 'Darcel Schlecht' } }),
    );
    expect(linhas).toHaveLength(1);
    expect(linhas[0]).toMatch(/^POST \/api\/priorizacao\/fila 200 \d+ms$/);
  });
});
