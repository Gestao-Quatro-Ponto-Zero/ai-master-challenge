/** Contrato HTTP do contexto `organizacao`. */
import { z } from 'zod';
import type { Organizacao } from './index';

export const ROTA_ORGANIZACAO = '/api/organizacao';

const texto = z.string().trim().min(1).max(80);

/** Filtro por vendedor/manager/região, usado no corpo da fila. */
export const filtroSchema = z.strictObject({
  vendedor: texto.optional(),
  manager: texto.optional(),
  regiao: texto.optional(),
});

export type RespostaOrganizacao = Organizacao;
