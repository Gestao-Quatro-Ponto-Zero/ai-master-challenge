// O-41 — a rotina diária de verdade contra um Postgres em memória (PGlite) com as migrations e o dataset inteiro.
// Lê as migrations de G4_DB_DIR ou de ../db (a pasta solution/db ao lado do app). Sem a pasta, o teste é pulado.
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { randomUUID } from "node:crypto";
import { PGlite } from "@electric-sql/pglite";
import { beforeAll, describe, expect, it } from "vitest";
import type { Sql } from "@/server/motor/contrato";
import type { Conexao } from "@/server/motor/rotina";

const dir = process.env.G4_DB_DIR ?? resolve(process.cwd(), "../db");
const temBanco = existsSync(join(dir, "migrations")) && existsSync(join(dir, "seed", "seed_dataset.sql"));

describe.skipIf(!temBanco)("rotina diária contra o banco (PGlite, dataset inteiro)", () => {
  const db = new PGlite();
  const q = async <T = Record<string, unknown>>(t: string, p: unknown[] = []) => (await db.query(t, p)).rows as T[];
  const conexao: Conexao = {
    transacao: (fn) => db.transaction(async (tx) => fn((async (t: string, p: unknown[] = []) => (await tx.query(t, p)).rows) as Sql)),
  };
  const comoSistema = (sql: string) => db.transaction(async (tx) => {
    await tx.query("select system_iniciar_contexto_sistema($1)", [randomUUID()]);
    await tx.exec(sql);
  });

  beforeAll(async () => {
    for (const r of ["anon", "authenticated"]) await db.exec(`create role ${r}`);
    await db.exec("create role service_role bypassrls");
    const pasta = join(dir, "migrations");
    for (const f of readdirSync(pasta).filter((x) => /^\d{4}_.*\.sql$/.test(x)).sort()) {
      await db.exec(`begin;\n${readFileSync(join(pasta, f), "utf8")}\ncommit;`);
      if (f.startsWith("0006_")) await db.exec(readFileSync(join(dir, "seed", "seed_dataset.sql"), "utf8"));
    }
    // a âncora real vira "hoje": a data de negócio de hoje é 31/12/2017 (um domingo)
    await comoSistema("update config_parametros set valor = to_jsonb(to_char(system_dia_real(), 'YYYY-MM-DD')) where chave = 'data_ancora_real'");
  }, 600_000);

  it("1º dia (31/12/2017, domingo, sem execução ativa): grava a execução nova, ativa e dá nota a todos os abertos", async () => {
    const { rodarRotina } = await import("@/server/motor/rotina");
    const { motorScore } = await import("@/server/motor/motor-score");
    const r = await rodarRotina(conexao, motorScore, "manual");
    expect(r).toMatchObject({ status: "ok", dataNegocio: "2017-12-31", domingo: true });
    expect(r.semanal).toMatchObject({ redistribuidos: 0, motivo: "sem execução ativa" });
    const ex = Number(r.diario!.execucao_id);
    const [ativa] = await q<{ v: string }>("select config_texto('execucao_ativa') as v");
    expect(Number(ativa!.v)).toBe(ex);
    const [c] = await q<{ abertos: number; notas: number; sem_nota: number; fora: number; dono: number }>(`
      select (select count(*)::int from core_deals where estagio in ('Prospecting','Engaging')) abertos,
             (select count(*)::int from score_deals where execucao_id = $1) notas,
             (select count(*)::int from core_deals d where d.estagio in ('Prospecting','Engaging')
                and not exists (select 1 from score_deals s where s.execucao_id = $1 and s.opportunity_id = d.opportunity_id)) sem_nota,
             (select count(*)::int from score_deals where execucao_id = $1 and (score < 0 or score > 120)) fora,
             (select count(*)::int from score_deals s join core_deals d using (opportunity_id) where s.execucao_id = $1 and s.vendedor_nome <> d.vendedor_nome) dono`,
      [ex]);
    expect(c).toMatchObject({ sem_nota: 0, fora: 0, dono: 0 });
    expect(c!.notas).toBe(c!.abertos);
    expect(c!.abertos).toBe(2089);
    const [m] = await q<{ motivos: number; comp: number; fits: number; padroes: number }>(`
      select (select count(*)::int from score_motivos where execucao_id = $1) motivos, (select count(*)::int from score_componentes where execucao_id = $1) comp,
             (select count(*)::int from score_fit_vendedores where execucao_id = $1) fits, (select count(*)::int from score_padroes_conta where execucao_id = $1) padroes`, [ex]);
    expect(m!.motivos).toBeGreaterThan(2089);
    expect(m!.comp).toBeGreaterThan(2089);
    expect(m!.fits).toBeGreaterThan(0);
    expect(m!.padroes).toBeGreaterThan(0);
    const [ev] = await q<{ n: number }>("select count(*)::int n from system_eventos where tipo = 'rotina_diaria' and detalhe ->> 'status' = 'ok'");
    expect(ev!.n).toBe(1);
  }, 300_000);

  it("idempotente: no mesmo dia não roda de novo nem cria outra execução", async () => {
    const { rodarRotina } = await import("@/server/motor/rotina");
    const { motorScore } = await import("@/server/motor/motor-score");
    const [antes] = await q<{ n: number }>("select count(*)::int n from score_execucoes");
    expect(await rodarRotina(conexao, motorScore, "cron")).toMatchObject({ status: "ja_rodou", dataNegocio: "2017-12-31" });
    const [depois] = await q<{ n: number }>("select count(*)::int n from score_execucoes");
    expect(depois!.n).toBe(antes!.n);
  }, 300_000);

  it("forçada no mesmo domingo (O-45): os 35 vendedores ativos são elegíveis (decisão 49) e a 2ª rodada é estável", async () => {
    const { rodarRotina } = await import("@/server/motor/rotina");
    const { motorScore } = await import("@/server/motor/motor-score");
    const [ativos] = await q<{ n: number }>(
      "select count(distinct v.nome)::int n from core_vendedores v join config_usuarios u on u.vendedor_nome = v.nome and u.ativo");
    const r = await rodarRotina(conexao, motorScore, "manual", { forcar: true });
    expect(r).toMatchObject({ status: "ok", dataNegocio: "2017-12-31", domingo: true });
    expect(Number(r.semanal!.elegiveis)).toBe(ativos!.n);
    expect(ativos!.n).toBe(35);
    expect(Number(r.semanal!.redistribuidos)).toBeGreaterThan(0);
    // vendedores sem histórico na janela recebem leads
    const [sem] = await q<{ n: number }>(`
      select count(distinct r.para_vendedor)::int n from acao_reatribuicoes r
       where r.origem = 'redistribuicao'
         and not exists (select 1 from core_deals d where d.vendedor_nome = r.para_vendedor and d.estagio in ('Won', 'Lost')
                           and d.close_date > date '2017-12-31' - interval '3 months')`);
    expect(sem!.n).toBeGreaterThan(0);
    const [ev] = await q<{ n: number }>("select count(*)::int n from system_eventos where tipo = 'rotina_forcada'");
    expect(ev!.n).toBe(1);
    // de novo no mesmo dia: o plano já está equilibrado, nada muda
    const r2 = await rodarRotina(conexao, motorScore, "manual", { forcar: true });
    expect(r2).toMatchObject({ status: "ok", semanal: expect.objectContaining({ redistribuidos: 0 }), diario: expect.objectContaining({ repasses: 0 }) });
    // o cron do mesmo dia continua idempotente
    expect(await rodarRotina(conexao, motorScore, "cron")).toMatchObject({ status: "ja_rodou" });
  }, 600_000);

  it("domingo seguinte (07/01/2018): redistribuição só por equilíbrio pela core_repassar_deal e execução nova", async () => {
    const { rodarRotina } = await import("@/server/motor/rotina");
    const { motorScore } = await import("@/server/motor/motor-score");
    await comoSistema("update config_parametros set valor = to_jsonb(to_char(system_dia_real() - 7, 'YYYY-MM-DD')) where chave = 'data_ancora_real'");
    const r = await rodarRotina(conexao, motorScore, "cron");
    expect(r).toMatchObject({ status: "ok", dataNegocio: "2018-01-07", domingo: true });
    expect(Number(r.semanal!.elegiveis)).toBe(35);
    const [red] = await q<{ n: number; motivo: string }>(
      "select count(*)::int n, min(motivo) motivo from acao_reatribuicoes where origem = 'redistribuicao'");
    expect(red!.motivo).toBe("Redistribuição de domingo.");
    const redistribuidos = red!.n;
    // ninguém com contato registrado foi redistribuído e não houve penalidade (config em null)
    const [x] = await q<{ com_contato: number; pen: number }>(`
      select (select count(*)::int from acao_reatribuicoes r join core_deals d using (opportunity_id) where r.origem = 'redistribuicao' and d.ultimo_contato_em is not null) com_contato,
             (select count(*)::int from system_penalidades) pen`);
    expect(x).toMatchObject({ com_contato: 0, pen: 0 });
    // a nota nova já usa o dono novo
    const ex = Number(r.diario!.execucao_id);
    const [dono] = await q<{ n: number }>(
      "select count(*)::int n from score_deals s join core_deals d using (opportunity_id) where s.execucao_id = $1 and s.vendedor_nome <> d.vendedor_nome", [ex]);
    expect(dono!.n).toBe(0);
    // segunda-feira (08/01) não redistribui: só o diário
    await comoSistema("update config_parametros set valor = to_jsonb(to_char(system_dia_real() - 8, 'YYYY-MM-DD')) where chave = 'data_ancora_real'");
    const seg = await rodarRotina(conexao, motorScore, "cron");
    expect(seg).toMatchObject({ status: "ok", dataNegocio: "2018-01-08", domingo: false, semanal: null });
    const [red2] = await q<{ n: number }>("select count(*)::int n from acao_reatribuicoes where origem = 'redistribuicao'");
    expect(red2!.n).toBe(redistribuidos);
  }, 600_000);
});
