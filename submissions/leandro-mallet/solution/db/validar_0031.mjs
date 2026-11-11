// Valida a 0031 (funil com 5 etapas) num Postgres em memória (PGlite), sem conectar em banco nenhum.
// Uso (Node 20+), numa pasta com o PGlite instalado:
//   npm install @electric-sql/pglite@0.5.11
//   node validar_0031.mjs <solution/db>
// Confere: "Fechado" no rótulo; registro de atendimento (tipo e comentário obrigatórios, deal aberto) leva o lead
// de Novo lead para Atendimento (ultimo_contato_em preenchido); linha do tempo; regra da ação; nada apagado.
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
async function esperaErro(rotulo, f, codigo) {
  try { await f(); falha(`${rotulo}: deveria dar erro ${codigo}`); }
  catch (e) { e.code === codigo ? ok(`${rotulo} → recusado (${e.code})`) : falha(`${rotulo}: ${e.code} ${e.message}`); }
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
ok("0001–0031 aplicadas");

console.log("2. Cenário");
const anna = (await q(`select id from config_usuarios where nome_exibicao = 'Anna Snelling'`))[0].id;
await db.transaction(async (tx) => {
  await tx.query(`select system_iniciar_contexto_sistema($1)`, [corr()]);
  await tx.exec(`
    insert into core_deals (opportunity_id, nome, vendedor_nome, produto_nome, conta_nome, estagio, data_abertura, close_date, close_value) values
      ('C0000001', 'C1', 'Anna Snelling', 'GTX Pro', null, 'Prospecting', null, null, null),
      ('C0000002', 'C2', 'Anna Snelling', 'GTX Pro', null, 'Won', '2017-11-01', '2017-12-20', 3300);
  `);
});
ok("um lead novo (sem contato) e um fechado");

console.log("3. Rótulo e linha do tempo");
confere((await q(`select core_rotulo_estagio('Won') r`))[0].r === "Fechado", "Won aparece como Fechado");
const fechado = (await fn("core_linha_do_tempo", ["C0000002"])).map((l) => l.descricao);
confere(fechado.includes("Fechado: R$ 3300"), "fechamento do dataset: Fechado: R$ …", fechado.join(" | "));

console.log("4. Registro de atendimento");
const antes = (await q(`select count(*)::int n from acao_registros`))[0].n;
await esperaErro("sem tipo", () => fn("acao_registrar_contato", [anna, corr(), "C0000001", null, "Falei com ele."]), "GS400");
await esperaErro("tipo que não conta como contato", async () => {
  await db.transaction(async (tx) => {
    await tx.query(`select system_iniciar_contexto_sistema($1)`, [corr()]);
    await tx.exec(`update config_tipos_atividade set conta_como_contato = false where codigo = 'sem_resposta'`);
  });
  await fn("acao_registrar_contato", [anna, corr(), "C0000001", "sem_resposta", "Não atendeu."]);
}, "GS400");
await esperaErro("comentário só com espaços", () => fn("acao_registrar_contato", [anna, corr(), "C0000001", "ligacao", "   "]), "GS400");
await esperaErro("comentário com HTML", () => fn("acao_registrar_contato", [anna, corr(), "C0000001", "ligacao", "<b>oi</b>"]), "GS400");
await esperaErro("deal fechado", () => fn("acao_registrar_contato", [anna, corr(), "C0000002", "ligacao", "Pós-venda."]), "GS422");
await esperaErro("deal inexistente", () => fn("acao_registrar_contato", [anna, corr(), "ZZZZZZZZ", "ligacao", "x"]), "GS404");
await esperaErro("ação contato direto na tabela sem tipo", () => db.transaction(async (tx) => {
  await tx.query(`select system_iniciar_contexto_sistema($1)`, [corr()]);
  await tx.exec(`insert into acao_registros (opportunity_id, usuario_id, papel, acao, nota, data_negocio) values ('C0000001', ${anna}, 'vendedor', 'contato', 'x', '2017-12-31')`);
}), "23514");

const r = (await fn("acao_registrar_contato", [anna, corr(), "C0000001", "ligacao", "  Pediu a proposta.  "]))[0];
confere(r.acao === "contato" && r.tipo_atividade === "ligacao" && r.nota === "Pediu a proposta.", "registro gravado com tipo e comentário sem espaços nas pontas");
const deal = (await q(`select estagio, ultimo_contato_em from core_deals where opportunity_id = 'C0000001'`))[0];
confere(deal.estagio === "Prospecting" && deal.ultimo_contato_em !== null, "o lead continua Prospecting e ganha contato registrado (Novo lead → Atendimento)");
const linha = (await fn("core_linha_do_tempo", ["C0000001"])).map((l) => l.descricao);
confere(linha.some((t) => t === 'Atendimento: Ligação — "Pediu a proposta."'), "linha do tempo: Atendimento: Ligação — \"comentário\"", linha.join(" | "));
const depois = (await q(`select count(*)::int n from acao_registros`))[0].n;
confere(depois === antes + 1, `nada apagado (${antes} → ${depois})`);

console.log("5. Permissões");
const exec = await q(`select has_function_privilege('anon', 'acao_registrar_contato(bigint, uuid, text, text, text)', 'execute') a,
                             has_function_privilege('service_role', 'acao_registrar_contato(bigint, uuid, text, text, text)', 'execute') s`);
confere(!exec[0].a && exec[0].s, "anon não executa; service_role executa");

console.log(falhas ? `\n${falhas} falha(s).` : "\nTudo certo.");
process.exit(falhas ? 1 : 0);
