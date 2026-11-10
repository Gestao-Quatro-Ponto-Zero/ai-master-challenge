// Valida LOTE 1 + seed + LOTE 2 num Postgres em memória (PGlite), sem conectar em banco nenhum.
// Base: o validador de app/supabase/scripts (45 verificações de uso), adaptado à pasta oficial solution/db.
//
// Uso (Node 20+), numa pasta com o PGlite instalado:
//   npm install @electric-sql/pglite@0.5.11
//   node validar_tudo.mjs <solution/db> --com-dataset   # dataset inteiro: lote 2 aplica sobre os dados reais + catálogo
//   node validar_tudo.mjs <solution/db>                 # seed sem contas e deals + testes de uso das funções
//
// Ordem: migrations 0001–0006, seed/seed_dataset.sql, migrations 0007 em diante (cada arquivo numa transação).
// Sai com código 1 se algo falhar.

import { PGlite } from "@electric-sql/pglite";
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { randomUUID } from "node:crypto";

const base = process.argv[2];
if (!base) {
  console.error("Informe a pasta solution/db.");
  process.exit(2);
}
const pasta = join(base, "migrations");
const comDataset = process.argv.includes("--com-dataset");
if (comDataset) process.argv.push("--so-catalogo");

const db = new PGlite();
let falhas = 0;
const ok = (msg) => console.log(`  ok   ${msg}`);
const falha = (msg) => { falhas += 1; console.log(`  FALHA ${msg}`); };
const prefixo = /^(core|config|score|acao|system)_/;

async function esperaErro(rotulo, fn, codigo) {
  try {
    await fn();
    falha(`${rotulo}: deveria dar erro ${codigo ?? ""}`);
  } catch (e) {
    if (codigo && e.code !== codigo) falha(`${rotulo}: erro ${e.code} (${e.message}), esperado ${codigo}`);
    else ok(`${rotulo} → recusado (${e.code})`);
  }
}

// Papéis do Supabase, para exercitar os revokes
// Papéis como no Supabase: service_role passa por cima do RLS (bypassrls)
for (const r of ["anon", "authenticated"]) await db.exec(`create role ${r}`);
await db.exec(`create role service_role bypassrls`);

console.log("1. Aplicando migrations");
const arquivos = readdirSync(pasta).filter((f) => /^\d{4}_.*\.sql$/.test(f)).sort();
let seed = readFileSync(join(base, "seed", "seed_dataset.sql"), "utf8");
if (!comDataset) {
  // sem contas e deals do dataset: os testes de uso criam os próprios
  seed = seed.split(/;\n/).filter((c) => !/^\s*insert into core_(contas|deals) /m.test(c)).join(";\n");
}
for (const f of arquivos) {
  const sql = readFileSync(join(pasta, f), "utf8");
  try {
    await db.exec(`begin;
${sql}
commit;`);
    ok(f);
  } catch (e) {
    falha(`${f}: ${e.message}`);
    await db.exec("rollback;").catch(() => {});
    console.log("Parando: as próximas migrations dependem desta.");
    process.exit(1);
  }
  if (f.startsWith("0006_")) {
    try { await db.exec(seed); ok(`seed/seed_dataset.sql${comDataset ? " (dataset inteiro)" : " (sem contas e deals)"}`); }
    catch (e) { falha(`seed: ${e.message}`); process.exit(1); }
  }
}
if (comDataset) {
  const n = async (sql) => (await db.query(sql)).rows[0].n;
  const deals = await n(`select count(*)::int as n from core_deals`);
  const contas = await n(`select count(*)::int as n from core_contas`);
  const fkOk = await n(`select count(*)::int as n from pg_constraint where conname in
    ('core_deals_contato_id_fkey', 'core_deals_importacao_id_fkey', 'system_auditoria_lote_id_fkey') and convalidated`);
  deals === 8800 && contas === 85 ? ok(`dataset preservado depois do lote 2: ${deals} deals, ${contas} contas`) : falha(`dataset: ${deals} deals, ${contas} contas`);
  fkOk === 3 ? ok("as 3 FKs pendentes do lote 1 foram criadas e validadas sobre os dados") : falha(`FKs pendentes: ${fkOk}`);
  const visao = await n(`select count(*)::int as n from core_deals_visao`);
  visao === 8800 ? ok("core_deals_visao lê os 8.800 deals") : falha(`core_deals_visao: ${visao}`);
}

console.log("2. Conferência pelo catálogo");
const q = async (sql, p = []) => (await db.query(sql, p)).rows;

const tabelas = await q(`select relname from pg_class c join pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public' and c.relkind = 'r' order by 1`);
const semPrefixo = tabelas.filter((t) => !prefixo.test(t.relname));
semPrefixo.length ? falha(`tabelas sem prefixo: ${semPrefixo.map((t) => t.relname)}`) : ok(`${tabelas.length} tabelas, todas com prefixo`);

const fks = await q(`select c.conname, c.conrelid::regclass::text as tabela, c.confdeltype, c.confupdtype, c.conkey, c.conrelid
  from pg_constraint c join pg_namespace n on n.oid = c.connamespace where n.nspname = 'public' and c.contype = 'f'`);
