/** Rotas do contexto `organizacao`: vendedores, managers e regiões para o seletor de perfil e os filtros. */
import { Hono } from 'hono';
import type { ServicosLeadScorer } from '@lead-scorer/dominio/aplicacao';
import { ROTA_ORGANIZACAO } from '@lead-scorer/dominio/organizacao';

/** `GET /api/organizacao`. O perfil escolhido a partir dela não é autenticação. */
export function rotasOrganizacao(servicos: ServicosLeadScorer): Hono {
  const app = new Hono();
  app.get(ROTA_ORGANIZACAO, (c) => c.json(servicos.organizacao()));
  return app;
}
