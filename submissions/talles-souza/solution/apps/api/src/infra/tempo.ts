/**
 * Timeout por requisição e log de uma linha.
 *
 * Limite declarado do timeout: ele corta o que espera (I/O, promessas). O cálculo do domínio é
 * síncrono e o Node não interrompe código síncrono no meio; um cálculo que trave segura o
 * processo até terminar. O cálculo mais pesado (a fila inteira) é medido nos testes de integração.
 */
import type { MiddlewareHandler } from 'hono';
import { responderErro } from './erros';

/** Requisição que passa de `ms` → 503 `tempo_esgotado`. */
export function tempoLimite(ms: number): MiddlewareHandler {
  return async (c, next) => {
    let timer: ReturnType<typeof setTimeout> | undefined;
    const esgotou = new Promise<'esgotou'>((resolve) => {
      timer = setTimeout(() => resolve('esgotou'), ms);
    });
    try {
      const r = await Promise.race([next().then(() => 'ok' as const), esgotou]);
      if (r === 'esgotou') {
        return responderErro(c, 503, {
          codigo: 'tempo_esgotado',
          mensagem: 'A resposta passou de ' + ms + ' ms. Tente de novo.',
        });
      }
    } finally {
      clearTimeout(timer);
    }
  };
}

/** Uma linha por requisição: método, caminho (sem query), status e duração. Nunca o corpo. */
export function logDeRequisicao(
  log: (linha: string) => void,
  relogio: () => number,
): MiddlewareHandler {
  return async (c, next) => {
    const inicio = relogio();
    await next();
    log(
      c.req.method +
        ' ' +
        c.req.path +
        ' ' +
        c.res.status +
        ' ' +
        Math.round(relogio() - inicio) +
        'ms',
    );
  };
}
