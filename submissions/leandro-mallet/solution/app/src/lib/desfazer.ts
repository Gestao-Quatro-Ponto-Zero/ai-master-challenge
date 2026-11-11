// Formato do token do "Desfazer". O token é conferido antes de qualquer chamada ao banco.
import { z } from "zod";

const UUID = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}";
const NUMERO = "(?:0|[1-9][0-9]{0,14})";
const DEAL = "[A-Z0-9]{8}";

const FORMATOS = [
  new RegExp(`^deal:${UUID}$`), // mudança num deal: o correlation_id da escrita original
  new RegExp(`^(acao|comentario|lote):${NUMERO}$`),
  new RegExp(`^(tagmais|tagmenos):${DEAL}:${NUMERO}$`),
  new RegExp(`^d${NUMERO}$`), // reserva em memória
];

export function tokenDesfazerValido(token: string): boolean {
  return token.length <= 80 && FORMATOS.some((f) => f.test(token));
}

export const corpoDesfazer = z.object({ token: z.string().min(2).max(80).refine(tokenDesfazerValido) });
