/** Contrato HTTP do contexto `priorizacao`. */
import { z } from 'zod';
import { filtroSchema } from '../organizacao';
import { idDealSchema, novoLeadSchema } from '../pipeline';
import { respostasDoDealSchema } from '../qualificacao';
import type { Fila, ItemFila, Painel, PoliticaPriorizacao } from './index';

export const ROTA_FILA = '/api/priorizacao/fila';
export const ROTA_ITEM = '/api/priorizacao/item';
export const ROTA_POLITICA = '/api/priorizacao/politica';
/** `POST`: o painel "Acompanhar a equipe" (4 métricas e a linha de cada vendedor) de um filtro; mesmo corpo da fila. */
export const ROTA_PAINEL = '/api/priorizacao/painel';

/** A segunda-feira de um filtro, com as respostas que o vendedor guardou no navegador. */
export const pedidoFilaSchema = z.strictObject({
  filtro: filtroSchema,
  respostas: z.array(respostasDoDealSchema).max(2500).default([]),
});
export type PedidoFila = z.infer<typeof pedidoFilaSchema>;

/** Um deal (ou lead novo) classificado, com as respostas dele. */
export const pedidoItemSchema = z.union([
  z.strictObject({ dealId: idDealSchema, respostas: respostasDoDealSchema.nullable().optional() }),
  z.strictObject({ lead: novoLeadSchema, respostas: respostasDoDealSchema.nullable().optional() }),
]);
export type PedidoItem = z.infer<typeof pedidoItemSchema>;

export type RespostaFila = Fila;
export type RespostaItem = ItemFila;
export type RespostaPolitica = PoliticaPriorizacao;
export type RespostaPainel = Painel;
