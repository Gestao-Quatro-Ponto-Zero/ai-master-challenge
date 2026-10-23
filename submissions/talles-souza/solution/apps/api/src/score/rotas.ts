/**
 * Rotas do contexto `score`: os fatos explicados de um deal ou de um lead novo, a chance
 * histórica por faixa de idade, a tabela de pontos e o motor de pontos medidos no histórico.
 */
import { Hono } from 'hono';
import type { ServicosLeadScorer } from '@lead-scorer/dominio/aplicacao';
import {
  pedidoAvaliacaoSchema,
  ROTA_AVALIAR,
  ROTA_CHANCE,
  ROTA_MOTOR,
  ROTA_PONTOS,
} from '@lead-scorer/dominio/score';
import { erroDoDominio, lerJson, validar } from '../infra/erros';

/** `POST /api/score/avaliar`, `GET /api/score/chance`, `GET /api/score/pontos` e `GET /api/score/motor`. */
export function rotasScore(servicos: ServicosLeadScorer): Hono {
  const app = new Hono();
  app.get(ROTA_CHANCE, (c) => c.json(servicos.chance()));
  app.get(ROTA_PONTOS, (c) => c.json(servicos.pontos()));
  app.get(ROTA_MOTOR, (c) => c.json(servicos.motor()));
  app.post(ROTA_AVALIAR, async (c) => {
    const pedido = validar(pedidoAvaliacaoSchema, await lerJson(c));
    const r = servicos.avaliar(pedido);
    if (!r.ok) throw erroDoDominio(r.erro);
    return c.json(r.valor);
  });
  return app;
}
