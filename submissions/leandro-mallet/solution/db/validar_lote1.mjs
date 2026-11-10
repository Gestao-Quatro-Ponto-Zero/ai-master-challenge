// Valida o LOTE 1 num Postgres em memória (PGlite), sem conectar em banco nenhum.
//
// Uso (Node 20+), numa pasta com o PGlite instalado:
//   npm install @electric-sql/pglite@0.5.11
//   node validar_lote1.mjs <pasta solution/db>
//
// 1. Aplica migrations/0001…0006 (cada arquivo numa transação) e depois seed/seed_dataset.sql.
// 2. Confere pelo catálogo: prefixos, FK com índice e ON DELETE RESTRICT, nenhum CASCADE,
//    RLS e gatilhos de bloqueio em todas as tabelas.
// 3. Confere os dados carregados contra o dataset limpo e a auditoria da carga.
// 4. Testa as guardas: DELETE, TRUNCATE, escrita sem usuário, UPDATE na auditoria, permissões
//    de anon e service_role, versão do deal e reexecução do seed sem duplicar.
// Sai com código 1 se algo falhar.

import { PGlite } from "@electric-sql/pglite";
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

const base = process.argv[2];
if (!base) { console.error("Informe a pasta solution/db."); process.exit(2); }

const db = new PGlite();
let falhas = 0;
const ok = (m) => console.log(`  ok    ${m}`);
const falha = (m) => { falhas += 1; console.log(`  FALHA ${m}`); };
const q = async (sql, p = []) => (await db.query(sql, p)).rows;
const um = async (sql, p = []) => Object.values((await q(sql, p))[0])[0];
const igual = (rotulo, obtido, esperado) =>
  String(obtido) === String(esperado) ? ok(`${rotulo}: ${obtido}`) : falha(`${rotulo}: ${obtido} (esperado ${esperado})`);
async function esperaErro(rotulo, fn, codigo) {
  try { await fn(); falha(`${rotulo}: deveria ser recusado`); }
  catch (e) {
    if (codigo && e.code !== codigo) falha(`${rotulo}: erro ${e.code} (${e.message}), esperado ${codigo}`);
    else ok(`${rotulo} → recusado (${e.code})`);
  }
}

// Papéis como no Supabase: service_role passa por cima do RLS (bypassrls); anon e authenticated não.
for (const r of ["anon", "authenticated"]) await db.exec(`create role ${r}`);
await db.exec(`create role service_role bypassrls`);

console.log("1. Aplicando o lote 1");
const pastaMig = join(base, "migrations");
const lote1 = readdirSync(pastaMig).filter((f) => /^000[1-6]_.*\.sql$/.test(f)).sort();
if (lote1.length !== 6) { falha(`esperava 6 arquivos 0001–0006, achei ${lote1.length}`); process.exit(1); }
for (const f of lote1) {
  try { await db.exec(`begin;\n${readFileSync(join(pastaMig, f), "utf8")}\ncommit;`); ok(f); }
  catch (e) { falha(`${f}: ${e.message}`); process.exit(1); }
}
const seed = readFileSync(join(base, "seed", "seed_dataset.sql"), "utf8");
try { await db.exec(seed); ok("seed/seed_dataset.sql"); }
catch (e) { falha(`seed: ${e.message}`); process.exit(1); }

console.log("2. Catálogo");
const prefixo = /^(core|config|score|acao|system)_/;
const tabelas = (await q(`select relname from pg_class c join pg_namespace n on n.oid=c.relnamespace
  where n.nspname='public' and c.relkind='r' order by 1`)).map((r) => r.relname);
igual("tabelas do lote 1", tabelas.join(", "),
  "config_parametros, config_usuarios, core_contas, core_deals, core_escritorios, core_managers, core_produtos, core_vendedores, system_auditoria");
tabelas.every((t) => prefixo.test(t)) ? ok("todas com prefixo") : falha("tabela sem prefixo");
const objetos = await q(`select proname as n from pg_proc p join pg_namespace s on s.oid=p.pronamespace where s.nspname='public'
  union all select tgname from pg_trigger t join pg_class c on c.oid=t.tgrelid join pg_namespace s on s.oid=c.relnamespace
   where s.nspname='public' and not t.tgisinternal
  union all select relname from pg_class c join pg_namespace s on s.oid=c.relnamespace where s.nspname='public' and c.relkind in ('i','v')`);
