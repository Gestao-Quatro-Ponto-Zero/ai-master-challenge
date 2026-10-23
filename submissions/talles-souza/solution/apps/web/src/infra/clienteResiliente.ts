/**
 * Cliente que a tela usa: tenta a API (com timeout, retry e disjuntor); se a API não responde
 * depois dos retries ou o circuito está aberto, responde pelo modo local, com os mesmos casos de
 * uso. O `modo` é observável (o banner "modo local" lê daí); quando a API volta, volta a `api`.
 */
import { OPERACOES, type ClienteLeadScorer } from './cliente';
import type { ClienteHttp } from './clienteHttp';
import { comoErroCliente, type ErroCliente } from './erros';

export type Modo = 'api' | 'local';

export interface ClienteResiliente extends ClienteLeadScorer {
  modo(): Modo;
  /** Avisa a cada troca de modo; devolve a função que cancela. */
  assinar(ouvinte: (modo: Modo) => void): () => void;
  /** Pergunta a saúde da API; se respondeu, o modo volta a `api`. */
  sondar(): Promise<Modo>;
}

/** Falhas que mandam para o modo local: a API sumiu ou quebrou (5xx), não o pedido que veio errado. */
function deveCairParaLocal(e: ErroCliente): boolean {
  return e.tipo === 'circuito_aberto' || e.falhaDoServidor;
}

/**
 * A API está de pé mas não conhece a rota (404 `nao_encontrado`: API mais antiga que a web).
 * Responde pelo local sem trocar o modo, porque a conexão está boa.
 */
function rotaAusente(e: ErroCliente): boolean {
  return e.tipo === 'http' && e.extra.status === 404 && e.extra.codigo === 'nao_encontrado';
}

/** Cria o cliente resiliente. */
export function criarClienteResiliente(
  http: ClienteHttp,
  local: ClienteLeadScorer,
): ClienteResiliente {
  let modo: Modo = 'api';
  const ouvintes = new Set<(m: Modo) => void>();
  // Ordem das chamadas: só um sucesso que começou depois da última queda volta ao modo `api`
  // (senão uma resposta atrasada, de antes da queda, faria o banner piscar).
  let seq = 0;
  let ultimaQueda = 0;

  function trocar(novo: Modo): void {
    if (novo === modo) return;
    modo = novo;
    for (const o of ouvintes) o(novo);
  }

  const cliente = {
    modo: () => modo,
    assinar(ouvinte: (m: Modo) => void) {
      ouvintes.add(ouvinte);
      return () => {
        ouvintes.delete(ouvinte);
      };
    },
    async sondar() {
      const minha = ++seq;
      try {
        await http.saude();
        if (minha > ultimaQueda) trocar('api');
      } catch {
        // continua no modo em que estava
      }
      return modo;
    },
  } as ClienteResiliente;

  for (const op of OPERACOES) {
    (cliente as unknown as Record<string, (...a: unknown[]) => Promise<unknown>>)[op] = async (
      ...args
    ) => {
      const minha = ++seq;
      try {
        const valor = await (http[op] as (...a: unknown[]) => Promise<unknown>)(...args);
        if (minha > ultimaQueda) trocar('api');
        return valor;
      } catch (bruto) {
        const erro = comoErroCliente(bruto);
        const pelaRota = rotaAusente(erro);
        if (!pelaRota && !deveCairParaLocal(erro)) throw erro;
        if (!pelaRota) {
          ultimaQueda = Math.max(ultimaQueda, minha);
          trocar('local');
        }
        return (local[op] as (...a: unknown[]) => Promise<unknown>)(...args);
      }
    };
  }
  return cliente;
}
