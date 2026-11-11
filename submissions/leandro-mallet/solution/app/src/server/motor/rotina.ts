import "server-only";
// Rotina diária do score (O-41): uma transação com o papel de carga; domingo roda o job semanal e todo dia o diário.
// Idempotente pelo dia de negócio (system_rotina_ja_rodou). Erro → rollback e evento "rotina_diaria_falha".
// Nada de DELETE: só as funções do banco e os inserts/updates que o papel de carga já tem.
import { randomUUID } from "node:crypto";
import type { ContextoRotina, MotorScore, ResumoJob, Sql } from "./contrato";

/** Conexão mínima: abre uma transação, entrega o "sql" dela e faz commit (ou rollback se a função lançar). */
export interface Conexao {
  transacao<T>(fn: (sql: Sql) => Promise<T>): Promise<T>;
}

export type StatusRotina = "ok" | "ja_rodou" | "ocupada" | "sem_motor" | "falha";

export interface ResultadoRotina {
  status: StatusRotina;
  dataNegocio: string | null;
  domingo: boolean;
  semanal?: ResumoJob | null;
  diario?: ResumoJob | null;
  erro?: string;
}

const CHAVE_TRAVA = 30034;

/** Começo de toda transação da rotina: papel de carga e contexto "sistema" com um correlation_id novo. */
async function abrir(sql: Sql) {
  await sql("set local role system_carga");
  const correlationId = randomUUID();
  await sql("select system_iniciar_contexto_sistema($1::uuid)", [correlationId]);
  return correlationId;
}

const registrar = (sql: Sql, tipo: string, detalhe: Record<string, unknown>) =>
  sql("select system_registrar_evento($1, $2::jsonb)", [tipo, JSON.stringify(detalhe)]);

/** Mensagem curta e sem dado sensível para o registro de falha. */
const resumoErro = (e: unknown) => (e instanceof Error ? e.message : String(e)).replace(/\s+/g, " ").slice(0, 300);

/**
 * forcar (só no POST manual): roda mesmo com o dia já marcado como rodado e registra "rotina_forcada"; nada é apagado.
 * O cron diário nunca força.
 */
export async function rodarRotina(conexao: Conexao, motor: MotorScore | null, origem: "cron" | "manual", opcoes: { forcar?: boolean } = {}): Promise<ResultadoRotina> {
  const forcar = origem === "manual" && !!opcoes.forcar;
  let dataNegocio: string | null = null;
  let domingo = false;
  try {
    return await conexao.transacao(async (sql) => {
      const correlationId = await abrir(sql);
      // Uma rotina por vez: se outra já está rodando, esta sai sem fazer nada.
      const [trava] = await sql<{ ok: boolean }>("select pg_try_advisory_xact_lock($1) as ok", [CHAVE_TRAVA]);
      if (!trava?.ok) return { status: "ocupada", dataNegocio: null, domingo: false };

      const [hoje] = await sql<{ data: string; dia_real: string; dow: number }>(
        "select system_data_negocio()::text as data, system_dia_real()::text as dia_real, extract(dow from system_data_negocio())::int as dow",
      );
      dataNegocio = hoje?.data ?? null;
      domingo = hoje?.dow === 0;
      if (!hoje || !dataNegocio) throw new Error("Relógio do banco sem data de negócio.");

      const [ja] = await sql<{ rodou: boolean }>("select system_rotina_ja_rodou($1::date) as rodou", [dataNegocio]);
      if (ja?.rodou && !forcar) return { status: "ja_rodou", dataNegocio, domingo };

      if (!motor) {
        // Sem o motor do score, nada é gravado além do registro; o dia não conta como rodado.
        await registrar(sql, "rotina_diaria", { dia_negocio: dataNegocio, status: "sem_motor", origem });
        return { status: "sem_motor", dataNegocio, domingo };
      }

      const ctx: ContextoRotina = { sql, dataNegocio, diaReal: hoje.dia_real, domingo, correlationId };
      const semanal = domingo ? await motor.semanal(ctx) : null;
      const diario = await motor.diario(ctx);
      // Rodada forçada: o dia já estava marcado; fica um registro próprio (o "ok" do dia continua o primeiro).
      if (forcar && ja?.rodou) await registrar(sql, "rotina_forcada", { dia_negocio: dataNegocio, origem, domingo, semanal, diario });
      else await registrar(sql, "rotina_diaria", { dia_negocio: dataNegocio, status: "ok", origem, forcada: forcar, domingo, semanal, diario });
      return { status: "ok", dataNegocio, domingo, semanal, diario };
    });
  } catch (e) {
    const erro = resumoErro(e);
    // A transação da rotina foi desfeita; o registro da falha vai numa transação à parte.
    try {
      await conexao.transacao(async (sql) => {
        await abrir(sql);
        await registrar(sql, "rotina_diaria_falha", { dia_negocio: dataNegocio, origem, erro });
      });
    } catch {
      // sem banco nem para registrar: o erro volta na resposta
    }
    return { status: "falha", dataNegocio, domingo, erro };
  }
}