const naoRestrict = fks.filter((f) => f.confdeltype !== "r");
naoRestrict.length ? falha(`FK sem ON DELETE RESTRICT: ${naoRestrict.map((f) => f.conname)}`) : ok(`${fks.length} chaves estrangeiras, todas ON DELETE RESTRICT`);
const cascade = fks.filter((f) => f.confdeltype === "c" || f.confupdtype === "c");
cascade.length ? falha(`CASCADE: ${cascade.map((f) => f.conname)}`) : ok("nenhum CASCADE");

const indices = await q(`select i.indrelid, i.indkey::text as cols, i.indpred is null as total
  from pg_index i join pg_class c on c.oid = i.indrelid join pg_namespace n on n.oid = c.relnamespace where n.nspname = 'public'`);
const semIndice = fks.filter((f) => {
  const fkCols = f.conkey.join(" ");
  return !indices.some((i) => i.indrelid === f.conrelid && i.total && (i.cols + " ").startsWith(fkCols + " "));
});
semIndice.length ? falha(`FK sem índice: ${semIndice.map((f) => `${f.tabela}.${f.conname}`)}`) : ok("toda FK tem índice começando pelas colunas dela");

const semRls = await q(`select relname from pg_class c join pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public' and c.relkind = 'r' and not c.relrowsecurity`);
semRls.length ? falha(`sem RLS: ${semRls.map((t) => t.relname)}`) : ok("RLS ligado em todas as tabelas");
const politicas = await q(`select count(*)::int as n from pg_policies where schemaname = 'public' and roles <> array['system_carga']::name[]`);
politicas[0].n === 0 ? ok("nenhuma política de RLS fora do papel de carga (nenhuma para anon, authenticated ou service_role)") : falha(`${politicas[0].n} políticas de RLS fora do papel de carga`);
const execCarga = await q(`select string_agg(p.proname, ', ') as f from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname in ('system_iniciar_contexto_sistema', 'score_ativar_execucao', 'config_gerar_usuarios', 'core_repassar_deal')
    and has_function_privilege('service_role', p.oid, 'execute')`);
execCarga[0].f === null ? ok("service_role não executa as funções de carga (contexto sistema, score, usuários, repasse)") : falha(`service_role executa: ${execCarga[0].f}`);

const semBloqueio = await q(`select c.relname from pg_class c join pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public' and c.relkind = 'r'
    and (not exists (select 1 from pg_trigger g where g.tgrelid = c.oid and g.tgname = c.relname || '_bloquear_delete')
      or not exists (select 1 from pg_trigger g where g.tgrelid = c.oid and g.tgname = c.relname || '_bloquear_truncate'))`);
semBloqueio.length ? falha(`sem bloqueio de DELETE/TRUNCATE: ${semBloqueio.map((t) => t.relname)}`) : ok("bloqueio de DELETE e TRUNCATE em todas as tabelas");

const funcoes = await q(`select p.proname, p.prosrc from pg_proc p join pg_namespace n on n.oid = p.pronamespace where n.nspname = 'public'`);
const funcSemPrefixo = funcoes.filter((f) => !prefixo.test(f.proname));
funcSemPrefixo.length ? falha(`funções sem prefixo: ${funcSemPrefixo.map((f) => f.proname)}`) : ok(`${funcoes.length} funções, todas com prefixo`);
const comDelete = funcoes.filter((f) => /\bdelete\s+from\b/i.test(f.prosrc) || /\btruncate\b/i.test(f.prosrc));
comDelete.length ? falha(`DELETE/TRUNCATE em funções: ${comDelete.map((f) => f.proname)}`) : ok("nenhuma função faz DELETE ou TRUNCATE");

const views = await q(`select viewname from pg_views where schemaname = 'public'`);
const viewsSemPrefixo = views.filter((v) => !prefixo.test(v.viewname));
viewsSemPrefixo.length ? falha(`views sem prefixo: ${viewsSemPrefixo.map((v) => v.viewname)}`) : ok(`${views.length} views, todas com prefixo`);
const viewsInvoker = await q(`select c.relname from pg_class c join pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public' and c.relkind = 'v' and not coalesce(c.reloptions::text like '%security_invoker=true%', false)`);
viewsInvoker.length ? falha(`views sem security_invoker: ${viewsInvoker.map((v) => v.relname)}`) : ok("views com security_invoker");

const gatilhos = await q(`select g.tgname from pg_trigger g join pg_class c on c.oid = g.tgrelid join pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public' and not g.tgisinternal`);
const gatSemPrefixo = gatilhos.filter((g) => !prefixo.test(g.tgname));
gatSemPrefixo.length ? falha(`gatilhos sem prefixo: ${gatSemPrefixo.map((g) => g.tgname)}`) : ok(`${gatilhos.length} gatilhos, todos com prefixo`);

const idx = await q(`select indexname from pg_indexes where schemaname = 'public'`);
const idxSemPrefixo = idx.filter((i) => !prefixo.test(i.indexname));
idxSemPrefixo.length ? falha(`índices sem prefixo: ${idxSemPrefixo.map((i) => i.indexname)}`) : ok(`${idx.length} índices, todos com prefixo`);

