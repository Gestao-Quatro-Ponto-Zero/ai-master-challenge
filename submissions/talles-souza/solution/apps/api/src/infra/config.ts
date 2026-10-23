/**
 * Configuração da borda HTTP. Tudo tem padrão; variável de ambiente só ajusta. Valor inválido
 * não sobe o servidor (melhor falhar na partida do que rodar sem proteção).
 */
import type { Context } from 'hono';
import { getConnInfo } from '@hono/node-server/conninfo';
import { LIMITE_TAXA_PADRAO, type ConfigLimiteTaxa } from './limite-taxa';

/** Parâmetros da borda HTTP. */
export interface ConfigApi {
  limiteTaxa: ConfigLimiteTaxa;
  /** Tempo máximo de uma requisição (ms) antes do 503. */
  tempoLimiteMs: number;
  /** Tamanho máximo do corpo (bytes) antes do 413. */
  payloadMaxBytes: number;
  /** Origens que o CORS libera. */
  corsOrigens: string[];
  /**
   * Valores aceitos no cabeçalho `Host` (contra DNS rebinding); null = não confere. O servidor
   * monta a lista com a própria porta e as origens do CORS.
   */
  hostsPermitidos: string[] | null;
}

/** Padrões: rate limit 60 + 2/s por IP, timeout 5 s, corpo até 1 MB, CORS do Vite (dev 5173, preview 4173). */
export const CONFIG_PADRAO: ConfigApi = {
  limiteTaxa: LIMITE_TAXA_PADRAO,
  tempoLimiteMs: 5_000,
  payloadMaxBytes: 1024 * 1024,
  corsOrigens: ['http://localhost:5173', 'http://localhost:4173'],
  hostsPermitidos: null,
};

/** Os `Host` que este servidor atende: localhost e 127.0.0.1 na porta dele, mais os das origens do CORS. */
export function hostsDoServidor(porta: number, corsOrigens: readonly string[]): string[] {
  const proprios = ['localhost:' + porta, '127.0.0.1:' + porta, '[::1]:' + porta];
  return [...new Set([...proprios, ...corsOrigens.map((o) => new URL(o).host)])];
}

function numero(env: Record<string, string | undefined>, nome: string, padrao: number): number {
  const bruto = env[nome];
  if (bruto === undefined || bruto.trim() === '') return padrao;
  const n = Number(bruto);
  if (!Number.isFinite(n) || n <= 0) throw new Error(nome + ' precisa ser um número positivo');
  return n;
}

/**
 * Lê a configuração do ambiente: `RATE_LIMIT_CAPACIDADE`, `RATE_LIMIT_RECARGA_POR_SEGUNDO`,
 * `TIMEOUT_MS`, `PAYLOAD_MAX_BYTES`, `CORS_ORIGENS` (lista separada por vírgula).
 */
export function lerConfig(env: Record<string, string | undefined>): ConfigApi {
  const origens = env['CORS_ORIGENS'];
  return {
    limiteTaxa: {
      capacidade: numero(env, 'RATE_LIMIT_CAPACIDADE', CONFIG_PADRAO.limiteTaxa.capacidade),
      recargaPorSegundo: numero(
        env,
        'RATE_LIMIT_RECARGA_POR_SEGUNDO',
        CONFIG_PADRAO.limiteTaxa.recargaPorSegundo,
      ),
      limpezaACadaMs: CONFIG_PADRAO.limiteTaxa.limpezaACadaMs,
      maxBaldes: CONFIG_PADRAO.limiteTaxa.maxBaldes,
    },
    tempoLimiteMs: numero(env, 'TIMEOUT_MS', CONFIG_PADRAO.tempoLimiteMs),
    payloadMaxBytes: numero(env, 'PAYLOAD_MAX_BYTES', CONFIG_PADRAO.payloadMaxBytes),
    hostsPermitidos: CONFIG_PADRAO.hostsPermitidos,
    corsOrigens:
      origens === undefined || origens.trim() === ''
        ? [...CONFIG_PADRAO.corsOrigens]
        : origens
            .split(',')
            .map((o) => o.trim())
            .filter((o) => o !== ''),
  };
}

/**
 * IP do cliente pelo socket. Sem socket (pedido feito direto ao app, como nos testes), todos
 * caem no mesmo balde `sem-socket`. Nunca lê `X-Forwarded-For` (ver `limite-taxa.ts`).
 */
export function ipDoSocket(c: Context): string {
  try {
    return getConnInfo(c).remote.address ?? 'sem-endereco';
  } catch {
    return 'sem-socket';
  }
}
