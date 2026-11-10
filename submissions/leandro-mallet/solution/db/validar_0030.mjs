// Valida a 0030 (Prioridades do dia seguem a nota) num Postgres em memória (PGlite), sem conectar em banco nenhum.
// Uso (Node 20+), numa pasta com o PGlite instalado:
//   npm install @electric-sql/pglite@0.5.11
//   node validar_0030.mjs <solution/db>
// Aplica 0001–0030 e o seed sem contas e deals, monta um cenário próprio e confere:
//   ordem (atendimento atrasado > lead novo com FIT alto > nota > HEAT > id, sem valor esperado);
//   super hot sem ticket; filtro do manager e do admin; troca da execução ativa no meio do dia
//   (não marcados substituídos, marcados ficam, nada apagado); ✓ em item substituído recusado.
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
const confere = (cond, m, detalhe) => (cond ? ok(m) : falha(`${m}${detalhe ? ` — ${detalhe}` : ""}`));
const q = async (sql, p = []) => (await db.query(sql, p)).rows;
const fn = (nome, args) => q(`select * from ${nome}(${args.map((_, i) => `$${i + 1}`).join(", ")})`, args);
const corr = () => randomUUID();
const ids = (linhas) => linhas.map((l) => l.opportunity_id);
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
ok("0001–0030 aplicadas");

console.log("2. Cenário");
const usuario = async (papel, nome) =>
  (await q(`select id from config_usuarios where papel = $1 and ($2::text is null or nome_exibicao = $2)`, [papel, nome ?? null]))[0].id;
const anna = await usuario("vendedor", "Anna Snelling");
const dustin = await usuario("manager", "Dustin Brinkmann");
const admin = await usuario("admin");

// B1 lead do CRM criado há 3 dias, sem contato, FIT 80 → atendimento atrasado (grupo 0)
// B2 deal do dataset com a marca "atendimento_atrasado" da execução → grupo 0
// B3 lead do CRM criado agora, sem nota; FIT 82 pelo vendedor no cohort → lead novo (grupo 1)
// B7 lead do CRM criado agora com FIT 60 → grupo 2, nota 95
// B8 lead do CRM criado agora, FIT 90, mas já com contato → grupo 2, nota 20
// B4/B5 empatam na nota (90): vem antes o de maior HEAT (B5). B6 tem nota 70 e o maior valor esperado.
// B9 em risco (121 dias), nota 10. B10 super hot (47 dias) com produto barato (MG Special): sem ticket, continua super hot.
await db.transaction(async (tx) => {
  await tx.query(`select system_iniciar_contexto_sistema($1)`, [corr()]);
  await tx.exec(`
    insert into core_contas (nome, setor, funcionarios, porte, pais) values ('Hottechi', 'technology', 16499, 'grande', 'United States');
    insert into core_deals (opportunity_id, nome, vendedor_nome, produto_nome, conta_nome, estagio, data_abertura, criado_em) values
      ('B0000001', 'B1', 'Anna Snelling', 'GTX Pro', 'Hottechi', 'Prospecting', null, now() - interval '3 days'),
      ('B0000002', 'B2', 'Anna Snelling', 'GTX Basic', null, 'Prospecting', null, null),
      ('B0000003', 'B3', 'Anna Snelling', 'GTX Pro', 'Hottechi', 'Prospecting', null, now()),
      ('B0000004', 'B4', 'Anna Snelling', 'GTX Basic', null, 'Prospecting', null, null),
      ('B0000005', 'B5', 'Anna Snelling', 'GTX Basic', null, 'Prospecting', null, null),
      ('B0000006', 'B6', 'Anna Snelling', 'GTX Plus Pro', null, 'Prospecting', null, null),
      ('B0000007', 'B7', 'Anna Snelling', 'GTX Basic', null, 'Prospecting', null, now()),
      ('B0000008', 'B8', 'Anna Snelling', 'GTX Basic', null, 'Prospecting', null, now()),
      ('B0000009', 'B9', 'Anna Snelling', 'GTX Basic', null, 'Engaging', '2017-09-01', null),
      ('B0000010', 'B10', 'Anna Snelling', 'MG Special', null, 'Engaging', '2017-11-14', null);
    update core_deals set ultimo_contato_em = '2017-12-30' where opportunity_id = 'B0000008';
    insert into score_execucoes (reference_date, gerado_em, versao, arquivo_sha256) values ('2017-12-31', now(), 't-1', repeat('a', 64));
    insert into score_deals (execucao_id, opportunity_id, vendedor_nome, cohort, fit, heat, score, acao_sugerida, valor_esperado, marcadores) values
      (1, 'B0000001', 'Anna Snelling', 'produto=GTX Pro', 80, 30, 50, 'focar', 100, '{}'),
      (1, 'B0000002', 'Anna Snelling', 'produto=GTX Basic', 76, 10, 40, 'focar', 100, '{atendimento_atrasado}'),
      (1, 'B0000004', 'Anna Snelling', 'produto=GTX Basic', 70, 10, 90, 'focar', 10, '{}'),
      (1, 'B0000005', 'Anna Snelling', 'produto=GTX Basic', 70, 50, 90, 'focar', 10, '{}'),
      (1, 'B0000006', 'Anna Snelling', 'produto=GTX Plus Pro', 70, 90, 70, 'focar', 999999, '{}'),
      (1, 'B0000007', 'Anna Snelling', 'produto=GTX Basic', 60, 90, 95, 'focar', 10, '{}'),
      (1, 'B0000008', 'Anna Snelling', 'produto=GTX Basic', 90, 10, 20, 'focar', 10, '{}'),
      (1, 'B0000009', 'Anna Snelling', 'produto=GTX Basic', 50, 10, 10, 'requalificar', 10, '{risco_esfriar}'),
      (1, 'B0000010', 'Anna Snelling', 'produto=MG Special', 50, 50, 30, 'focar', 55, '{}');
    insert into score_fit_vendedores (execucao_id, vendedor_nome, cohort, produto_nome, taxa_media_movel, casos, fit) values
      (1, 'Anna Snelling', 'produto=GTX Pro', 'GTX Pro', 0.71, 25, 82);
  `);
});
await fn("score_ativar_execucao", [corr(), 1]);
ok("10 deals da Anna e execução 1 ativa");