const dinheiro = await q(`select table_name || '.' || column_name as col, data_type from information_schema.columns
  where table_schema = 'public' and column_name in ('preco', 'close_value', 'valor_esperado')
    and table_name in (select relname from pg_class where relkind = 'r')`);
const naoInteiro = dinheiro.filter((d) => !["integer", "bigint"].includes(d.data_type));
naoInteiro.length ? falha(`dinheiro fora de inteiro: ${naoInteiro.map((d) => d.col)}`) : ok("dinheiro em inteiro (preco, close_value, valor_esperado)");

const execAnon = await q(`select count(*)::int as n from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and has_function_privilege('anon', p.oid, 'execute')`);
execAnon[0].n === 0 ? ok("anon não executa nenhuma função") : falha(`anon executa ${execAnon[0].n} funções`);
const delServico = await q(`select count(*)::int as n from pg_class c join pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public' and c.relkind = 'r' and has_table_privilege('service_role', c.oid, 'delete')`);
delServico[0].n === 0 ? ok("service_role sem DELETE em nenhuma tabela") : falha(`service_role com DELETE em ${delServico[0].n} tabelas`);

if (process.argv.includes("--so-catalogo")) {
  console.log(falhas ? `\n${falhas} falha(s).` : "\nTudo certo (só aplicação e catálogo).");
  process.exit(falhas ? 1 : 0);
}

console.log("3. Teste de uso");
const fn = (nome, args) => q(`select * from ${nome}(${args.map((_, i) => `$${i + 1}`).join(", ")})`, args);
const corr = () => randomUUID();
const usuario = async (papel, nome) =>
  (await q(`select id from config_usuarios where papel = $1 and ($2::text is null or nome_exibicao = $2)`, [papel, nome ?? null]))[0].id;

const cont = await q(`select papel, count(*)::int as n from config_usuarios group by papel order by papel`);
ok(`usuários gerados: ${cont.map((c) => `${c.papel} ${c.n}`).join(", ")}`);

// Carga do "sistema": 2 contas e 6 deals do dataset, depois uma execução de score
await db.transaction(async (tx) => {
  await tx.query(`select system_iniciar_contexto_sistema($1)`, [corr()]);
  await tx.exec(`
    insert into core_contas (nome, setor, funcionarios, porte, pais) values
      ('Hottechi', 'technology', 16499, 'grande', 'United States'), ('Cancity', 'retail', 2448, 'media', 'United States');
    insert into core_deals (opportunity_id, nome, vendedor_nome, produto_nome, conta_nome, estagio, data_abertura, close_date, close_value) values
      ('AAAA0001', 'Hottechi · GTX Pro', 'Anna Snelling', 'GTX Pro', 'Hottechi', 'Engaging', '2017-11-14', null, null),
      ('AAAA0002', 'Sem empresa · MG Special', 'Anna Snelling', 'MG Special', null, 'Prospecting', null, null, null),
      ('AAAA0003', 'Cancity · GTX Plus Pro', 'Anna Snelling', 'GTX Plus Pro', 'Cancity', 'Engaging', '2017-09-01', null, null),
      ('AAAA0004', 'Cancity · GTX Basic', 'Cecily Lampkin', 'GTX Basic', 'Cancity', 'Engaging', '2017-05-01', null, null),
      ('AAAA0005', 'Hottechi · MG Advanced', 'Anna Snelling', 'MG Advanced', 'Hottechi', 'Won', '2017-10-01', '2017-12-20', 3300),
      ('AAAA0006', 'Cancity · GTX Basic', 'Cecily Lampkin', 'GTX Basic', 'Cancity', 'Lost', '2017-11-20', '2017-12-28', 0);
  `);
  await tx.exec(`
    insert into score_execucoes (reference_date, gerado_em, versao, arquivo_sha256)
      values ('2017-12-31', now(), 'teste-1', repeat('a', 64));
    insert into score_deals (execucao_id, opportunity_id, vendedor_nome, cohort, fit, heat, score, acao_sugerida, valor_esperado) values
      (1, 'AAAA0001', 'Anna Snelling', 'produto=GTX Pro', 80, 70, 77, 'focar', 3200),
      (1, 'AAAA0002', 'Anna Snelling', 'produto=MG Special', 40, 50, 43, 'requalificar', 35),
      (1, 'AAAA0003', 'Anna Snelling', 'produto=GTX Plus Pro', 60, 20, 48, 'requalificar', 3500);
    insert into score_componentes (execucao_id, opportunity_id, grupo, componente, pontos, maximo)
      values (1, 'AAAA0001', 'fit', 'aderência ao cohort', 56, 70);
  `);
  await tx.exec(`
    insert into score_motivos (execucao_id, opportunity_id, ordem, grupo, texto) values (1, 'AAAA0001', 1, 'fit', 'GTX Pro é o produto em que a Anna mais fecha.');
    insert into score_fit_vendedores (execucao_id, vendedor_nome, cohort, produto_nome, taxa_media_movel, casos, fit) values
      (1, 'Anna Snelling', 'produto=GTX Pro', 'GTX Pro', 0.71, 25, 82),
      (1, 'Cecily Lampkin', 'produto=GTX Pro', 'GTX Pro', 0.65, 30, 75),
      (1, 'Lajuana Vencill', 'produto=GTX Pro', 'GTX Pro', 0.90, 4, 95);
  `);
});
await fn("score_ativar_execucao", [corr(), 1]);
ok("carga de contas, deals e score como 'sistema'");

