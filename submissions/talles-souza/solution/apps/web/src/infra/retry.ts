/**
 * Retry com backoff exponencial e full jitter: a espera depois da falha n é sorteada entre 0 e
 * min(teto, base · 2ⁿ). Só repete erro transitório e só em operação idempotente.
 */
import { comoErroCliente } from './erros';
import { aleatorioDoSistema, dormirDeVerdade, type Aleatorio, type Dormir } from './tempo';

export interface OpcoesRetry {
  /** Total de tentativas, contando a primeira. */
  tentativas: number;
  baseMs: number;
  tetoMs: number;
}

export const RETRY_PADRAO: OpcoesRetry = { tentativas: 3, baseMs: 200, tetoMs: 2000 };

/** Espera antes da próxima tentativa, depois da falha número `falha` (0 = a primeira). */
export function esperaComJitter(falha: number, opcoes: OpcoesRetry, aleatorio: Aleatorio): number {
  const limite = Math.min(opcoes.tetoMs, opcoes.baseMs * 2 ** falha);
  return Math.floor(aleatorio() * limite);
}

export interface ContextoRetry {
  /** Operação que pode repetir sem efeito colateral. Sem isso, nunca repete. */
  idempotente: boolean;
  opcoes?: OpcoesRetry;
  dormir?: Dormir;
  aleatorio?: Aleatorio;
}

/**
 * Executa `op` com retry. Um 429 com `Retry-After` espera o que a API pediu, se couber no teto;
 * se não couber, desiste na hora (esperar mais que o teto não ajuda o vendedor).
 */
export async function comRetry<T>(op: () => Promise<T>, ctx: ContextoRetry): Promise<T> {
  const opcoes = ctx.opcoes ?? RETRY_PADRAO;
  const dormir = ctx.dormir ?? dormirDeVerdade;
  const aleatorio = ctx.aleatorio ?? aleatorioDoSistema;
  for (let falha = 0; ; falha++) {
    try {
      return await op();
    } catch (bruto) {
      const erro = comoErroCliente(bruto);
      const ultima = falha + 1 >= opcoes.tentativas;
      if (!ctx.idempotente || !erro.transitorio || ultima) throw erro;
      const pedido = erro.extra.retryAfterMs;
      if (pedido !== undefined && pedido > opcoes.tetoMs) throw erro;
      await dormir(pedido ?? esperaComJitter(falha, opcoes, aleatorio));
    }
  }
}