console.log("3. Ordem");
const icones = Object.fromEntries((await q(`select opportunity_id, icone from core_deals_visao`)).map((r) => [r.opportunity_id, r.icone]));
confere(icones.B0000010 === "super_hot" && icones.B0000009 === "em_risco", "super hot sem ticket: MG Special (US$ 55) com 47 dias é super hot; 121 dias = em risco");
const cortes = (await q(`select valor from config_parametros where chave = 'icone_cortes'`))[0].valor;
confere(cortes.preco_min_quente === null && cortes.dias_min_quente === 15, "icone_cortes: preco_min_quente = null, janela mantida");

const esperado = ["B0000001", "B0000002", "B0000003", "B0000007", "B0000005", "B0000004", "B0000006", "B0000010", "B0000008", "B0000009"];
const lista1 = await fn("acao_prioridades_do_dia", [anna, corr()]);
confere(JSON.stringify(ids(lista1)) === JSON.stringify(esperado),
  "vendedora: atrasado > lead novo FIT ≥ 75 > nota > HEAT no empate; valor esperado não conta", ids(lista1).join(","));
const gravadas = await q(`select count(*)::int n, count(*) filter (where execucao_id = 1)::int e1 from acao_prioridades where usuario_id = $1`, [anna]);
confere(gravadas[0].n === 10 && gravadas[0].e1 === 10, "a lista grava a execução usada (1) em cada item");

const listaDustin = await fn("acao_prioridades_do_dia", [dustin, corr()]);
const filtroPadrao = (await q(`select valor ->> 'filtro' as f from config_parametros where chave = 'prioridades_gestor'`))[0].f;
confere(filtroPadrao === "atencao", "padrão do gestor = 'atencao' (só o que pede ação)");
confere(JSON.stringify(ids(listaDustin)) === JSON.stringify(["B0000001", "B0000002", "B0000003", "B0000009"]),
  "manager (padrão 'atencao'): atendimento atrasado, lead novo com FIT alto e em risco; super hot fora", ids(listaDustin).join(","));

await db.transaction(async (tx) => {
  await tx.query(`select system_iniciar_contexto_sistema($1)`, [corr()]);
  await tx.exec(`update config_parametros set valor = '{"filtro": "icone"}' where chave = 'prioridades_gestor'`);
});
const listaAdmin = await fn("acao_prioridades_do_dia", [admin, corr()]);
confere(JSON.stringify(ids(listaAdmin)) === JSON.stringify(["B0000010", "B0000009"]),
  "admin com o filtro alternativo 'icone': super hot e em risco, pela nota", ids(listaAdmin).join(","));