const admin = await usuario("admin");
const anna = await usuario("vendedor", "Anna Snelling");
const dustin = await usuario("manager", "Dustin Brinkmann");

const busca = (await fn("core_buscar_deals", [{ papel: "vendedor", vendedor: "Anna Snelling" }, { estagios: ["Engaging", "Prospecting"] }, "nota", 50, 0]))[0].core_buscar_deals;
busca.total === 3 && busca.linhas[0].opportunity_id === "AAAA0001" ? ok("busca da vendedora: 3 abertos, maior nota primeiro") : falha(`busca: ${JSON.stringify(busca).slice(0, 200)}`);
const icones = Object.fromEntries((await q(`select opportunity_id, icone from core_deals_visao`)).map((r) => [r.opportunity_id, r.icone]));
icones.AAAA0001 === "super_hot" && icones.AAAA0003 === "em_risco" && icones.AAAA0004 === "esfriou" && icones.AAAA0002 === null
  ? ok("ícones: 47 dias e US$ 4.821 = super hot; 121 dias = em risco; 244 dias = esfriou; Prospecção sem ícone")
  : falha(`ícones: ${JSON.stringify(icones)}`);
const filtro = (await fn("core_buscar_deals", [{ papel: "admin" }, { icones: ["esfriou", "em_risco"], contem: "cancity" }, "valor", 50, 0]))[0].core_buscar_deals;
filtro.total === 2 ? ok("etiquetas: (esfriou ou em risco) + contém 'cancity' = 2") : falha(`filtro: ${filtro.total}`);
const colunas = await fn("core_resumir_colunas", [{ papel: "vendedor", vendedor: "Anna Snelling" }, {}]);
colunas.length === 2 ? ok(`colunas do Pipeline: ${colunas.map((c) => `${c.estagio} ${c.quantidade}`).join(", ")}`) : falha("colunas");

// Roteamento: manager cadastra sem vendedor → maior FIT com casos >= 10 (Anna, 82); Lajuana tem FIT 95 mas só 4 casos
const novo = (await fn("core_criar_deal", [dustin, corr(), "GTX Pro", "Hottechi", null, "Prospecting", null, null, null]))[0];
novo.vendedor_nome === "Anna Snelling" ? ok(`roteamento: lead novo ${novo.opportunity_id} foi para Anna Snelling (maior FIT com casos suficientes)`) : falha(`roteamento: ${novo.vendedor_nome}`);
const rota = (await q(`select regra, fit from system_roteamentos where opportunity_id = $1`, [novo.opportunity_id]))[0];
rota.regra === "maior_fit" && rota.fit === 82 ? ok("roteamento registrado (maior_fit, FIT 82)") : falha(`rota: ${JSON.stringify(rota)}`);

// Estágios, conflito de versão, reabrir por papel
let d = (await q(`select * from core_deals where opportunity_id = 'AAAA0002'`))[0];
const versaoVelha = d.atualizado_em;
d = (await fn("core_mudar_estagio", [anna, corr(), "AAAA0002", versaoVelha, "Engaging", null, null, null, null]))[0];
d.estagio === "Engaging" && d.data_abertura ? ok("Prospecção → Em negociação (data de abertura = data de referência)") : falha("mudar estágio");
await esperaErro("conflito de versão (versão antiga)", () => fn("core_mudar_estagio", [anna, corr(), "AAAA0002", versaoVelha, "Lost", null, null, "preco", null]), "GS409");
await esperaErro("Prospecção → Ganho", () => fn("core_mudar_estagio", [anna, corr(), novo.opportunity_id, null, "Won", 100, null, null, null]), "GS422");
await esperaErro("Ganho sem valor", () => fn("core_encerrar_deal", [anna, corr(), "AAAA0002", null, "ganho", null, null, null]), "GS400");
d = (await fn("core_encerrar_deal", [anna, corr(), "AAAA0002", null, "ganho", 60, null, null]))[0];
d.estagio === "Won" && d.close_value === 60 ? ok("Em negociação → Ganho com valor") : falha("ganho");
await esperaErro("vendedora reabrindo deal", () => fn("core_reabrir_deal", [anna, corr(), "AAAA0002", null]), "GS403");
d = (await fn("core_reabrir_deal", [dustin, corr(), "AAAA0002", null]))[0];
d.estagio === "Engaging" && d.close_value === null ? ok("manager reabre deal encerrado") : falha("reabrir");

// Desfazer alteração (janela curta)
const cDesf = corr();
await fn("core_atualizar_deal", [anna, cDesf, "AAAA0003", null, "Cancity · renovação", null, null, false]);
const desf = (await fn("core_desfazer_alteracao", [anna, corr(), cDesf]))[0].core_desfazer_alteracao;
const nomeVolta = (await q(`select nome from core_deals where opportunity_id = 'AAAA0003'`))[0].nome;
desf.restaurados === 1 && nomeVolta === "Cancity · GTX Plus Pro" ? ok("desfazer alteração devolve o nome") : falha(`desfazer: ${JSON.stringify(desf)} ${nomeVolta}`);

