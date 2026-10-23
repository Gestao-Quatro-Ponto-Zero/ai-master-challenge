/** Contrato HTTP do contexto `qualificacao`. */
import { z } from 'zod';
import type { MetodoQualificacao } from './index';

export const ROTA_METODO = '/api/qualificacao/metodo';

/** Schema das respostas guardadas/enviadas (formato versionado). */
export const respostasDoDealSchema = z.strictObject({
  formato: z.literal(1),
  dealId: z.string().min(1).max(40),
  metodoId: z.string().min(1).max(80),
  respostas: z
    .array(
      z.strictObject({
        perguntaId: z.string().min(1).max(80),
        valor: z.enum(['sim', 'nao']),
        respondidoEm: z.iso.datetime({ offset: true }),
      }),
    )
    .max(50),
  decisao: z
    .strictObject({
      acao: z.enum(['avancar_hoje', 'manter_ritmo', 'qualificar', 'encaminhar_para_nutricao']),
      aceita: z.boolean(),
      motivo: z.string().trim().min(3).max(280).nullable(),
      em: z.iso.datetime({ offset: true }),
    })
    .nullable(),
});

export type RespostaMetodo = MetodoQualificacao;

/** `GET`: as respostas e decisões guardadas no servidor (query: vendedor, manager, região). */
export const ROTA_REGISTROS = '/api/qualificacao/registros';
/** `POST`: grava uma resposta do vendedor. */
export const ROTA_RESPONDER = '/api/qualificacao/responder';
/** `POST`: grava a decisão do vendedor sobre a ação sugerida. */
export const ROTA_DECIDIR = '/api/qualificacao/decidir';
/** `POST`: grava a mesma decisão para vários negócios ("Encaminhar os N"). */
export const ROTA_DECIDIR_LOTE = '/api/qualificacao/decidir-lote';

const idNegocio = z.string().regex(/^[A-Z0-9]{8}$/);
const acaoSchema = z.enum([
  'avancar_hoje',
  'manter_ritmo',
  'qualificar',
  'encaminhar_para_nutricao',
]);
const motivoSchema = z.string().trim().max(280).nullable().optional();

export const pedidoResponderSchema = z.strictObject({
  dealId: idNegocio,
  perguntaId: z.string().min(1).max(80),
  valor: z.enum(['sim', 'nao']),
});
export type PedidoResponder = z.infer<typeof pedidoResponderSchema>;

export const pedidoDecidirSchema = z.strictObject({
  dealId: idNegocio,
  acao: acaoSchema,
  aceita: z.boolean(),
  motivo: motivoSchema,
});
export type PedidoDecidir = z.infer<typeof pedidoDecidirSchema>;

export const pedidoDecidirLoteSchema = z.strictObject({
  dealIds: z.array(idNegocio).min(1).max(2500),
  acao: acaoSchema,
  aceita: z.boolean(),
  motivo: motivoSchema,
});
export type PedidoDecidirLote = z.infer<typeof pedidoDecidirLoteSchema>;

/** Onde as respostas ficam no servidor: no banco compartilhado ou só na memória do processo. */
export type Armazenamento = 'banco' | 'memoria';

export interface RespostaRegistros {
  armazenamento: Armazenamento;
  registros: z.infer<typeof respostasDoDealSchema>[];
}

export interface RespostaLote {
  armazenamento: Armazenamento;
  /** Quantas linhas foram gravadas (uma por negócio). */
  registros: number;
  /** A data comum a todas (ISO 8601). */
  em: string;
}
