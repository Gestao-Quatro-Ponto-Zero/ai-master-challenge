/**
 * Rate limit por token bucket, um balde por IP. Protege o cálculo do domínio (a fila de 2.089
 * abertos é recalculada a cada pedido) contra um cliente que dispara sem parar.
 *
 * Limites declarados:
 * - O IP vem do socket (`getConnInfo`), nunca de `X-Forwarded-For`: a API não fica atrás de
 *   proxy, então o cabeçalho seria controlado pelo próprio cliente. Atrás de um proxy, o
 *   limite passaria a valer para o proxy inteiro; aí seria preciso confiar no cabeçalho dele.
 * - Os baldes vivem na memória do processo: com mais de uma instância, cada uma tem o seu.
 */
import type { Context, MiddlewareHandler } from 'hono';
import { responderErro } from './erros';

/** Parâmetros do token bucket. */
export interface ConfigLimiteTaxa {
  /** Pedidos que um IP pode fazer de uma vez (tamanho do balde). */
  capacidade: number;
  /** Fichas devolvidas ao balde por segundo. */
  recargaPorSegundo: number;
  /** De quanto em quanto tempo (ms) os baldes ociosos são descartados. */
  limpezaACadaMs: number;
  /** Teto de baldes na memória (padrão 10 mil); cheio, limpa e, se precisar, descarta o mais antigo. */
  maxBaldes?: number;
}

/** Padrão: 60 pedidos de uma vez, 2 por segundo depois disso, limpeza a cada minuto. */
export const LIMITE_TAXA_PADRAO: ConfigLimiteTaxa = {
  capacidade: 60,
  recargaPorSegundo: 2,
  limpezaACadaMs: 60_000,
  maxBaldes: 10_000,
};

interface Balde {
  fichas: number;
  atualizadoEm: number;
}

/** Resultado de uma tentativa de gastar uma ficha. */
export type Consumo = { permitido: true } | { permitido: false; esperarSegundos: number };

/** Token bucket em memória, com relógio injetável (ms). */
export interface LimitadorDeTaxa {
  consumir(chave: string): Consumo;
  /** Quantos baldes estão na memória (para teste e diagnóstico). */
  baldes(): number;
}

/** Cria o limitador. Um balde cheio há tempo suficiente é ocioso e sai na próxima limpeza. */
export function criarLimitador(config: ConfigLimiteTaxa, relogio: () => number): LimitadorDeTaxa {
  const baldes = new Map<string, Balde>();
  let ultimaLimpeza = relogio();

  const recarregar = (b: Balde, agora: number): void => {
    const decorrido = Math.max(0, agora - b.atualizadoEm) / 1000;
    b.fichas = Math.min(config.capacidade, b.fichas + decorrido * config.recargaPorSegundo);
    b.atualizadoEm = agora;
  };

  const limpar = (agora: number): void => {
    for (const [chave, b] of baldes) {
      recarregar(b, agora);
      if (b.fichas >= config.capacidade) baldes.delete(chave);
    }
    ultimaLimpeza = agora;
  };

  return {
    consumir(chave) {
      const agora = relogio();
      if (agora - ultimaLimpeza >= config.limpezaACadaMs) limpar(agora);
      let b = baldes.get(chave);
      if (!b) {
        const maxBaldes = config.maxBaldes ?? 10_000;
        if (baldes.size >= maxBaldes) {
          limpar(agora);
          const maisAntigo = baldes.keys().next();
          if (baldes.size >= maxBaldes && !maisAntigo.done) baldes.delete(maisAntigo.value);
        }
        b = { fichas: config.capacidade, atualizadoEm: agora };
        baldes.set(chave, b);
      }
      recarregar(b, agora);
      if (b.fichas >= 1) {
        b.fichas -= 1;
        return { permitido: true };
      }
      const faltam = 1 - b.fichas;
      return {
        permitido: false,
        esperarSegundos: Math.max(1, Math.ceil(faltam / config.recargaPorSegundo)),
      };
    },
    baldes: () => baldes.size,
  };
}

/** Middleware: estourou o balde → 429 `limite_de_taxa` com `Retry-After` em segundos (arredondado para cima). */
export function limiteDeTaxa(
  limitador: LimitadorDeTaxa,
  ipDe: (c: Context) => string,
): MiddlewareHandler {
  return async (c, next) => {
    const r = limitador.consumir(ipDe(c));
    if (!r.permitido) {
      c.header('Retry-After', String(r.esperarSegundos));
      return responderErro(c, 429, {
        codigo: 'limite_de_taxa',
        mensagem: 'Muitos pedidos seguidos. Tente de novo em ' + r.esperarSegundos + ' s.',
      });
    }
    await next();
  };
}