// Contato
const contato = (await fn("core_salvar_contato", [anna, corr(), null, "Hottechi", "Maria Souza", "Compras", "maria@hottechi.com", "11 99999-0000", "AAAA0001", null]))[0];
const mascarado = (await q(`select depois->>'email' as e from system_auditoria where tabela = 'core_contatos' order by id desc limit 1`))[0].e;
mascarado === "m***@hottechi.com" ? ok("contato salvo; e-mail mascarado na auditoria") : falha(`máscara: ${mascarado}`);
await esperaErro("contato de outra empresa", () => fn("core_atualizar_deal", [anna, corr(), "AAAA0003", null, null, null, contato.id, false]), "GS422");

// Ações e último contato
const acao = (await fn("acao_registrar", [anna, corr(), "AAAA0001", "liguei", "pediu proposta"]))[0];
let uc = (await q(`select ultimo_contato_em from core_deals where opportunity_id = 'AAAA0001'`))[0].ultimo_contato_em;
uc ? ok("Liguei atualiza o último contato") : falha("último contato");
await fn("acao_desfazer", [anna, corr(), acao.id]);
uc = (await q(`select ultimo_contato_em from core_deals where opportunity_id = 'AAAA0001'`))[0].ultimo_contato_em;
uc === null ? ok("desfazer o Liguei limpa o último contato") : falha("desfazer último contato");
await esperaErro("ação em deal fechado", () => fn("acao_registrar", [anna, corr(), "AAAA0005", "liguei", null]), "GS422");

// Comentários: postar, apagar (lógico), restaurar
const com = (await fn("acao_comentar", [anna, corr(), "AAAA0001", "Cliente pediu desconto."]))[0];
await fn("acao_remover_comentario", [anna, corr(), com.id]);
const removido = (await q(`select removido_em is not null as r from acao_comentarios where id = $1`, [com.id]))[0].r;
const qtd = (await q(`select qtd_comentarios from core_deals_visao where opportunity_id = 'AAAA0001'`))[0].qtd_comentarios;
removido && Number(qtd) === 0 ? ok("apagar comentário = remoção lógica (some da tela, fica no banco)") : falha("remover comentário");
await fn("acao_restaurar_comentario", [anna, corr(), com.id]);
ok("restaurar comentário");
await esperaErro("comentário com HTML", () => fn("acao_comentar", [anna, corr(), "AAAA0001", "<script>x</script>"]), "GS400");

// Tags
await esperaErro("vendedora criando tag", () => fn("config_criar_tag", [anna, corr(), "urgente", "tag-1"]), "GS403");
const tag = (await fn("config_criar_tag", [dustin, corr(), "urgente", "tag-1"]))[0];
await fn("acao_aplicar_tag", [anna, corr(), "AAAA0001", tag.id]);
await fn("acao_aplicar_tag", [anna, corr(), "AAAA0001", tag.id]);
const tags = (await q(`select tags from core_deals_visao where opportunity_id = 'AAAA0001'`))[0].tags;
tags.length === 1 ? ok("tag aplicada uma vez (segunda aplicação não duplica)") : falha(`tags: ${tags}`);
await fn("acao_remover_tag", [anna, corr(), "AAAA0001", tag.id]);
ok("remover tag (lógico)");

// Lote e desfazer lote
const lote = (await fn("system_executar_lote", [dustin, corr(), "encerrar_perdido", { motivo: "sem_resposta" }, ["AAAA0003", "AAAA0004", "AAAA0005"], { icones: ["esfriou"] }]))[0].system_executar_lote;
lote.aplicados === 2 && lote.pulados === 1 ? ok("lote: 2 encerrados como Perdido, 1 pulado (já estava fechado)") : falha(`lote: ${JSON.stringify(lote)}`);
const loteTag = (await fn("system_executar_lote", [dustin, corr(), "aplicar_tag", { tag_id: tag.id }, ["AAAA0001", "AAAA0002"], {}]))[0].system_executar_lote;
loteTag.aplicados === 2 ? ok("lote: tag aplicada em 2") : falha(`lote tag: ${JSON.stringify(loteTag)}`);
const desfLote = (await fn("system_desfazer_lote", [dustin, corr(), lote.lote_id]))[0].system_desfazer_lote;
const voltaram = (await q(`select count(*)::int as n from core_deals where opportunity_id in ('AAAA0003', 'AAAA0004') and estagio = 'Engaging'`))[0].n;
desfLote.restaurados === 2 && voltaram === 2 ? ok("desfazer lote devolve os 2 deals a Em negociação") : falha(`desfazer lote: ${JSON.stringify(desfLote)} ${voltaram}`);
await esperaErro("desfazer o mesmo lote de novo", () => fn("system_desfazer_lote", [dustin, corr(), lote.lote_id]), "GS422");

