/**
 * Entrada da API como função serverless da Vercel (deploy A: web estática + esta função). O
 * `scripts/construir-vercel.mjs` empacota este arquivo num só (`index.mjs`) dentro da saída do
 * build (`.vercel/output/functions/api.func/`), com o `deals.json` e o `.sha256` ao lado, em
 * `data/`. O app é o mesmo do `npm start` (`criarApp`); muda só a borda:
 * - o export default é o app Hono no adaptador de Node do Hono (`getRequestListener`): o handler
 *   `(req, res)` das funções Node da Vercel;
 * - os estáticos saem da CDN da Vercel, não do `serveStatic` (que continua no `npm start`);
 * - o IP do rate limit vem de `x-real-ip`, que a borda da Vercel preenche (o socket é o proxy).
 * Ambiente: `DATABASE_URL` (o banco compartilhado; sem ela, `deals.json` + memória) e os da borda
 * em `infra/config.ts`. Dado que não confere: a função falha na partida e a web cai para o modo
 * local, com o aviso de sempre.
 */
import { getRequestListener } from '@hono/node-server';
import type { Context } from 'hono';
import { fileURLToPath } from 'node:url';
import { criarApp } from './app';
import { montarDependencias } from './carregador';
import { lerConfig } from './infra/config';

/** O IP do cliente na Vercel: a borda dela preenche `x-real-ip` (o socket é o proxy). */
export function ipDaVercel(c: Context): string {
  return c.req.header('x-real-ip')?.trim() || 'sem-ip';
}

const caminho =
  process.env['DEALS_PATH'] ?? fileURLToPath(new URL('./data/deals.json', import.meta.url));
const carga = await montarDependencias(process.env, caminho, (linha) => console.warn(linha));
if (!carga.ok) {
  throw new Error('A função não subiu: ' + carga.erro.codigo + ': ' + carga.erro.mensagem);
}

const app = criarApp({
  servicos: carga.valor.servicos,
  registros: carga.valor.registros,
  saude: {
    versao: process.env['VERCEL_GIT_COMMIT_SHA']?.slice(0, 7) ?? 'vercel',
    iniciadoEm: new Date().toISOString(),
    dados: carga.valor.dados,
  },
  config: lerConfig(process.env),
  ipDe: ipDaVercel,
});

export default getRequestListener(app.fetch);
