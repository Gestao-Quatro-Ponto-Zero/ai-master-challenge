/** Contrato HTTP do contexto `pipeline`. Respostas = tipos do domínio serializados em JSON. */
import { z } from 'zod';
import type { Conta, Deal, Janela, Lacuna, Produto } from './index';

export const ROTA_RESUMO = '/api/pipeline/resumo';
export const ROTA_DEALS = '/api/pipeline/deals';
/** `GET` de um deal pelo `opportunity_id`. */
export function rotaDeal(id: string): string {
  return ROTA_DEALS + '/' + encodeURIComponent(id);
}

const texto = z.string().trim().min(1).max(80);

/** Query string de `GET /api/pipeline/deals`. */
export const consultaDealsSchema = z.strictObject({
  vendedor: texto.optional(),
  manager: texto.optional(),
  regiao: texto.optional(),
  estagio: z.enum(['Prospecting', 'Engaging', 'Won', 'Lost']).optional(),
  aberto: z.enum(['true', 'false']).optional(),
  limite: z.coerce.number().int().min(1).max(2500).default(500),
  deslocamento: z.coerce.number().int().min(0).default(0),
});
export type ConsultaDeals = z.infer<typeof consultaDealsSchema>;

/** Id de deal na rota. */
export const idDealSchema = z.string().regex(/^[A-Z0-9]{8}$/);

/** Corpo do lead novo (tela "Novo lead"). */
export const novoLeadSchema = z.strictObject({
  vendedor: texto,
  produto: texto,
  conta: texto.optional(),
  dataEngajamento: z.iso.date().optional(),
});

export interface RespostaResumo {
  formato: number;
  referencia: string;
  total: number;
  abertos: number;
  janela: Janela;
  lacunas: Record<Lacuna, number>;
  catalogo: Produto[];
  contas: Conta[];
  /** SHA-256 conferido do `deals.json` carregado. */
  checksum: string;
}

export interface RespostaDeals {
  total: number;
  limite: number;
  deslocamento: number;
  deals: Deal[];
}