// Importação: conferir, importar, reimportar
const linhas = [
  { linha: 2, opportunity_id: "IMPT0001", sales_agent: "Anna Snelling", product: "GTX Pro", account: "Hottechi", deal_stage: "Engaging", engage_date: "2017-12-01", close_date: "", close_value: "" },
  { linha: 3, opportunity_id: "IMPT0002", sales_agent: "Ana Snelling", product: "GTX Pro", account: "", deal_stage: "Prospecting", engage_date: "", close_date: "", close_value: "" },
  { linha: 4, opportunity_id: "IMPT0003", sales_agent: "Anna Snelling", product: "MG Special", account: "", deal_stage: "Won", engage_date: "2017-10-01", close_date: "2017-11-01", close_value: "" },
  { linha: 5, opportunity_id: "AAAA0001", sales_agent: "Anna Snelling", product: "GTX Pro", account: "Hottechi", deal_stage: "Engaging", engage_date: "2017-11-14", close_date: "", close_value: "" },
];
await esperaErro("vendedora importando", () => fn("core_importar_deals", [anna, corr(), "x.csv", "b".repeat(64), JSON.stringify(linhas), true]), "GS403");
const conf = (await fn("core_importar_deals", [dustin, corr(), "pipeline.csv", "b".repeat(64), JSON.stringify(linhas), true]))[0].core_importar_deals;
conf.aceitas === 1 && conf.recusadas === 2 && conf.ja_existiam === 1 ? ok(`conferência: 1 aceita, 1 já existia, 2 recusadas (${conf.recusas.map((r) => r.motivo).join(" | ")})`) : falha(`conferência: ${JSON.stringify(conf)}`);
const imp = (await fn("core_importar_deals", [dustin, corr(), "pipeline.csv", "b".repeat(64), JSON.stringify(linhas), false]))[0].core_importar_deals;
const reimp = (await fn("core_importar_deals", [dustin, corr(), "pipeline.csv", "b".repeat(64), JSON.stringify(linhas), false]))[0].core_importar_deals;
imp.aceitas === 1 && reimp.aceitas === 0 && reimp.ja_existiam === 2 ? ok("importar grava 1; reimportar não duplica") : falha(`import: ${JSON.stringify(imp)} / ${JSON.stringify(reimp)}`);

// Prioridades do dia
const lista = await fn("acao_prioridades_do_dia", [anna, corr()]);
lista.length > 0 && lista[0].opportunity_id ? ok(`prioridades da vendedora: ${lista.length} itens, 1º ${lista[0].opportunity_id} (nota ${lista[0].score})`) : falha("prioridades");
// Decisão 37: ✓ exige tipo de atividade e comentário
await esperaErro("✓ sem tipo de atividade (assinatura antiga)", () => fn("acao_marcar_prioridade", [anna, corr(), lista[0].opportunity_id, "feita", null]), "GS400");
await esperaErro("✓ sem comentário", () => fn("acao_marcar_prioridade", [anna, corr(), lista[0].opportunity_id, "feita", "ligacao", " "]), "GS400");
await esperaErro("✓ com tipo inexistente", () => fn("acao_marcar_prioridade", [anna, corr(), lista[0].opportunity_id, "feita", "telepatia", "ok"]), "GS400");
const feita = (await fn("acao_marcar_prioridade", [anna, corr(), lista[0].opportunity_id, "feita", "ligacao", "Falei com Compras; pediu proposta."]))[0];
feita.tipo_atividade === "ligacao" && feita.prioridade_id && feita.nota && feita.criado_em
  ? ok("✓ grava tipo, comentário, item da lista e horário real") : falha(`✓: ${JSON.stringify(feita)}`);
const ucFeita = (await q(`select ultimo_contato_em from core_deals where opportunity_id = $1`, [lista[0].opportunity_id]))[0].ultimo_contato_em;
ucFeita ? ok("✓ com atividade atualiza o último contato") : falha("✓ não atualizou o último contato");
const depois = await fn("acao_prioridades_do_dia", [anna, corr()]);
depois.find((i) => i.opportunity_id === lista[0].opportunity_id).marcada === "feita" ? ok("✓ marcado como feita") : falha("marcar prioridade");
await esperaErro("marcar o mesmo item de novo", () => fn("acao_marcar_prioridade", [anna, corr(), lista[0].opportunity_id, "pulada", null]), "GS422");
const listaManager = await fn("acao_prioridades_do_dia", [dustin, corr()]);
ok(`prioridades do manager: ${listaManager.length} itens (em risco ou super hot do time)`);

// Painel e linha do tempo
const painel = (await fn("core_painel_numeros", [{ papel: "admin" }]))[0].core_painel_numeros;
painel.total_leads >= 8 && painel.fim_de_trimestre === true ? ok(`painel: ${painel.total_leads} leads, ${painel.fechamentos_janela} fechamentos em 30 dias, aviso de fim de trimestre`) : falha(`painel: ${JSON.stringify(painel)}`);
const funil = await fn("core_painel_funil", [{ papel: "admin" }]);
ok(`funil: ${funil.map((f) => `${f.estagio} ${f.quantidade}`).join(", ")}`);
const tempo = await fn("core_linha_do_tempo", ["AAAA0001"]);
const tipos = tempo.map((t) => t.tipo);
tipos.includes("aberto") && tipos.includes("acao") && tipos.includes("comentario") && tipos.includes("tag")
  ? ok(`linha do tempo: ${tipos.join(", ")}`) : falha(`linha do tempo: ${tipos}`);

