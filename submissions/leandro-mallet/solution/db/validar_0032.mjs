// Valida a 0032 (20 prioridades por dia) num Postgres em memória (PGlite), sem conectar em banco nenhum.
// Uso (Node 20+), numa pasta com o PGlite instalado:
//   npm install @electric-sql/pglite@0.5.11
//   node validar_0032.mjs <solution/db>
// Confere: meta = 20; lista de hoje montada com 10 é completada até 20 na próxima abertura, sem tirar os itens que já
// estavam (marcados ou não); depois disso a leitura volta a mostrar a lista; vendedor com poucos deals não fica preso
// em "desatualizada"; nada apagado.
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
const fn = (nome, args) => q(`select * from ${nome}(${args.map((_, i) => `$${i + 1}`).join(", ")})`, args);
const corr = () => randomUUID();
const comoSistema = (sql) => db.transaction(async (tx) => {
  await tx.query(`select system_iniciar_contexto_sistema($1)`, [corr()]);
  await tx.exec(sql);
});

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
ok("0001–0032 aplicadas");
confere((await q(`select valor from config_parametros where chave = 'meta_prioridades_dia'`))[0].valor === 20, "meta_prioridades_dia = 20");

console.log("2. Cenário: Anna com 25 leads e nota; Cecily com 3");
const id = (nome) => q(`select id from config_usuarios where nome_exibicao = $1`, [nome]).then((r) => r[0].id);
const anna = await id("Anna Snelling");
const cecily = await id("Cecily Lampkin");
const linhas = (v, n, pre) => Array.from({ length: n }, (_, i) => `('${pre}${String(i).padStart(6, "0")}', '${pre}${i}', '${v}', 'GTX Basic', null, 'Prospecting')`).join(",\n");
await comoSistema(`
  insert into core_deals (opportunity_id, nome, vendedor_nome, produto_nome, conta_nome, estagio) values
    ${linhas("Anna Snelling", 25, "AN")}, ${linhas("Cecily Lampkin", 3, "CE")};
  insert into score_execucoes (reference_date, gerado_em, versao, arquivo_sha256) values ('2017-12-31', now(), 't-1', repeat('a', 64));
  insert into score_deals (execucao_id, opportunity_id, vendedor_nome, cohort, fit, heat, score, acao_sugerida, valor_esperado)
    select 1, opportunity_id, vendedor_nome, 'produto=GTX Basic', 60, 50, 100 - row_number() over (order by opportunity_id), 'focar', 550
      from core_deals;
`);
await fn("score_ativar_execucao", [corr(), 1]);
ok("execução 1 ativa");

console.log("3. Lista montada com 10 (antes da 0032) e completada até 20");
await comoSistema(`update config_parametros set valor = '10' where chave = 'meta_prioridades_dia'`);
const l10 = await fn("acao_prioridades_do_dia", [anna, corr()]);
confere(l10.length === 10, `com a meta 10, a lista tem 10 (${l10.length})`);
await fn("acao_marcar_prioridade", [anna, corr(), l10[0].opportunity_id, "feita", "ligacao", "Falei com Compras."]);
await fn("acao_marcar_prioridade", [anna, corr(), l10[1].opportunity_id, "pulada", null, null]);
const antes = (await q(`select count(*)::int n from acao_prioridades`))[0].n;

await comoSistema(`update config_parametros set valor = '20' where chave = 'meta_prioridades_dia'`);
confere((await fn("acao_listar_prioridades", [anna])).length === 0, "com a meta nova, a lista de 10 fica desatualizada (a leitura volta vazia)");
const l20 = await fn("acao_prioridades_do_dia", [anna, corr()]);
confere(l20.length === 20, `na próxima abertura a lista vai a 20 (${l20.length})`);
const ids10 = l10.map((r) => r.opportunity_id);
confere(JSON.stringify(l20.slice(0, 10).map((r) => r.opportunity_id)) === JSON.stringify(ids10), "os 10 de antes ficam no lugar, na mesma ordem");
confere(l20[0].marcada === "feita" && l20[1].marcada === "pulada", "os marcados (✓ e ✕) continuam marcados");
const novos = l20.slice(10).map((r) => r.score);
confere(novos.every((s, i) => i === 0 || s <= novos[i - 1]) && novos[0] <= l20[9].score, "os 10 novos entram depois, pela nota");
confere((await fn("acao_listar_prioridades", [anna])).length === 20, "depois de completada, a leitura mostra os 20");
const de_novo = await fn("acao_prioridades_do_dia", [anna, corr()]);
confere(JSON.stringify(de_novo.map((r) => r.opportunity_id)) === JSON.stringify(l20.map((r) => r.opportunity_id)), "abrir de novo não mexe na lista");
const depois = (await q(`select count(*)::int n from acao_prioridades`))[0].n;
confere(depois === antes + 10, `nada apagado: só entraram 10 linhas (${antes} → ${depois})`);

console.log("4. Vendedor com poucos deals");
const lc = await fn("acao_prioridades_do_dia", [cecily, corr()]);
confere(lc.length === 3, `Cecily tem 3 deals e a lista fica com 3 (${lc.length})`);
confere((await fn("acao_listar_prioridades", [cecily])).length === 3, "a lista curta não fica presa em desatualizada");
const meta = await q(`select distinct meta_dia from acao_prioridades where substituida_em is null`);
confere(meta.length === 1 && meta[0].meta_dia === 20, "todas as linhas ativas guardam a meta usada (20)");

console.log(falhas ? `\n${falhas} falha(s).` : "\nTudo certo.");
process.exit(falhas ? 1 : 0);
