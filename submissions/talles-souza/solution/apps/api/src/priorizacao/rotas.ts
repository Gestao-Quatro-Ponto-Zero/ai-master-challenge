/**
 * Rotas do contexto `priorizacao`: a segunda-feira do vendedor (fila em blocos), um deal ou lead
 * classificado e a política em uso. As respostas que o vendedor guardou no navegador vêm no corpo.
 */
import { Hono } from 'hono';
import type { ServicosLeadScorer } from '@lead-scorer/dominio/aplicacao';
import {
  pedidoFilaSchema,
  pedidoItemSchema,
  ROTA_FILA,
  ROTA_ITEM,
  ROTA_PAINEL,
  ROTA_POLITICA,
} from '@lead-scorer/dominio/priorizacao';
import { erroDoDominio, lerJson, validar } from '../infra/erros';

/**
 * `POST /api/priorizacao/fila`, `POST /api/priorizacao/item`, `POST /api/priorizacao/painel` e
 * `GET /api/priorizacao/politica`.
 */
export function rotasPriorizacao(servicos: ServicosLeadScorer): Hono {
  const app = new Hono();
  app.post(ROTA_FILA, async (c) => {
    const pedido = validar(pedidoFilaSchema, await lerJson(c));
    const r = servicos.fila(pedido);
    if (!r.ok) throw erroDoDominio(r.erro);
    return c.json(r.valor);
  });
  app.post(ROTA_ITEM, async (c) => {
    const pedido = validar(pedidoItemSchema, await lerJson(c));
    const r = servicos.item(pedido);
    if (!r.ok) throw erroDoDominio(r.erro);
    return c.json(r.valor);
  });
  app.post(ROTA_PAINEL, async (c) => {
    const pedido = validar(pedidoFilaSchema, await lerJson(c));
    const r = servicos.painel(pedido);
    if (!r.ok) throw erroDoDominio(r.erro);
    return c.json(r.valor);
  });
  app.get(ROTA_POLITICA, (c) => c.json(servicos.politica()));
  return app;
}