// Correção de segurança (0022): papel de carga, correlation_id e limite de escritas
await esperaErro("app (service_role) chama o contexto sistema",
  () => db.exec(`set role service_role; select system_iniciar_contexto_sistema(gen_random_uuid());`), "42501");
await db.exec(`reset role`);
await esperaErro("app (service_role) escolhe o usuário sistema",
  () => db.exec(`set role service_role; begin; select system_iniciar_contexto(1, gen_random_uuid()); commit;`), "GS403");
await db.exec(`rollback`).catch(() => {}); await db.exec(`reset role`);
const cReuso = corr();
await db.exec(`begin; select system_iniciar_contexto(${anna}, '${cReuso}'); commit;`);
await esperaErro("correlation_id reaproveitado em outra transação",
  () => db.exec(`begin; select system_iniciar_contexto(${anna}, '${cReuso}'); commit;`), "GS400");
await db.exec(`rollback`).catch(() => {});
const zane = await usuario("vendedor", "Zane Levy");
let bloqueado = 0;
for (let i = 0; i < 32; i++) {
  try { await db.exec(`set role service_role; begin; select system_iniciar_contexto(${zane}, '${corr()}'); commit; reset role;`); }
  catch (e) { await db.exec(`rollback`).catch(() => {}); await db.exec(`reset role`); if (e.code === "GS429") bloqueado = i + 1; break; }
}
bloqueado === 31 ? ok("limite de escritas do app: o 31º pedido no minuto é recusado (GS429), contado pelo banco") : falha(`limite: bloqueou no pedido ${bloqueado}`);

// 0026: teto global (troca de usuário não fura o teto)
await db.exec(`begin; select system_iniciar_contexto_sistema('${corr()}');
  update config_parametros set valor = '40'::jsonb where chave = 'limite_global_escritas'; commit;`);
const outros = (await q(`select id from config_usuarios where papel = 'vendedor' and nome_exibicao not in ('Zane Levy', 'Anna Snelling') order by id`)).map((r) => r.id);
let pedidos = 0, globalMsg = null;
for (let i = 0; i < 60 && !globalMsg; i++) {
  const uid = outros[i % outros.length];             // no máximo 2 pedidos por usuário: bem abaixo do limite individual
  try { await db.exec(`set role service_role; begin; select system_iniciar_contexto(${uid}, '${corr()}'); commit; reset role;`); pedidos += 1; }
  catch (e) { await db.exec(`rollback`).catch(() => {}); await db.exec(`reset role`); if (e.code === "GS429") globalMsg = e.message; else throw e; }
}
globalMsg && /muitas mudanças agora/.test(globalMsg)
  ? ok(`teto global: trocando de usuário, o app é recusado depois de ${pedidos} pedidos (GS429: "${globalMsg}")`)
  : falha(`teto global não disparou (${pedidos} pedidos)`);
await db.exec(`set role system_carga; begin; select system_iniciar_contexto_sistema('${corr()}'); commit; reset role;`);
ok("papel de carga passa mesmo com o teto global atingido");
await db.exec(`begin; select system_iniciar_contexto_sistema('${corr()}');
  update config_parametros set valor = '300'::jsonb where chave = 'limite_global_escritas'; commit;`);
await db.exec(`set role system_carga; begin; select system_iniciar_contexto_sistema('${corr()}');
  insert into core_contas (nome, setor, funcionarios, porte, pais) values ('Carga Teste', 'retail', 10, 'pequena', 'Brazil'); commit; reset role;`);
const cargaOk = (await q(`select a.papel from system_auditoria a where a.tabela = 'core_contas' and a.registro_id = 'Carga Teste'`))[0];
cargaOk && cargaOk.papel === "sistema" ? ok("papel de carga grava como sistema, com auditoria") : falha(`carga: ${JSON.stringify(cargaOk)}`);

// Decisão 38: repasse e penalidade (só o papel de carga)
const exAtiva = (await q(`select score_execucao_ativa() as e`))[0].e;
const repassa = (args) => db.exec(`set role system_carga; begin; select core_repassar_deal('${corr()}', ${args}); commit; reset role;`);
const falhaRepasse = async (rotulo, args, cod) => {
  await esperaErro(rotulo, () => repassa(args), cod);
  await db.exec(`rollback`).catch(() => {}); await db.exec(`reset role`);
};
await falhaRepasse("repasse com FIT do novo abaixo de 75", `'AAAA0004', 'Anna Snelling', 'repasse_janela', ${exAtiva}, 80::smallint, 74::smallint, 1::smallint`, "GS422");
await falhaRepasse("repasse com FIT do novo mais de 3 pontos abaixo do dono", `'AAAA0004', 'Anna Snelling', 'repasse_janela', ${exAtiva}, 80::smallint, 76::smallint, 1::smallint`, "GS422");
await falhaRepasse("repasse fora do top 5", `'AAAA0004', 'Anna Snelling', 'repasse_janela', ${exAtiva}, 80::smallint, 78::smallint, 6::smallint`, "GS422");
await esperaErro("app (service_role) chama o repasse",
  () => db.exec(`set role service_role; select core_repassar_deal(gen_random_uuid(), 'AAAA0004', 'Anna Snelling', 'repasse_janela', null, 80::smallint, 78::smallint, 1::smallint);`), "42501");
