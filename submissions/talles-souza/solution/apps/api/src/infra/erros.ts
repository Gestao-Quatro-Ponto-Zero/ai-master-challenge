/**
 * Erros na fronteira HTTP. Todo erro sai no formato `RespostaErro` do domínio
 * (`{ erro: { codigo, mensagem, detalhes? } }`), sem eco do valor recebido e sem stack.
 */
import type { Context } from 'hono';
import type { ContentfulStatusCode } from 'hono/utils/http-status';
import type { ZodType } from 'zod';
import type { ErroDominio, RespostaErro } from '@lead-scorer/dominio/compartilhado';

/** Erro com status HTTP; o `onError` do app o transforma em `RespostaErro`. */
export class ErroHttp extends Error {
  constructor(
    readonly status: ContentfulStatusCode,
    readonly erro: ErroDominio,
  ) {
    super(erro.mensagem);
    this.name = 'ErroHttp';
  }
}

/** Status HTTP de cada código de erro do domínio. Código desconhecido é tratado como entrada recusada (400). */
const STATUS_DO_CODIGO: Record<string, ContentfulStatusCode> = {
  deal_nao_encontrado: 404,
  lead_invalido: 400,
  respostas_invalidas: 400,
  motivo_obrigatorio: 400,
  pergunta_inexistente: 400,
  lote_vazio: 400,
  lote_repetido: 400,
};

/** Converte uma falha de domínio (`Resultado` com `ok: false`) em `ErroHttp`. */
export function erroDoDominio(erro: ErroDominio): ErroHttp {
  return new ErroHttp(STATUS_DO_CODIGO[erro.codigo] ?? 400, erro);
}

/** Responde com o corpo de erro padrão. */
export function responderErro(
  c: Context,
  status: ContentfulStatusCode,
  erro: ErroDominio,
): Response {
  const corpo: RespostaErro = { erro };
  return c.json(corpo, status);
}

/**
 * Valida `dados` contra o schema zod do contrato. Inválido → 400 `entrada_invalida`, com o
 * caminho e a mensagem de cada problema (a mensagem do zod descreve o tipo esperado, não o valor).
 */
export function validar<T>(schema: ZodType<T>, dados: unknown): T {
  const r = schema.safeParse(dados);
  if (r.success) return r.data;
  throw new ErroHttp(400, {
    codigo: 'entrada_invalida',
    mensagem: 'A entrada não segue o contrato.',
    detalhes: r.error.issues.map((i) => ({
      caminho: i.path.map(String).join('.'),
      mensagem: i.message,
    })),
  });
}

/** Lê o corpo como JSON; corpo vazio ou malformado → 400 `entrada_invalida`. */
export async function lerJson(c: Context): Promise<unknown> {
  // sem application/json, um POST de outra origem seria "simples" (sem preflight do CORS)
  if (!(c.req.header('content-type') ?? '').toLowerCase().includes('application/json')) {
    throw new ErroHttp(415, {
      codigo: 'tipo_nao_suportado',
      mensagem: 'Envie o corpo como application/json.',
    });
  }
  const texto = await c.req.text();
  try {
    return JSON.parse(texto) as unknown;
  } catch {
    throw new ErroHttp(400, {
      codigo: 'entrada_invalida',
      mensagem: 'O corpo não é um JSON válido.',
    });
  }
}