console.log("4. Troca da execução ativa no meio do dia");
await fn("acao_marcar_prioridade", [anna, corr(), "B0000001", "feita", "ligacao", "Falei com Compras."]);
await fn("acao_marcar_prioridade", [anna, corr(), "B0000002", "pulada", null, null]);
await db.transaction(async (tx) => {
  await tx.query(`select system_iniciar_contexto_sistema($1)`, [corr()]);
  await tx.exec(`
    update core_deals set estagio = 'Lost', close_date = '2017-12-31', close_value = 0, motivo_perda = 'outro' where opportunity_id = 'B0000004';
    insert into score_execucoes (reference_date, gerado_em, versao, arquivo_sha256) values ('2017-12-31', now(), 't-2', repeat('b', 64));
    insert into score_deals (execucao_id, opportunity_id, vendedor_nome, cohort, fit, heat, score, acao_sugerida, valor_esperado, marcadores)
      select 2, opportunity_id, vendedor_nome, cohort, fit, heat,
             case opportunity_id when 'B0000006' then 99 when 'B0000007' then 5 else score end,
             acao_sugerida, valor_esperado, marcadores
        from score_deals where execucao_id = 1;
    insert into score_fit_vendedores (execucao_id, vendedor_nome, cohort, produto_nome, taxa_media_movel, casos, fit)
      select 2, vendedor_nome, cohort, produto_nome, taxa_media_movel, casos, fit from score_fit_vendedores where execucao_id = 1;
  `);
});
await fn("score_ativar_execucao", [corr(), 2]);
const antes = (await q(`select count(*)::int n from acao_prioridades where usuario_id = $1`, [anna]))[0].n;
const lida = await fn("acao_listar_prioridades", [anna]);
confere(lida.length === 0, "lista de execução antiga não é lida (volta vazia; quem chama monta de novo)");

const lista2 = await fn("acao_prioridades_do_dia", [anna, corr()]);
const esperado2 = ["B0000001", "B0000002", "B0000003", "B0000006", "B0000005", "B0000010", "B0000008", "B0000009", "B0000007"];
confere(JSON.stringify(ids(lista2)) === JSON.stringify(esperado2),
  "refeita: ✓ e ✗ ficam; os não marcados voltam pela ordem nova (B6 subiu, B7 desceu, B4 encerrado saiu)", ids(lista2).join(","));
confere(lista2[0].marcada === "feita" && lista2[1].marcada === "pulada", "os marcados continuam com a marca");
const linhas = await q(`select opportunity_id, execucao_id, substituida_em is not null as subst from acao_prioridades where usuario_id = $1 order by posicao`, [anna]);
const depois = linhas.length;
confere(depois === antes, `nenhuma linha apagada nem duplicada (${antes} → ${depois})`);
const b4 = linhas.find((l) => l.opportunity_id === "B0000004");
confere(b4?.subst === true && b4?.execucao_id === 1, "o item que saiu fica gravado como substituído (execução 1)");
const novos = linhas.filter((l) => !l.subst && !["B0000001", "B0000002"].includes(l.opportunity_id));
confere(novos.every((l) => l.execucao_id === 2), "os itens repostos gravam a execução nova (2)");
confere(linhas.filter((l) => ["B0000001", "B0000002"].includes(l.opportunity_id)).every((l) => l.execucao_id === 1 && !l.subst),
  "os marcados ficam com a execução em que foram montados");

const de2 = await fn("acao_listar_prioridades", [anna]);
confere(de2.length === 9, "depois de refeita, a leitura volta a mostrar a lista (9 itens)");
const sem = await fn("acao_prioridades_do_dia", [anna, corr()]);
confere(JSON.stringify(ids(sem)) === JSON.stringify(esperado2), "chamar de novo com a mesma execução não mexe na lista");
await esperaErro("✓ em item substituído (B4)", () => fn("acao_marcar_prioridade", [anna, corr(), "B0000004", "pulada", null, null]), "GS404");
const marcado = await fn("acao_marcar_prioridade", [anna, corr(), "B0000006", "pulada", null, null]);
confere(marcado.length === 1, "✗ num item reposto funciona");
const audit = (await q(`select count(*)::int n from system_auditoria where tabela = 'acao_prioridades' and operacao = 'update'`))[0].n;
confere(audit > 0, `a substituição passa pela auditoria (${audit} alterações registradas)`);

console.log(falhas ? `\n${falhas} falha(s).` : "\nTudo certo.");
process.exit(falhas ? 1 : 0);