await db.exec(`reset role`);
await db.exec(`begin; select system_iniciar_contexto_sistema('${corr()}');
  update config_parametros set valor = '{"pontos": 5, "dias": 7}'::jsonb where chave = 'penalidade_roteamento'; commit;`);
await repassa(`'AAAA0004', 'Anna Snelling', 'repasse_janela', ${exAtiva}, 80::smallint, 78::smallint, 2::smallint, 'em_risco'`);
const rep = (await q(`select d.vendedor_nome, r.origem, r.de_vendedor, (select count(*)::int from system_penalidades p where p.reatribuicao_id = r.id) as pen,
  core_penalidade_ativa(r.de_vendedor) as pontos
  from core_deals d join acao_reatribuicoes r on r.opportunity_id = d.opportunity_id where d.opportunity_id = 'AAAA0004' order by r.id desc limit 1`))[0];
rep.vendedor_nome === "Anna Snelling" && rep.origem === "repasse_janela" && rep.pen === 1 && Number(rep.pontos) === 5
  ? ok(`repasse de janela: lead foi de ${rep.de_vendedor} para Anna; ${rep.de_vendedor} leva 5 pontos de penalidade por 7 dias`)
  : falha(`repasse: ${JSON.stringify(rep)}`);
const teto = (await q(`select (valor ->> 'teto_abertos') as t from config_parametros where chave = 'roteamento'`))[0].t;
teto === null ? ok("roteamento sem teto de abertos (decisão 38)") : falha(`teto: ${teto}`);

// Decisão 33: bonus de 0 a 20 e nota até 120; padrão de compra por conta
await db.transaction(async (tx) => {
  await tx.query(`select system_iniciar_contexto_sistema($1)`, [corr()]);
  await tx.exec(`insert into score_execucoes (reference_date, gerado_em, versao, arquivo_sha256)
                   values ('2017-12-31', now(), 'teste-bonus', repeat('c', 64))`);
});
const exb = (await q(`select max(id)::int as id from score_execucoes`))[0].id;
await db.exec(`insert into score_deals (execucao_id, opportunity_id, vendedor_nome, fit, heat, bonus, score, acao_sugerida, valor_esperado)
               values (${exb}, 'AAAA0001', 'Anna Snelling', 100, 100, 20, 120, 'focar', 3200)`);
ok("nota 120 com bonus 20 aceita");
await esperaErro("nota 121", () => db.exec(`insert into score_deals (execucao_id, opportunity_id, vendedor_nome, score, acao_sugerida, valor_esperado)
               values (${exb}, 'AAAA0003', 'Anna Snelling', 121, 'focar', 1)`), "23514");
await esperaErro("bonus 21", () => db.exec(`insert into score_deals (execucao_id, opportunity_id, vendedor_nome, bonus, score, acao_sugerida, valor_esperado)
               values (${exb}, 'AAAA0003', 'Anna Snelling', 21, 50, 'focar', 1)`), "23514");
await db.exec(`insert into score_padroes_conta (execucao_id, conta_nome, compras_ganhas, receita_ganha, intervalo_tipico_dias,
                 mes_habitual, ultima_compra, proxima_compra_esperada, na_janela, bonus, explicacao)
               values (${exb}, 'Hottechi', 1, 3300, 90, 12, '2017-12-20', '2018-03-20', false, 0, 'Compra a cada 3 meses; a próxima é esperada em março.')`);
ok("padrão de compra por conta gravado");
await esperaErro("padrão de conta inexistente", () => db.exec(`insert into score_padroes_conta (execucao_id, conta_nome, compras_ganhas, receita_ganha)
               values (${exb}, 'Nao Existe', 0, 0)`), "23503");
await esperaErro("DELETE em score_padroes_conta", () => db.exec(`delete from score_padroes_conta`), "GS405");
const bonusVisao = (await q(`select bonus from core_deals_visao where opportunity_id = 'AAAA0001'`))[0].bonus;
bonusVisao === null || bonusVisao === 0 || bonusVisao === 20 ? ok(`core_deals_visao expõe o bonus da execução ativa (${bonusVisao})`) : falha(`bonus na visão: ${bonusVisao}`);

// Bloqueios
await esperaErro("DELETE em core_deals", () => db.exec(`delete from core_deals where opportunity_id = 'AAAA0001'`), "GS405");
await esperaErro("TRUNCATE em acao_comentarios", () => db.exec(`truncate acao_comentarios`), "GS405");
await esperaErro("UPDATE na auditoria", () => db.exec(`update system_auditoria set papel = 'x'`), "GS405");
await esperaErro("escrita sem usuário", () => db.exec(`update core_deals set nome = 'x' where opportunity_id = 'AAAA0001'`), "GS401");
const aud = (await q(`select count(*)::int as n, count(distinct correlation_id)::int as c from system_auditoria`))[0];
ok(`auditoria: ${aud.n} registros, ${aud.c} correlation_ids`);

console.log(falhas ? `\n${falhas} falha(s).` : "\nTudo certo.");
process.exit(falhas ? 1 : 0);
