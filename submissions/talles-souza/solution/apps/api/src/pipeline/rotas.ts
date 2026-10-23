/** Rotas do contexto `pipeline`: resumo do dataset, lista de deals com filtro e um deal pelo id. */
import { Hono } from 'hono';
import { z } from 'zod';
import type { ServicosLeadScorer } from '@lead-scorer/dominio/aplicacao';
import {
  consultaDealsSchema,
  idDealSchema,
  ROTA_DEALS,
  ROTA_RESUMO,
} from '@lead-scorer/dominio/pipeline';
import { ErroHttp, validar } from '../infra/erros';

const parametroIdSchema = z.strictObject({ id: idDealSchema });

/** `GET /api/pipeline/resumo`, `GET /api/pipeline/deals` e `GET /api/pipeline/deals/:id`. */
export function rotasPipeline(servicos: ServicosLeadScorer): Hono {
  const app = new Hono();
  app.get(ROTA_RESUMO, (c) => c.json(servicos.resumo()));
  app.get(ROTA_DEALS, (c) => c.json(servicos.deals(validar(consultaDealsSchema, c.req.query()))));
  app.get(ROTA_DEALS + '/:id', (c) => {
    const { id } = validar(parametroIdSchema, { id: c.req.param('id') });
    const deal = servicos.deal(id);
    if (!deal)
      throw new ErroHttp(404, {
        codigo: 'deal_nao_encontrado',
        mensagem: 'Nenhum deal com esse id.',
      });
    return c.json(deal);
  });
  return app;
}
