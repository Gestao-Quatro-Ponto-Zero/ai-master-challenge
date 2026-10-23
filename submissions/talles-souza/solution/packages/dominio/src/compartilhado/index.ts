/** Erro de domínio, com código estável para a API e mensagem para gente. */
export interface ErroDominio {
  codigo: string;
  mensagem: string;
  detalhes?: unknown;
}

/** Resultado de uma operação que pode falhar sem lançar exceção. */
export type Resultado<T, E = ErroDominio> = { ok: true; valor: T } | { ok: false; erro: E };

/** Embrulha um valor de sucesso. */
export function ok<T>(valor: T): Resultado<T, never> {
  return { ok: true, valor };
}

/** Embrulha uma falha de domínio. */
export function falha(codigo: string, mensagem: string, detalhes?: unknown): Resultado<never> {
  return {
    ok: false,
    erro: detalhes === undefined ? { codigo, mensagem } : { codigo, mensagem, detalhes },
  };
}

/** Corpo de toda resposta HTTP de erro (400, 404, 413, 429, 500, 503). */
export interface RespostaErro {
  erro: ErroDominio;
}

/** Erro levantado por um contrato ainda não implementado (só existe durante a Onda 0). */
export function naoImplementado(nome: string): never {
  throw new Error('não implementado: ' + nome);
}