const semPref = objetos.filter((o) => !prefixo.test(o.n));
semPref.length ? falha(`objetos sem prefixo: ${semPref.map((o) => o.n)}`) : ok(`${objetos.length} functions, triggers, índices e views com prefixo`);
const fks = await q(`select conname, conrelid, conkey, confdeltype, confupdtype from pg_constraint c
  join pg_namespace n on n.oid=c.connamespace where n.nspname='public' and contype='f'`);
fks.every((f) => f.confdeltype === "r") ? ok(`${fks.length} FKs, todas ON DELETE RESTRICT`) : falha("FK sem RESTRICT");
fks.some((f) => f.confdeltype === "c" || f.confupdtype === "c") ? falha("há CASCADE") : ok("nenhum CASCADE");
const idx = await q(`select indrelid, indkey::text as cols, indpred is null as total from pg_index i
  join pg_class c on c.oid=i.indrelid join pg_namespace n on n.oid=c.relnamespace where n.nspname='public'`);
const semIdx = fks.filter((f) => !idx.some((i) => i.indrelid === f.conrelid && i.total && (i.cols + " ").startsWith(f.conkey.join(" ") + " ")));
semIdx.length ? falha(`FK sem índice: ${semIdx.map((f) => f.conname)}`) : ok("toda FK com índice");
const semGuarda = await q(`select relname from pg_class c join pg_namespace n on n.oid=c.relnamespace
  where n.nspname='public' and c.relkind='r' and (not relrowsecurity
    or not exists (select 1 from pg_trigger g where g.tgrelid=c.oid and g.tgname=c.relname||'_bloquear_delete')
    or not exists (select 1 from pg_trigger g where g.tgrelid=c.oid and g.tgname=c.relname||'_bloquear_truncate'))`);
semGuarda.length ? falha(`sem RLS/bloqueio: ${semGuarda.map((r) => r.relname)}`) : ok("RLS e bloqueio de DELETE/TRUNCATE nas 9 tabelas");
const politicas = await um(`select count(*) from pg_policies where schemaname='public'`);
igual("políticas de RLS (nenhuma pública)", politicas, 0);

console.log("3. Dados carregados");
igual("escritórios", await um(`select count(*) from core_escritorios`), 3);
igual("managers", await um(`select count(*) from core_managers`), 6);
igual("vendedores", await um(`select count(*) from core_vendedores`), 35);
igual("produtos", await um(`select count(*) from core_produtos`), 7);
igual("contas", await um(`select count(*) from core_contas`), 85);
igual("contas com empresa-mãe", await um(`select count(*) from core_contas where empresa_mae_nome is not null`), 15);
igual("usuários (1 sistema, 1 admin, 6 managers, 35 vendedores)",
  await um(`select string_agg(papel||':'||n, ' ' order by papel) from (select papel, count(*) n from config_usuarios group by papel) x`),
  "admin:1 manager:6 sistema:1 vendedor:35");
igual("parâmetros", await um(`select count(*) from config_parametros`), 27);
igual("deals", await um(`select count(*) from core_deals`), 8800);
igual("deals por estágio", await um(`select string_agg(estagio||':'||n, ' ' order by estagio) from
  (select estagio, count(*) n from core_deals group by estagio) x`), "Engaging:1589 Lost:2473 Prospecting:500 Won:4238");
