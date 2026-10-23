/**
 * Borda HTTP: o `Host` precisa ser deste servidor (DNS rebinding), o corpo precisa ser JSON
 * (POST de outra origem sem preflight) e os baldes do rate limit têm teto na memória.
 */
import { describe, expect, it } from 'vitest';
import { criarApp } from '../src/app';
import { hostsDoServidor } from '../src/infra/config';
import { criarLimitador } from '../src/infra/limite-taxa';
import { depsDeTeste } from './falsos';

describe('Host', () => {
  const app = criarApp(depsDeTeste({ config: { hostsPermitidos: hostsDoServidor(8787, []) } }));

  it('atende pelo próprio endereço', async () => {
    const r = await app.request('/health', { headers: { host: '127.0.0.1:8787' } });
    expect(r.status).toBe(200);
  });

  it('recusa com 421 um Host de fora', async () => {
    const r = await app.request('/api/organizacao', { headers: { host: 'atacante.exemplo:8787' } });
    expect(r.status).toBe(421);
    expect(await r.json()).toMatchObject({ erro: { codigo: 'host_invalido' } });
  });

  it('a lista inclui as origens do CORS (o proxy do Vite repassa o Host dele)', () => {
    expect(hostsDoServidor(8787, ['http://localhost:5173'])).toContain('localhost:5173');
  });
});

describe('corpo', () => {
  it('POST sem application/json recebe 415', async () => {
    const app = criarApp(depsDeTeste());
    const r = await app.request('/api/priorizacao/fila', {
      method: 'POST',
      headers: { 'content-type': 'text/plain' },
      body: JSON.stringify({ filtro: {} }),
    });
    expect(r.status).toBe(415);
    expect(await r.json()).toMatchObject({ erro: { codigo: 'tipo_nao_suportado' } });
  });
});

describe('rate limit', () => {
  it('a memória dos baldes tem teto', () => {
    const l = criarLimitador(
      { capacidade: 1, recargaPorSegundo: 0, limpezaACadaMs: 1e9, maxBaldes: 2 },
      () => 0,
    );
    for (const ip of ['10.0.0.1', '10.0.0.2', '10.0.0.3', '10.0.0.4']) l.consumir(ip);
    expect(l.baldes()).toBeLessThanOrEqual(2);
  });
});
