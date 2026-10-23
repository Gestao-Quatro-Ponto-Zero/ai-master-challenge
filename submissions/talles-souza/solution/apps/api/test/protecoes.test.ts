/** As proteções da borda: payload, rate limit com relógio controlado, timeout, cabeçalhos, CORS e config. */
import { describe, expect, it } from 'vitest';
import { criarApp } from '../src/app';
import { CONFIG_PADRAO, lerConfig } from '../src/infra/config';
import { criarLimitador } from '../src/infra/limite-taxa';
import { CSP_API } from '../src/infra/seguranca';
import { depsDeTeste, postJson } from './falsos';

function relogioControlado(inicio = 1_000_000) {
  let agora = inicio;
  return { relogio: () => agora, avancar: (ms: number) => (agora += ms) };
}

describe('limite de payload', () => {
  it('corpo acima de 1 MB → 413 payload_grande (padrão)', async () => {
    const app = criarApp(depsDeTeste());
    const grande = JSON.stringify({ filtro: {}, lixo: 'x'.repeat(1024 * 1024) });
    const r = await app.request('/api/priorizacao/fila', postJson(grande));
    expect(r.status).toBe(413);
    expect(((await r.json()) as { erro: { codigo: string } }).erro.codigo).toBe('payload_grande');
  });

  it('corpo abaixo do limite passa para a validação', async () => {
    const app = criarApp(depsDeTeste({ config: { payloadMaxBytes: 100 } }));
    expect((await app.request('/api/priorizacao/fila', postJson({ filtro: {} }))).status).toBe(200);
    expect(
      (
        await app.request(
          '/api/priorizacao/fila',
          postJson({ filtro: { vendedor: 'y'.repeat(120) } }),
        )
      ).status,
    ).toBe(413);
  });
});

describe('rate limit (token bucket por IP)', () => {
  const config = { limiteTaxa: { capacidade: 3, recargaPorSegundo: 1, limpezaACadaMs: 60_000 } };

  it('estoura na 4ª seguida com 429, Retry-After e libera depois da recarga', async () => {
    const t = relogioControlado();
    const app = criarApp(depsDeTeste({ config, relogio: t.relogio }));
    for (let i = 0; i < 3; i++) expect((await app.request('/api/organizacao')).status).toBe(200);

    const barrado = await app.request('/api/organizacao');
    expect(barrado.status).toBe(429);
    expect(barrado.headers.get('Retry-After')).toBe('1');
    expect(((await barrado.json()) as { erro: { codigo: string } }).erro.codigo).toBe(
      'limite_de_taxa',
    );

    t.avancar(999);
    expect((await app.request('/api/organizacao')).status).toBe(429);
    t.avancar(1);
    expect((await app.request('/api/organizacao')).status).toBe(200);
    expect((await app.request('/api/organizacao')).status).toBe(429);
  });

  it('Retry-After arredonda para cima com recarga lenta', async () => {
    const t = relogioControlado();
    const app = criarApp(
      depsDeTeste({
        config: { limiteTaxa: { capacidade: 1, recargaPorSegundo: 0.4, limpezaACadaMs: 60_000 } },
        relogio: t.relogio,
      }),
    );
    expect((await app.request('/api/organizacao')).status).toBe(200);
    const barrado = await app.request('/api/organizacao');
    expect(barrado.headers.get('Retry-After')).toBe('3'); // 1 ficha / 0,4 por s = 2,5 s → 3
    t.avancar(2_500);
    expect((await app.request('/api/organizacao')).status).toBe(200);
  });

  it('cada IP tem o seu balde', async () => {
    const t = relogioControlado();
    const app = criarApp(depsDeTeste({ config, relogio: t.relogio }));
    for (let i = 0; i < 3; i++) await app.request('/api/organizacao');
    expect((await app.request('/api/organizacao')).status).toBe(429);
    expect(
      (await app.request('/api/organizacao', { headers: { 'x-ip-de-teste': '10.0.0.2' } })).status,
    ).toBe(200);
  });

  it('/health fica fora do limite (monitoramento)', async () => {
    const t = relogioControlado();
    const app = criarApp(depsDeTeste({ config, relogio: t.relogio }));
    for (let i = 0; i < 3; i++) await app.request('/api/organizacao');
    expect((await app.request('/api/organizacao')).status).toBe(429);
    for (let i = 0; i < 10; i++) expect((await app.request('/health')).status).toBe(200);
  });

  it('a resposta 429 também leva os cabeçalhos de segurança e o CORS', async () => {
    const t = relogioControlado();
    const app = criarApp(
      depsDeTeste({
        config: { limiteTaxa: { ...config.limiteTaxa, capacidade: 1 } },
        relogio: t.relogio,
      }),
    );
    await app.request('/api/organizacao');
    const r = await app.request('/api/organizacao', {
      headers: { Origin: 'http://localhost:5173' },
    });
    expect(r.status).toBe(429);
    expect(r.headers.get('X-Content-Type-Options')).toBe('nosniff');
    expect(r.headers.get('Access-Control-Allow-Origin')).toBe('http://localhost:5173');
  });

  it('baldes ociosos (cheios de novo) saem na limpeza', () => {
    const t = relogioControlado();
    const limitador = criarLimitador(
      { capacidade: 2, recargaPorSegundo: 1, limpezaACadaMs: 10_000 },
      t.relogio,
    );
    limitador.consumir('a');
    limitador.consumir('b');
    expect(limitador.baldes()).toBe(2);
    t.avancar(10_000);
    limitador.consumir('c');
    expect(limitador.baldes()).toBe(1);
  });
});