igual("abertos sem empresa", await um(`select count(*) from core_deals where conta_nome is null and estagio in ('Prospecting','Engaging')`), 1425);
igual("fechados sem empresa", await um(`select count(*) from core_deals where conta_nome is null and estagio in ('Won','Lost')`), 0);
igual("Prospecting sem data de abertura", await um(`select count(*) from core_deals where estagio='Prospecting' and data_abertura is null`), 500);
igual("receita ganha (soma close_value)", await um(`select sum(close_value) from core_deals where estagio='Won'`), 10005534);
igual("GTXPro corrigido", await um(`select count(*) from core_deals where produto_nome='GTX Pro'`), 1480);
igual("nome padrão do deal", await um(`select nome from core_deals where opportunity_id='1C1I7A6R'`), "Cancity · GTX Plus Basic");
igual("período de abertura", await um(`select min(data_abertura)||' a '||max(data_abertura) from core_deals`), "2016-10-20 a 2017-12-27");
igual("auditoria da carga (todas as linhas inseridas, assinadas por 'sistema')",
  await um(`select count(*) from system_auditoria where usuario_id=1 and operacao='insert'`), 3 + 6 + 35 + 7 + 85 + 43 + 27 + 8800);
igual("data do negócio na auditoria do seed", await um(`select max(data_negocio)::text from system_auditoria where tabela='core_deals'`), "2017-12-31");

console.log("4. Guardas");
await esperaErro("DELETE em core_deals", () => db.exec(`delete from core_deals where opportunity_id='1C1I7A6R'`), "GS405");
await esperaErro("TRUNCATE em core_deals (gatilho)", () => db.exec(`truncate core_deals`), "GS405");
await esperaErro("TRUNCATE em system_auditoria (gatilho)", () => db.exec(`truncate system_auditoria`), "GS405");
await esperaErro("TRUNCATE em core_contas (tem FK apontando)", () => db.exec(`truncate core_contas`));
await esperaErro("UPDATE sem usuário", () => db.exec(`update core_deals set nome='x' where opportunity_id='1C1I7A6R'`), "GS401");
await esperaErro("UPDATE na auditoria", () => db.exec(`update system_auditoria set papel='x' where id=1`), "GS405");
await esperaErro("DELETE na auditoria", () => db.exec(`delete from system_auditoria where id=1`), "GS405");
await esperaErro("anon lê core_deals", () => db.exec(`set role anon; select 1 from core_deals limit 1;`), "42501");
await db.exec(`reset role`);
await esperaErro("service_role apaga deal", () => db.exec(`set role service_role; delete from core_deals where opportunity_id='1C1I7A6R';`), "42501");
await db.exec(`reset role`);
await db.exec(`set role service_role`);
const lidos = await um(`select count(*) from core_deals`);
await db.exec(`reset role`);
igual("service_role lê core_deals", lidos, 8800);

await db.exec(`begin; select system_iniciar_contexto(5, '11111111-1111-4111-8111-111111111111'::uuid);
  update core_deals set nome = 'Cancity · GTX Plus Basic (editado)' where opportunity_id='1C1I7A6R'; commit;`);
const aud = (await q(`select usuario_id, papel, antes->>'nome' as antes, depois->>'nome' as depois from system_auditoria
  where tabela='core_deals' and registro_id='1C1I7A6R' and operacao='update'`))[0];
aud && aud.usuario_id == 5 && aud.antes === "Cancity · GTX Plus Basic" && aud.depois.endsWith("(editado)")
  ? ok(`update auditado com antes e depois, usuário 5 (${aud.papel})`) : falha(`auditoria do update: ${JSON.stringify(aud)}`);
igual("versão do deal (atualizado_por)", await um(`select atualizado_por from core_deals where opportunity_id='1C1I7A6R'`), 5);
await esperaErro("usuário inexistente", () => db.exec(`begin; select system_iniciar_contexto(999, gen_random_uuid()); commit;`), "GS401");
await db.exec(`rollback`).catch(() => {});

const antes = await um(`select count(*) from system_auditoria`);
await db.exec(seed);
igual("seed rodado de novo: deals", await um(`select count(*) from core_deals`), 8800);
igual("seed rodado de novo: nenhuma linha nova na auditoria", await um(`select count(*) from system_auditoria`), antes);
igual("seed não sobrescreveu a edição", await um(`select nome from core_deals where opportunity_id='1C1I7A6R'`), "Cancity · GTX Plus Basic (editado)");

console.log(falhas ? `\n${falhas} falha(s).` : "\nLote 1 aprovado: migrations e seed aplicados, catálogo, dados e guardas conferidos.");
process.exit(falhas ? 1 : 0);
