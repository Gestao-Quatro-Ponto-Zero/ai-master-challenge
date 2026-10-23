/**
 * Serve a web construída (`apps/web/dist`) pelo mesmo processo da API, para que `npm start`
 * entregue app + API numa porta só. A raiz `/` abre a segunda-feira do vendedor (`index.html`);
 * caminho sem extensão que não é arquivo cai no `index.html` (o roteador da web é por hash, mas
 * um link colado com caminho também abre o app). `/dados/deals.json` sai daqui para o modo local.
 */
import type { Hono } from 'hono';
import { serveStatic } from '@hono/node-server/serve-static';
import { join } from 'node:path';
import { ehCaminhoDaApi } from './seguranca';

const TEM_EXTENSAO = /\.[a-z0-9]+$/i;

/** Monta estáticos e o fallback da SPA. Nunca responde por `/api` nem `/health`. */
export function montarWeb(app: Hono, raiz: string): void {
  const estaticos = serveStatic({ root: raiz });
  const indice = serveStatic({ path: join(raiz, 'index.html') });
  app.use('*', async (c, next) => (ehCaminhoDaApi(c.req.path) ? next() : estaticos(c, next)));
  app.get('*', async (c, next) => {
    if (ehCaminhoDaApi(c.req.path) || TEM_EXTENSAO.test(c.req.path)) return next();
    return indice(c, next);
  });
}
