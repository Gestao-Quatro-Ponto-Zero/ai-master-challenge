import { describe, expect, it } from 'vitest';
import { criarClienteHttp, lerRetryAfter } from './clienteHttp';
import { criarDisjuntor } from './disjuntor';
import { criarRegistrosHttp } from './registrosHttp';
import type { Temporizador } from './tempo';

function json(status: number, corpo: unknown, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { 'content-type': 'application/json', ...headers },
  });
}

/** Temporizador manual: o teste decide quando o timeout dispara. */
function temporizadorManual() {
  const pendentes = new Map<number, () => void>();
  let seq = 0;
  const t: Temporizador & { disparar(): void } = {
    definir(fn) {
      pendentes.set(++seq, fn);
      return seq;
    },
    limpar(id) {
      pendentes.delete(id as number);
    },
    disparar() {
      for (const fn of [...pendentes.values()]) fn();
      pendentes.clear();
    },
  };
  return t;
}

const semEspera = { dormir: async () => {}, aleatorio: () => 0 };

describe('clienteHttp', () => {
  it('lê o Retry-After em segundos, arredondando para cima', () => {
    expect(lerRetryAfter('2')).toBe(2000);
    expect(lerRetryAfter('0.4')).toBe(400);
    expect(lerRetryAfter(null)).toBeUndefined();
    expect(lerRetryAfter('amanhã')).toBeUndefined();
  });

  it('repete um 503 e devolve a resposta seguinte', async () => {
    const respostas = [
      json(503, { erro: { codigo: 'tempo_esgotado', mensagem: 'x' } }),
      json(200, { status: 'ok' }),
    ];
    const chamadas: string[] = [];
    const c = criarClienteHttp({
      ...semEspera,
      fetch: async (url) => {
        chamadas.push(String(url));
        return respostas.shift() ?? json(500, {});
      },
    });
    await expect(c.politica()).resolves.toEqual({ status: 'ok' });
    expect(chamadas).toEqual(['/api/priorizacao/politica', '/api/priorizacao/politica']);
  });

  it('aborta pelo timeout e marca como transitório', async () => {
    const tempo = temporizadorManual();
    let tentativas = 0;
    const c = criarClienteHttp({
      ...semEspera,
      temporizador: tempo,
      retry: { tentativas: 1, baseMs: 200, tetoMs: 2000 },
      fetch: (_url, init) =>
        new Promise((_res, rej) => {
          tentativas++;
          init?.signal?.addEventListener('abort', () =>
            rej(new DOMException('abortado', 'AbortError')),
          );
          tempo.disparar();
        }),
    });
    await expect(c.resumo()).rejects.toMatchObject({ tipo: 'timeout', transitorio: true });
    expect(tentativas).toBe(1);
  });

  it('não repete 400 e devolve o erro do domínio como resultado', async () => {
    let chamadas = 0;
    const c = criarClienteHttp({
      ...semEspera,
      fetch: async () => {
        chamadas++;
        return json(400, {
          erro: { codigo: 'respostas_invalidas', mensagem: 'respostas de outro deal' },
        });
      },
    });
    const r = await c.fila({ filtro: {}, respostas: [] });
    expect(r).toEqual({
      ok: false,
      erro: { codigo: 'respostas_invalidas', mensagem: 'respostas de outro deal' },
    });
    expect(chamadas).toBe(1);
  });

  it('deal inexistente (404) vira null', async () => {
    const c = criarClienteHttp({
      ...semEspera,
      fetch: async () => json(404, { erro: { codigo: 'deal_nao_encontrado', mensagem: 'x' } }),
    });
    await expect(c.deal('ZZZZ9999')).resolves.toBeNull();
  });

  it('manda a query dos deals e o corpo JSON dos POST', async () => {
    const vistos: { url: string; metodo: string | undefined; corpo: unknown }[] = [];
    const c = criarClienteHttp({
      ...semEspera,
      fetch: async (url, init) => {
        vistos.push({
          url: String(url),
          metodo: init?.method,
          corpo: init?.body ? JSON.parse(String(init.body)) : null,
        });
        return json(200, { total: 0, limite: 10, deslocamento: 0, deals: [] });
      },
    });
    await c.deals({ vendedor: 'Ana', limite: 10, deslocamento: 0 });
    await c.item({ dealId: 'AAAA0001', respostas: null });
    expect(vistos[0]).toEqual({
      url: '/api/pipeline/deals?vendedor=Ana&limite=10&deslocamento=0',
      metodo: 'GET',
      corpo: null,
    });
    expect(vistos[1]).toEqual({
      url: '/api/priorizacao/item',
      metodo: 'POST',
      corpo: { dealId: 'AAAA0001', respostas: null },
    });
  });

  it('três falhas de rede abrem o disjuntor e a chamada seguinte nem sai', async () => {
    let chamadas = 0;
    const disjuntor = criarDisjuntor(undefined, () => 0);
    const c = criarClienteHttp({
      ...semEspera,
      disjuntor,
      fetch: async () => {
        chamadas++;
        throw new TypeError('Failed to fetch');
      },
    });
    await expect(c.resumo()).rejects.toMatchObject({ tipo: 'rede' });
    expect(chamadas).toBe(3);
    await expect(c.resumo()).rejects.toMatchObject({ tipo: 'circuito_aberto' });
    expect(chamadas).toBe(3);
  });
});

describe('registros no servidor (respostas e decisões)', () => {
  const registro = {
    formato: 1 as const,
    dealId: 'AAAA0001',
    metodoId: 'metodo-bant-v1',
    respostas: [],
    decisao: null,
  };
  it('baixa os registros e envia as gravações como JSON', async () => {
    const pedidos: { url: string; init: RequestInit | undefined }[] = [];
    const registros = criarRegistrosHttp({
      fetch: async (url, init) => {
        pedidos.push({ url: String(url), init });
        return new Response(
          JSON.stringify(
            String(url).endsWith('/registros')
              ? { armazenamento: 'banco', registros: [registro] }
              : { registros: 1 },
          ),
          { status: 200 },
        );
      },
    });
    expect(await registros.baixar()).toEqual({ armazenamento: 'banco', registros: [registro] });
    expect(
      await registros.decidirLote({
        dealIds: ['AAAA0001'],
        acao: 'encaminhar_para_nutricao',
        aceita: true,
      }),
    ).toBe(true);
    expect(pedidos.map((x) => [x.init?.method, x.url])).toEqual([
      ['GET', '/api/qualificacao/registros'],
      ['POST', '/api/qualificacao/decidir-lote'],
    ]);
    expect(JSON.parse(String(pedidos[1]?.init?.body))).toMatchObject({ dealIds: ['AAAA0001'] });
  });

  it('API fora ou recusando: null/false, sem lançar (a resposta fica no navegador)', async () => {
    let chamadas = 0;
    const caida = criarRegistrosHttp({
      fetch: async () => {
        chamadas += 1;
        throw new TypeError('Failed to fetch');
      },
    });
    expect(await caida.baixar()).toBeNull();
    expect(await caida.responder({ dealId: 'AAAA0001', perguntaId: 'dor', valor: 'sim' })).toBe(
      false,
    );
    expect(chamadas).toBe(2); // gravar não repete
    const recusa = criarRegistrosHttp({
      fetch: async () => new Response('{}', { status: 404 }),
    });
    expect(await recusa.decidir({ dealId: 'AAAA0001', acao: 'manter_ritmo', aceita: true })).toBe(
      false,
    );
  });
});
