/** A web construída servida pela API: estáticos, fallback da SPA, CSP da web e a API intacta. */
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { criarApp } from '../src/app';
import { CSP_API, CSP_WEB } from '../src/infra/seguranca';
import { depsDeTeste } from './falsos';

let raiz = '';

beforeAll(() => {
  raiz = mkdtempSync(join(tmpdir(), 'lead-scorer-web-'));
  writeFileSync(join(raiz, 'index.html'), '<!doctype html><title>Lead Scorer</title>');
  mkdirSync(join(raiz, 'assets'));
  writeFileSync(join(raiz, 'assets', 'app.js'), 'console.log(1)');
  mkdirSync(join(raiz, 'dados'));
  writeFileSync(join(raiz, 'dados', 'deals.json'), '{"formato":1}');
});

afterAll(() => {
  rmSync(raiz, { recursive: true, force: true });
});

function app() {
  return criarApp({ ...depsDeTeste(), web: { raiz } });
}

describe('web servida pela API', () => {
  it('/ abre o index.html com a CSP da web', async () => {
    const r = await app().request('/');
    expect(r.status).toBe(200);
    expect(await r.text()).toContain('Lead Scorer');
    expect(r.headers.get('Content-Security-Policy')).toBe(CSP_WEB);
    expect(r.headers.get('X-Frame-Options')).toBe('DENY');
    expect(r.headers.get('Cache-Control')).toBeNull();
  });

  it('estáticos e /dados/deals.json saem com o tipo certo', async () => {
    const js = await app().request('/assets/app.js');
    expect(js.status).toBe(200);
    expect(js.headers.get('Content-Type')).toMatch(/javascript/);
    const dados = await app().request('/dados/deals.json');
    expect(dados.status).toBe(200);
    expect(await dados.json()).toEqual({ formato: 1 });
  });

  it('caminho sem extensão cai no index.html; arquivo que falta dá 404', async () => {
    expect(await (await app().request('/manager')).text()).toContain('Lead Scorer');
    expect((await app().request('/assets/nao-existe.js')).status).toBe(404);
  });

  it('não serve fora da pasta', async () => {
    expect((await app().request('/../package.json')).status).toBe(404);
  });

  it('a API continua respondendo como API', async () => {
    const r = await app().request('/api/organizacao');
    expect(r.status).toBe(200);
    expect(r.headers.get('Content-Security-Policy')).toBe(CSP_API);
    const inexistente = await app().request('/api/nada');
    expect(inexistente.status).toBe(404);
    expect(((await inexistente.json()) as { erro: { codigo: string } }).erro.codigo).toBe(
      'nao_encontrado',
    );
  });
});
