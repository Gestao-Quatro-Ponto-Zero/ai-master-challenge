// Valida a 0033 (redistribuição de domingo só por equilíbrio) num Postgres em memória (PGlite).
// Uso (Node 20+), numa pasta com o PGlite instalado:
//   npm install @electric-sql/pglite@0.5.11
//   node validar_0033.mjs <solution/db>
// Confere: redistribuição sem as travas do repasse; lead com contato recusado nas duas origens; repasse por janela
// ainda com as travas (e com a penalidade); motivo novo em acao_reatribuicoes e na linha do tempo; nada apagado.
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
const corr = () => randomUUID();
const comoSistema = (sql) => db.transaction(async (tx) => {
  await tx.query(`select system_iniciar_contexto_sistema($1)`, [corr()]);
  await tx.exec(sql);
});
// core_repassar_deal(correlation, deal, para, origem, execucao, fit_dono, fit_novo, posicao_top, faixa_heat)
const repassar = (deal, para, origem, fitDono, fitNovo, top) =>
  q(`select * from core_repassar_deal($1, $2, $3, $4, null, $5::smallint, $6::smallint, $7::smallint, null)`, [corr(), deal, para, origem, fitDono, fitNovo, top]);
async function esperaErro(rotulo, f, codigo) {
  try { await f(); falha(`${rotulo}: deveria dar erro ${codigo}`); }
  catch (e) { e.code === codigo ? ok(`${rotulo} → recusado (${e.code}: ${e.message})`) : falha(`${rotulo}: ${e.code} ${e.message}`); }
}

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
ok("0001–0033 aplicadas");

console.log("2. Cenário");
await comoSistema(`
  insert into core_deals (opportunity_id, nome, vendedor_nome, produto_nome, conta_nome, estagio, data_abertura, close_date, close_value) values
    ('R0000001', 'R1', 'Anna Snelling', 'GTX Basic', null, 'Prospecting', null, null, null),
    ('R0000002', 'R2', 'Anna Snelling', 'GTX Basic', null, 'Prospecting', null, null, null),
    ('R0000003', 'R3', 'Anna Snelling', 'GTX Basic', null, 'Engaging', '2017-12-01', null, null),
    ('R0000004', 'R4', 'Anna Snelling', 'GTX Basic', null, 'Engaging', '2017-12-01', null, null),
    ('R0000005', 'R5', 'Anna Snelling', 'GTX Basic', null, 'Won', '2017-11-01', '2017-12-20', 550);
  update core_deals set ultimo_contato_em = '2017-12-30' where opportunity_id = 'R0000002';
  update config_parametros set valor = '{"pontos": 5, "dias": 7}' where chave = 'penalidade_roteamento';
`);
ok("deals da Anna (sem contato, com contato, fechado) e penalidade de janela configurada (5 pontos, 7 dias)");
const auditAntes = (await q(`select count(*)::int n from system_auditoria`))[0].n;

console.log("3. Redistribuição de domingo: só equilíbrio");
const r1 = (await repassar("R0000001", "Cecily Lampkin", "redistribuicao", 80, 40, 30))[0];
confere(r1 && r1.para_vendedor === "Cecily Lampkin", "aceita FIT do novo 40 (abaixo de 75), 40 pontos abaixo do dono e fora do top 5");
confere(r1.motivo === "Redistribuição de domingo." && r1.origem === "redistribuicao", `motivo novo gravado ("${r1.motivo}")`);
confere(r1.fit_dono === 80 && r1.fit_novo === 40 && r1.posicao_top === 30, "registro guarda fit_dono, fit_novo e a posição");
confere((await q(`select vendedor_nome v from core_deals where opportunity_id = 'R0000001'`))[0].v === "Cecily Lampkin", "o deal passa para o novo vendedor");
confere((await q(`select count(*)::int n from system_penalidades`))[0].n === 0, "redistribuição não gera penalidade");
await esperaErro("redistribuição de lead COM contato registrado", () => repassar("R0000002", "Cecily Lampkin", "redistribuicao", 80, 90, 1), "GS422");
await esperaErro("redistribuição de deal fechado", () => repassar("R0000005", "Cecily Lampkin", "redistribuicao", 80, 90, 1), "GS422");
await esperaErro("redistribuição para o próprio dono", () => repassar("R0000003", "Anna Snelling", "redistribuicao", 80, 90, 1), "GS422");
await esperaErro("redistribuição para vendedor que não existe", () => repassar("R0000003", "Ninguém", "redistribuicao", 80, 90, 1), "GS422");

console.log("4. Repasse por mudança de janela: travas mantidas");
await esperaErro("janela com FIT do novo abaixo de 75", () => repassar("R0000003", "Cecily Lampkin", "repasse_janela", 70, 74, 1), "GS422");
await esperaErro("janela com FIT do novo mais de 3 abaixo do dono", () => repassar("R0000003", "Cecily Lampkin", "repasse_janela", 90, 80, 1), "GS422");
await esperaErro("janela fora do top 5", () => repassar("R0000003", "Cecily Lampkin", "repasse_janela", 80, 80, 6), "GS422");
await esperaErro("janela de lead com contato", () => repassar("R0000002", "Cecily Lampkin", "repasse_janela", 80, 80, 1), "GS422");
const r4 = (await repassar("R0000004", "Cecily Lampkin", "repasse_janela", 80, 79, 2))[0];
confere(r4 && r4.motivo === "Lead sem contato mudou de faixa.", "janela dentro das travas é aceita, com o motivo de antes");
confere((await q(`select count(*)::int n from system_penalidades where reatribuicao_id = $1`, [r4.id]))[0].n === 1, "janela gera a penalidade configurada");

console.log("5. Linha do tempo");
const linha = (await q(`select descricao, tipo from core_linha_do_tempo('R0000001')`));
confere(linha.some((l) => l.tipo === "repasse" && l.descricao === "Redistribuição de domingo. Anna Snelling → Cecily Lampkin"), "mostra 'Redistribuição de domingo. Anna Snelling → Cecily Lampkin'", JSON.stringify(linha));
confere(!linha.some((l) => /Passado para Cecily/.test(l.descricao)), "não duplica como 'Passado para …'");
const linha4 = (await q(`select descricao from core_linha_do_tempo('R0000004')`)).map((l) => l.descricao);
confere(linha4.includes("Lead sem contato mudou de faixa. Anna Snelling → Cecily Lampkin"), "repasse por janela também aparece com o motivo");

console.log("6. Permissões e nada apagado");
const p = await q(`select has_function_privilege('service_role', 'core_repassar_deal(uuid, text, text, text, bigint, smallint, smallint, smallint, text)', 'execute') s,
                          has_function_privilege('anon', 'core_repassar_deal(uuid, text, text, text, bigint, smallint, smallint, smallint, text)', 'execute') a`);
confere(!p[0].s && !p[0].a, "o app (service_role) e anon continuam sem executar o repasse; só o papel de carga");
const auditDepois = (await q(`select count(*)::int n from system_auditoria`))[0].n;
confere(auditDepois > auditAntes, `as trocas passam pela auditoria (${auditAntes} → ${auditDepois})`);
confere((await q(`select count(*)::int n from core_deals where opportunity_id like 'R%'`))[0].n === 5, "nenhum deal apagado");

console.log(falhas ? `\n${falhas} falha(s).` : "\nTudo certo.");
process.exit(falhas ? 1 : 0);
