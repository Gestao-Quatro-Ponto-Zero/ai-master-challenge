import "server-only";
// Conexão da rotina com o banco: o papel de login g4_rotina (migration 0034), pela URL em DATABASE_URL_ROTINA.
// Só no servidor; a URL (com a senha) fica nos segredos do ambiente, nunca no código. TLS: use na URL o sslmode
// que o provedor pedir (ex.: sslmode=require ou no-verify).
import { Pool } from "pg";
import type { Sql } from "./contrato";
import type { Conexao } from "./rotina";

const g = globalThis as unknown as { __g4PoolRotina?: Pool };

function pool(): Pool {
  const url = process.env.DATABASE_URL_ROTINA;
  if (!url) throw new Error("DATABASE_URL_ROTINA não está configurada.");
  g.__g4PoolRotina ??= new Pool({ connectionString: url, max: 1, idleTimeoutMillis: 10_000, connectionTimeoutMillis: 15_000 });
  return g.__g4PoolRotina;
}

export const conexaoRotina: Conexao = {
  async transacao(fn) {
    const cliente = await pool().connect();
    try {
      await cliente.query("begin");
      const sql: Sql = async (texto, parametros = []) => (await cliente.query(texto, parametros)).rows;
      const r = await fn(sql);
      await cliente.query("commit");
      return r;
    } catch (e) {
      await cliente.query("rollback").catch(() => undefined);
      throw e;
    } finally {
      cliente.release();
    }
  },
};