describe('timeout', () => {
  it('requisição que passa do limite → 503 tempo_esgotado', async () => {
    const app = criarApp(depsDeTeste({ config: { tempoLimiteMs: 20 } }));
    // rota lenta registrada só no teste, atrás das mesmas proteções de /api
    app.get('/api/lenta', async (c) => {
      await new Promise((r) => setTimeout(r, 200));
      return c.json({ ok: true });
    });
    const r = await app.request('/api/lenta');
    expect(r.status).toBe(503);
    expect(((await r.json()) as { erro: { codigo: string } }).erro.codigo).toBe('tempo_esgotado');
  });

  it('requisição dentro do limite responde normalmente', async () => {
    const app = criarApp(depsDeTeste({ config: { tempoLimiteMs: 500 } }));
    app.get('/api/rapida', async (c) => {
      await new Promise((r) => setTimeout(r, 5));
      return c.json({ ok: true });
    });
    expect((await app.request('/api/rapida')).status).toBe(200);
  });
});

describe('cabeçalhos de segurança', () => {
  it('em /api: nosniff, DENY, no-referrer, CORP, CSP da API e no-store', async () => {
    const app = criarApp(depsDeTeste());
    for (const caminho of ['/api/organizacao', '/api/nada', '/api/pipeline/deals?limite=x']) {
      const h = (await app.request(caminho)).headers;
      expect(h.get('X-Content-Type-Options')).toBe('nosniff');
      expect(h.get('X-Frame-Options')).toBe('DENY');
      expect(h.get('Referrer-Policy')).toBe('no-referrer');
      expect(h.get('Cross-Origin-Resource-Policy')).toBe('same-origin');
      expect(h.get('Content-Security-Policy')).toBe(CSP_API);
      expect(h.get('Cache-Control')).toBe('no-store');
    }
  });

  it('em /health: os mesmos cabeçalhos com a CSP da API', async () => {
    const h = (await criarApp(depsDeTeste()).request('/health')).headers;
    expect(h.get('Content-Security-Policy')).toBe(CSP_API);
    expect(h.get('X-Frame-Options')).toBe('DENY');
  });
});

describe('CORS restrito', () => {
  it('libera a origem da lista, sem credenciais', async () => {
    const app = criarApp(depsDeTeste());
    const r = await app.request('/api/organizacao', {
      headers: { Origin: 'http://localhost:5173' },
    });
    expect(r.headers.get('Access-Control-Allow-Origin')).toBe('http://localhost:5173');
    expect(r.headers.get('Access-Control-Allow-Credentials')).toBeNull();
  });

  it('não libera origem fora da lista', async () => {
    const app = criarApp(depsDeTeste());
    const r = await app.request('/api/organizacao', { headers: { Origin: 'http://evil.example' } });
    expect(r.headers.get('Access-Control-Allow-Origin')).toBeNull();
  });

  it('preflight só com GET e POST', async () => {
    const app = criarApp(depsDeTeste());
    const r = await app.request('/api/priorizacao/fila', {
      method: 'OPTIONS',
      headers: { Origin: 'http://localhost:4173', 'Access-Control-Request-Method': 'POST' },
    });
    expect(r.status).toBe(204);
    expect(r.headers.get('Access-Control-Allow-Origin')).toBe('http://localhost:4173');
    expect(r.headers.get('Access-Control-Allow-Methods')).toBe('GET,POST');
  });
});

describe('config', () => {
  it('padrões: 60 + 2/s, 5 s, 1 MB e as origens do Vite', () => {
    expect(lerConfig({})).toEqual(CONFIG_PADRAO);
    expect(CONFIG_PADRAO.limiteTaxa).toMatchObject({ capacidade: 60, recargaPorSegundo: 2 });
    expect(CONFIG_PADRAO.tempoLimiteMs).toBe(5_000);
    expect(CONFIG_PADRAO.payloadMaxBytes).toBe(1_048_576);
  });

  it('ambiente ajusta; valor inválido não sobe', () => {
    const c = lerConfig({
      RATE_LIMIT_CAPACIDADE: '10',
      TIMEOUT_MS: '2000',
      CORS_ORIGENS: 'http://a.test, http://b.test',
    });
    expect(c.limiteTaxa.capacidade).toBe(10);
    expect(c.tempoLimiteMs).toBe(2000);
    expect(c.corsOrigens).toEqual(['http://a.test', 'http://b.test']);
    expect(() => lerConfig({ TIMEOUT_MS: 'abc' })).toThrow(/TIMEOUT_MS/);
    expect(() => lerConfig({ RATE_LIMIT_CAPACIDADE: '0' })).toThrow();
  });
});
