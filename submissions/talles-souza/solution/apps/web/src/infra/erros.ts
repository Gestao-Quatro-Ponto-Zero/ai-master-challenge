/** Erros do cliente, com a informação de que o retry, o disjuntor e o modo local precisam. */

/**
 * - `rede`: a requisição não chegou (fetch rejeitou).
 * - `timeout`: passou do tempo e foi abortada.
 * - `http`: a API respondeu com erro (o `status` diz qual).
 * - `circuito_aberto`: o disjuntor recusou sem tentar.
 * - `dados`: o modo local não conseguiu carregar ou conferir o `deals.json`.
 */
export type TipoErroCliente = 'rede' | 'timeout' | 'http' | 'circuito_aberto' | 'dados';

export class ErroCliente extends Error {
  override readonly name = 'ErroCliente';
  constructor(
    readonly tipo: TipoErroCliente,
    mensagem: string,
    readonly extra: {
      status?: number;
      /** Código estável do corpo `RespostaErro`, quando a API mandou um. */
      codigo?: string;
      /** `Retry-After` convertido para milissegundos. */
      retryAfterMs?: number;
    } = {},
  ) {
    super(mensagem);
  }

  /** Falha que pode passar sozinha: rede, timeout, 502/503/504 e 429. Erro de entrada (4xx) nunca é. */
  get transitorio(): boolean {
    if (this.tipo === 'rede' || this.tipo === 'timeout') return true;
    if (this.tipo !== 'http') return false;
    const s = this.extra.status ?? 0;
    return s === 429 || s === 502 || s === 503 || s === 504;
  }

  /**
   * A API não está servindo: falha transitória ou erro do próprio servidor (5xx). Conta para o
   * disjuntor e manda para o modo local; só o `transitorio` é repetido pelo retry.
   */
  get falhaDoServidor(): boolean {
    return this.transitorio || (this.tipo === 'http' && (this.extra.status ?? 0) >= 500);
  }
}

/** Garante um `ErroCliente` (o que vier de fora vira `rede`). */
export function comoErroCliente(e: unknown): ErroCliente {
  if (e instanceof ErroCliente) return e;
  return new ErroCliente('rede', e instanceof Error ? e.message : String(e));
}
