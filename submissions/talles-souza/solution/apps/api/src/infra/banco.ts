/**
 * Conexão com o banco compartilhado (Postgres, lib `pg`) e o disjuntor que protege a API quando
 * ele falha. A URL vem só de `DATABASE_URL` (ambiente); nunca do código. O papel do banco só
 * lê `deals`, `vendedores` e `metadados` e só lê e acrescenta em `respostas` e `decisoes`:
 * nada aqui altera ou apaga linha, nem mexe no schema.
 */
import pg from 'pg';

/** Quem roda SQL: o pool inteiro ou o cliente de uma transação. */
export interface Consultor {
  consultar<T extends object>(sql: string, parametros?: readonly unknown[]): Promise<T[]>;
}

/** O banco: consultas, transação e o fechamento do pool. */
export interface Banco extends Consultor {
  /**
   * Roda `fn` numa transação. Com `desfazer`, sempre termina em ROLLBACK (o teste de integração
   * grava e confere sem deixar linha no banco compartilhado).
   */
  transacao<T>(fn: (c: Consultor) => Promise<T>, opcoes?: { desfazer?: boolean }): Promise<T>;
  fechar(): Promise<void>;
}

/** Limites da conexão: poucas conexões (cabe numa função serverless) e tempo curto. */
export const LIMITES_BANCO = {
  conexoes: 3,
  conectarEmMs: 3_000,
  consultaEmMs: 4_000,
} as const;

function consultorDe(alvo: pg.Pool | pg.PoolClient): Consultor {
  return {
    async consultar<T extends object>(sql: string, parametros: readonly unknown[] = []) {
      const r = await alvo.query<T>(sql, [...parametros]);
      return r.rows;
    },
  };
}

/** Abre o pool para a URL dada (a de `DATABASE_URL`). `log` recebe os erros de conexão ociosa. */
export function criarBanco(url: string, log: (linha: string) => void): Banco {
  const pool = new pg.Pool({
    connectionString: url,
    max: LIMITES_BANCO.conexoes,
    connectionTimeoutMillis: LIMITES_BANCO.conectarEmMs,
    statement_timeout: LIMITES_BANCO.consultaEmMs,
    query_timeout: LIMITES_BANCO.consultaEmMs,
    idleTimeoutMillis: 10_000,
    application_name: 'lead-scorer',
  });
  // sem este ouvinte, uma conexão ociosa que cai derruba o processo
  pool.on('error', (e) => log('banco: conexão ociosa caiu: ' + semQuebra(e.message)));
  const raiz = consultorDe(pool);
  return {
    consultar: raiz.consultar,
    async transacao(fn, opcoes = {}) {
      const cliente = await pool.connect();
      try {
        await cliente.query('BEGIN');
        const valor = await fn(consultorDe(cliente));
        await cliente.query(opcoes.desfazer ? 'ROLLBACK' : 'COMMIT');
        return valor;
      } catch (e) {
        await cliente.query('ROLLBACK').catch(() => undefined);
        throw e;
      } finally {
        cliente.release();
      }
    },
    fechar: () => pool.end(),
  };
}

/** Mensagem de erro numa linha só, curta (pode trazer parte do SQL, nunca a URL). */
export function semQuebra(mensagem: string): string {
  return mensagem.replace(/[\r\n]+/g, ' ').slice(0, 200);
}

/** O circuito está aberto: o banco falhou seguidas vezes e a API nem tenta por um tempo. */
export class CircuitoAberto extends Error {
  constructor() {
    super('banco indisponível (circuito aberto)');
    this.name = 'CircuitoAberto';
  }
}

export interface OpcoesDisjuntorBanco {
  /** Falhas seguidas que abrem o circuito. */
  falhasParaAbrir: number;
  /** Quanto tempo o circuito fica aberto antes de deixar uma tentativa passar. */
  abertoPorMs: number;
  relogio: () => number;
}

export const DISJUNTOR_BANCO_PADRAO: OpcoesDisjuntorBanco = {
  falhasParaAbrir: 3,
  abertoPorMs: 30_000,
  relogio: Date.now,
};

export interface DisjuntorBanco {
  /** Roda `f`; com o circuito aberto, falha na hora com `CircuitoAberto`. */
  executar<T>(f: () => Promise<T>): Promise<T>;
  aberto(): boolean;
}

/**
 * Disjuntor simples: N falhas seguidas abrem o circuito por um tempo; passado o tempo, a próxima
 * chamada tenta de novo (meio aberto) e um sucesso fecha.
 */
export function criarDisjuntorBanco(
  opcoes: OpcoesDisjuntorBanco = DISJUNTOR_BANCO_PADRAO,
): DisjuntorBanco {
  let falhas = 0;
  let abertoAte = 0;
  const aberto = () => falhas >= opcoes.falhasParaAbrir && opcoes.relogio() < abertoAte;
  return {
    aberto,
    async executar(f) {
      if (aberto()) throw new CircuitoAberto();
      try {
        const valor = await f();
        falhas = 0;
        return valor;
      } catch (e) {
        falhas += 1;
        if (falhas >= opcoes.falhasParaAbrir) abertoAte = opcoes.relogio() + opcoes.abertoPorMs;
        throw e;
      }
    },
  };
}
