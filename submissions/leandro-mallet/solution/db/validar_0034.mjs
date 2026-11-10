// Valida a 0034 (relógio que anda e rotina diária) num Postgres em memória (PGlite).
// Uso (Node 20+), numa pasta com o PGlite instalado:
//   npm install @electric-sql/pglite@0.5.11
//   node validar_0034.mjs <solution/db>
// Confere: hoje (dia da âncora) = 31/12/2017; 7 dias reais depois = 07/01/2018, um domingo; o relógio alimenta a
// view (dias no pipeline); papel g4_rotina de login, sem senha, membro só de system_carga; a rotina registra o dia
// e system_rotina_ja_rodou responde; o app (service_role) não age como sistema; nada apagado.
import { PGlite } from "@electric-sql/pglite";
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { randomUUID } from "node:crypto";

const base = process.argv[2];
if (!base) {
  console.error("Informe a pasta solution/db.");
  process.exit(2);
}
const db = new PGlite();
let falhas = 0;
const ok = (m) => console.log(`  ok   ${m}`);
const falha = (m) => { falhas += 1; console.log(`  FALHA ${m}`); };
const confere = (c, m, d) => (c ? ok(m) : falha(`${m}${d ? ` — ${d}` : ""}`));
const q = async (sql, p = []) => (await db.query(sql, p)).rows;
const um = async (sql, p = []) => Object.values((await q(sql, p))[0] ?? {})[0];
const corr = () => randomUUID();
const comoSistema = (sql) => db.transaction(async (tx) => {
  await tx.query(`select system_iniciar_contexto_sistema($1)`, [corr()]);
  await tx.exec(sql);
});
const iso = (d) => (d instanceof Date ? d.toISOString().slice(0, 10) : String(d));

for (const r of ["anon", "authenticated"]) await db.exec(`create role ${r}`);
await db.exec(`create role service_role bypassrls`);

console.log("1. Migrations");
const pasta = join(base, "migrations");
let seed = readFileSync(join(base, "seed", "seed_dataset.sql"), "utf8");
seed = seed.split(/;\n/).filter((c) => !/^\s*insert into core_(contas|deals) /m.test(c)).join(";\n");
for (const f of readdirSync(pasta).filter((x) => /^\d{4}_.*\.sql$/.test(x)).sort()) {
  try { await db.exec(`begin;\n${readFileSync(join(pasta, f), "utf8")}\ncommit;`); }
  catch (e) { falha(`${f}: ${e.message}`); process.exit(1); }
  if (f.startsWith("0006_")) await db.exec(seed);
}
ok("0001–0034 aplicadas");

console.log("2. Relógio");
confere(await um(`select valor ->> 0 from (select jsonb_build_array(valor) valor from config_parametros where chave = 'data_ancora_real') x`) === "2026-11-10", "âncora real = 10/11/2026");
confere(await um(`select valor ->> 0 from (select jsonb_build_array(valor) valor from config_parametros where chave = 'data_ancora_negocio') x`) === "2017-12-31", "âncora de negócio = 31/12/2017");
// Simula "hoje" movendo a âncora real para hoje e para 7 dias atrás (o relógio do PGlite é o de agora).
const hoje = iso(await um(`select system_dia_real()`));
await comoSistema(`update config_parametros set valor = to_jsonb('${hoje}'::text) where chave = 'data_ancora_real'`);
confere(iso(await um(`select system_data_negocio()`)) === "2017-12-31", "no dia da âncora, a data de negócio é 31/12/2017");
await comoSistema(`update config_parametros set valor = to_jsonb(to_char(system_dia_real() - 7, 'YYYY-MM-DD')) where chave = 'data_ancora_real'`);
const d7 = iso(await um(`select system_data_negocio()`));
confere(d7 === "2018-01-07", `7 dias reais depois = 07/01/2018 (${d7})`);
confere(Number(await um(`select extract(dow from system_data_negocio())::int`)) === 0, "07/01/2018 é domingo (dia do job semanal)");
await comoSistema(`
  insert into core_deals (opportunity_id, nome, vendedor_nome, produto_nome, conta_nome, estagio, data_abertura)
  values ('K0000001', 'K1', 'Anna Snelling', 'GTX Basic', null, 'Engaging', '2017-12-01')`);
confere(Number(await um(`select dias_desde_abertura from core_deals_visao where opportunity_id = 'K0000001'`)) === 37, "a view anda junto: aberto em 01/12/2017 = 37 dias em 07/01/2018");
await comoSistema(`update config_parametros set valor = '"2026-11-10"' where chave = 'data_ancora_real'`);

console.log("3. Papel de login da rotina");
const papel = (await q(`select rolcanlogin, rolinherit, rolpassword from pg_authid where rolname = 'g4_rotina'`))[0];
confere(papel?.rolcanlogin === true, "g4_rotina existe e faz login");
confere(papel?.rolpassword === null, "sem senha no arquivo (quem aplica define fora do git)");
const membro = await q(`select r.rolname from pg_auth_members m join pg_roles r on r.oid = m.roleid join pg_roles u on u.oid = m.member where u.rolname = 'g4_rotina'`);
confere(membro.length === 1 && membro[0].rolname === "system_carga", `membro só de system_carga (${membro.map((m) => m.rolname)})`);

console.log("4. Rotina registrada");
const dia = iso(await um(`select system_data_negocio()`));
confere((await um(`select system_rotina_ja_rodou($1::date)`, [dia])) === false, "antes de rodar: o dia não rodou");
await db.exec(`set role g4_rotina`);
await db.transaction(async (tx) => {
  await tx.exec(`set local role system_carga`);
  await tx.query(`select system_iniciar_contexto_sistema($1)`, [corr()]);
  await tx.query(`select system_registrar_evento('rotina_diaria', jsonb_build_object('dia_negocio', $1::text, 'status', 'ok'))`, [dia]);
});
await db.exec(`reset role`);
confere((await um(`select system_rotina_ja_rodou($1::date)`, [dia])) === true, "a rotina entra como g4_rotina, assume system_carga e registra o dia; depois o dia consta como rodado");
await db.transaction(async (tx) => {
  await tx.query(`select system_iniciar_contexto_sistema($1)`, [corr()]);
  await tx.query(`select system_registrar_evento('rotina_diaria', jsonb_build_object('dia_negocio', '2018-01-08', 'status', 'falha'))`);
});
confere((await um(`select system_rotina_ja_rodou('2018-01-08'::date)`)) === false, "dia com falha não conta como rodado");

console.log("5. Permissões");
let recusou = false;
try { await db.exec(`set role service_role; select system_iniciar_contexto_sistema(gen_random_uuid());`); } catch { recusou = true; }
await db.exec(`reset role`);
confere(recusou, "o app (service_role) continua sem agir como sistema");
confere((await um(`select has_function_privilege('anon', 'system_rotina_ja_rodou(date)', 'execute')`)) === false, "anon não executa system_rotina_ja_rodou");

console.log(falhas ? `\n${falhas} falha(s).` : "\nTudo certo.");
process.exit(falhas ? 1 : 0);
