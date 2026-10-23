/**
 * Circuit breaker: 3 falhas seguidas do servidor (rede, timeout, 429, 5xx) abrem o circuito;
 * aberto, recusa na hora por 15 s; depois deixa passar 1 sonda (meio-aberto): sucesso fecha,
 * falha reabre. Erro de entrada (4xx) não conta como falha: a API está de pé. Resultado de
 * requisição que começou antes da última troca de estado não mexe no estado.
 */
import { ErroCliente, comoErroCliente } from './erros';
import { relogioDoSistema, type Relogio } from './tempo';

export type EstadoDisjuntor = 'fechado' | 'aberto' | 'meio_aberto';

export interface OpcoesDisjuntor {
  falhasParaAbrir: number;
  abertoMs: number;
}

export const DISJUNTOR_PADRAO: OpcoesDisjuntor = { falhasParaAbrir: 3, abertoMs: 15_000 };

export interface Disjuntor {
  /** Estado agora (o aberto vencido já aparece como meio-aberto). */
  estado(): EstadoDisjuntor;
  /** Executa `op` se o circuito deixar; senão lança `ErroCliente('circuito_aberto')`. */
  executar<T>(op: () => Promise<T>): Promise<T>;
}

/** Cria um disjuntor com relógio injetável. */
export function criarDisjuntor(
  opcoes: OpcoesDisjuntor = DISJUNTOR_PADRAO,
  relogio: Relogio = relogioDoSistema,
): Disjuntor {
  let estado: EstadoDisjuntor = 'fechado';
  let falhas = 0;
  let abertoEm = 0;
  let sondaEmVoo = false;
  // Cada troca de estado abre uma geração nova; o resultado de uma requisição que começou numa
  // geração anterior não mexe no estado (só a sonda decide o meio-aberto).
  let geracao = 0;

  function mudar(novo: EstadoDisjuntor): void {
    estado = novo;
    geracao++;
  }

  function atualizar(): EstadoDisjuntor {
    if (estado === 'aberto' && relogio() - abertoEm >= opcoes.abertoMs) mudar('meio_aberto');
    return estado;
  }

  function abrir(): void {
    mudar('aberto');
    abertoEm = relogio();
    falhas = 0;
  }

  function fechar(): void {
    if (estado !== 'fechado') mudar('fechado');
    falhas = 0;
  }

  return {
    estado: atualizar,
    async executar<T>(op: () => Promise<T>): Promise<T> {
      const agora = atualizar();
      if (agora === 'aberto' || (agora === 'meio_aberto' && sondaEmVoo)) {
        throw new ErroCliente(
          'circuito_aberto',
          'A API falhou seguidas vezes; nova tentativa em instantes.',
        );
      }
      const ehSonda = agora === 'meio_aberto';
      if (ehSonda) sondaEmVoo = true;
      const minha = geracao;
      try {
        const valor = await op();
        if (minha === geracao) fechar();
        return valor;
      } catch (bruto) {
        const erro = comoErroCliente(bruto);
        if (minha !== geracao) throw erro;
        if (erro.falhaDoServidor) {
          if (ehSonda) abrir();
          else if (++falhas >= opcoes.falhasParaAbrir) abrir();
        } else if (ehSonda) {
          // A API respondeu (com erro de entrada): está de pé.
          fechar();
        }
        throw erro;
      } finally {
        if (ehSonda) sondaEmVoo = false;
      }
    },
  };
}
