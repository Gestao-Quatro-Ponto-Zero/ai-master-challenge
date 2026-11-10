import "server-only";
// Motor do score para a rotina diária (O-41): liga a lógica pura da #3 (src/lib/score/) ao banco, pela transação
// da rotina (ctx.sql), com o papel de carga. Grava como a carga em Python (solution/scoring/carregar_score.py):
// só inserts nas score_* e as funções do banco (score_ativar_execucao, core_repassar_deal). Nada de DELETE.
//   - semanal (domingo da data de negócio): FIT da janela de 3 meses e redistribuição (core_repassar_deal,
//     origem 'redistribuicao', só equilíbrio, decisão 47) com a execução ativa como referência;
//   - diário: execução nova (FIT e padrões de conta do último domingo; HEAT e nota de hoje), ativada; depois o repasse
//     por mudança de faixa sem contato (core_repassar_deal, origem 'repasse_janela') com os parâmetros do banco.
// Os parâmetros do repasse vêm de config_parametros.repasse: max_repasses_por_lead null = sem limite; a penalidade
// (config penalidade_roteamento) é do próprio banco e com null não é gravada. Travados pelo manager: nenhum (ainda
// não existe no banco).
import { createHash } from "node:crypto";
import {
  arredondar, celulas, chamadasRedistribuicao, componentes, explicacaoConta, fitVendedores, JANELA_MESES, MINIMO_CASOS,
  ENCOLHIMENTO, notaDoDeal, padroesConta, PESOS, planejarRedistribuicao, planejarRepasses, preparar, VERSAO,
  type ChamadaRepasse, type LinhaConta, type LinhaDeal, type LinhaProduto, type ParametrosRepasse,
} from "@/lib/score";
import type { ContextoRotina, MotorScore, ResumoJob, Sql } from "./contrato";

const TRAVADOS = new Set<string>(); // trava do dono pelo manager: ainda não existe no banco (README, pendências)

/** Domingo da semana da data de negócio (a própria data, se for domingo): referência do FIT e dos padrões. */
export function domingoDaSemana(data: string): string {
  const d = new Date(`${data}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() - d.getUTCDay());
  return d.toISOString().slice(0, 10);
}

async function lerBase(sql: Sql) {
  const [deals, contas, produtos] = await Promise.all([
    sql<LinhaDeal>(
      `select opportunity_id, vendedor_nome, produto_nome, conta_nome, estagio, data_abertura::text, close_date::text,
              close_value, ultimo_contato_em::text, criado_em::text
         from core_deals`,
    ),
    sql<LinhaConta>("select nome, setor, receita_milhoes, funcionarios, pais from core_contas"),
    sql<LinhaProduto>("select nome, serie, preco from core_produtos"),
  ]);
  return { deals, contas, produtos };
}

/** Nota de hoje com o FIT e os padrões do último domingo (como a rotina de domingo + a diária). */
function calcularDoDia(base: Awaited<ReturnType<typeof lerBase>>, hoje: string) {
  const leads = preparar(base.deals, base.contas, base.produtos);
  const refFit = domingoDaSemana(hoje);
  const cel = celulas(leads, refFit);
  const { padroes } = padroesConta(leads, refFit);
  const notas = leads.filter((l) => l.estagio === "Prospecting" || l.estagio === "Engaging").map((l) => notaDoDeal(l, l.vendedor_nome, cel, padroes, hoje));
  return { leads, cel, padroes, notas, refFit };
}

async function repassar(sql: Sql, correlationId: string, chamadas: ChamadaRepasse[]) {
  let feitos = 0;
  for (const c of chamadas) {
    await sql(
      "select (core_repassar_deal($1::uuid, $2, $3, $4, $5::bigint, $6::smallint, $7::smallint, $8::smallint, $9)).id",
      [correlationId, c.p_opportunity_id, c.p_para_vendedor, c.p_origem, c.p_execucao_id || null, c.p_fit_dono, c.p_fit_novo, c.p_posicao_top, c.p_faixa_heat],
    );
    feitos += 1;
  }
  return feitos;
}

async function parametrosRepasse(sql: Sql): Promise<ParametrosRepasse> {
  const [c] = await sql<{ valor: Record<string, number | null> | null }>("select valor from config_parametros where chave = 'repasse'");
  const v = c?.valor ?? {};
  const n = (x: number | null | undefined, padrao: number) => (typeof x === "number" ? x : padrao);
  return {
    fitMinimo: n(v.fit_minimo, 75),
    maxAbaixoDoDono: n(v.max_abaixo_do_dono, 3),
    topN: n(v.top_n, 5),
    maxRepassesPorLead: typeof v.max_repasses_por_lead === "number" ? v.max_repasses_por_lead : null, // null = sem limite
  };
}

/** Vendedores ativos do time (decisão 49: todos são elegíveis na redistribuição; sem histórico entram com FIT 50). */
async function vendedoresAtivos(sql: Sql): Promise<string[]> {
  const linhas = await sql<{ nome: string }>(
    "select distinct v.nome from core_vendedores v join config_usuarios u on u.vendedor_nome = v.nome and u.ativo order by v.nome",
  );
  return linhas.map((l) => l.nome);
}

async function execucaoAtiva(sql: Sql): Promise<number | null> {
  const [r] = await sql<{ id: string | number | null }>("select score_execucao_ativa() as id");
  return r?.id === null || r?.id === undefined ? null : Number(r.id);
}

/** Grava a execução nova (como a carga em Python) e a ativa. Devolve o id. */
async function gravarExecucao(ctx: ContextoRotina, c: ReturnType<typeof calcularDoDia>, base: Awaited<ReturnType<typeof lerBase>>) {
  const { sql, dataNegocio, correlationId } = ctx;
  const deals = [...c.notas].sort((a, b) => (a.opportunity_id < b.opportunity_id ? -1 : 1)).map((n) => ({
    opportunity_id: n.opportunity_id, vendedor_nome: n.vendedor_nome, cohort: n.cohort, fit: arredondar(n.fit), heat: arredondar(n.heat),
    bonus: n.bonus, score: arredondar(n.nota), acao_sugerida: n.acao_sugerida, dias_no_pipeline: n.dias, valor_esperado: n.valor_esperado,
    marcadores: n.marcadores, componentes: componentes(n), motivos: n.motivos.map(([g, t], i) => ({ ordem: i + 1, grupo: g, texto: t })),
  }));
  const fits = fitVendedores(c.cel, base.produtos);
  const padroes = [...c.padroes.values()].sort((a, b) => (a.conta_nome < b.conta_nome ? -1 : 1)).map((p) => ({
    conta_nome: p.conta_nome, compras_ganhas: p.compras_ganhas, receita_ganha: Math.trunc(p.receita_ganha), ultima_compra: p.ultima_compra,
    na_janela: p.na_janela, bonus: p.bonus, explicacao: explicacaoConta(p),
  }));
  const conteudo = JSON.stringify({ dataNegocio, deals, fits, padroes });
  const sha = createHash("sha256").update(`${correlationId}|${conteudo}`).digest("hex");
  const parametros = { origem: "rotina_diaria", referencia_heat: dataNegocio, referencia_fit: c.refFit, janela_meses: JANELA_MESES, minimo_casos: MINIMO_CASOS, encolhimento: ENCOLHIMENTO };
  const [ex] = await sql<{ id: string }>(
    `insert into score_execucoes (reference_date, gerado_em, versao, pesos, parametros, arquivo_sha256, observacao)
     values ($1::date, now(), $2, $3::jsonb, $4::jsonb, $5, $6) returning id`,
    [dataNegocio, VERSAO, JSON.stringify(PESOS), JSON.stringify(parametros), sha, "Rotina diária do score (O-41)."],
  );
  const id = Number(ex!.id);
  const linhas = (dados: unknown) => [id, JSON.stringify(dados)];
  await sql(
    `insert into score_deals (execucao_id, opportunity_id, vendedor_nome, cohort, fit, heat, bonus, score, acao_sugerida, dias_no_pipeline, valor_esperado, marcadores)
     select $1, x.opportunity_id, x.vendedor_nome, x.cohort, x.fit, x.heat, x.bonus, x.score, x.acao_sugerida, x.dias_no_pipeline, x.valor_esperado,
            array(select jsonb_array_elements_text(x.marcadores))
       from jsonb_to_recordset($2::jsonb) as x(opportunity_id text, vendedor_nome text, cohort text, fit smallint, heat smallint, bonus smallint,
            score smallint, acao_sugerida text, dias_no_pipeline integer, valor_esperado integer, marcadores jsonb)`,
    linhas(deals.map((d) => ({
      opportunity_id: d.opportunity_id, vendedor_nome: d.vendedor_nome, cohort: d.cohort, fit: d.fit, heat: d.heat, bonus: d.bonus, score: d.score,
      acao_sugerida: d.acao_sugerida, dias_no_pipeline: d.dias_no_pipeline, valor_esperado: d.valor_esperado, marcadores: d.marcadores,
    }))),
  );
  await sql(
    `insert into score_componentes (execucao_id, opportunity_id, grupo, componente, pontos, maximo)
     select $1, x.opportunity_id, x.grupo, x.componente, x.pontos, x.maximo
       from jsonb_to_recordset($2::jsonb) as x(opportunity_id text, grupo text, componente text, pontos numeric, maximo numeric)`,
    linhas(deals.flatMap((d) => d.componentes.map((k) => ({ opportunity_id: d.opportunity_id, ...k })))),
  );
  await sql(
    `insert into score_motivos (execucao_id, opportunity_id, ordem, grupo, texto)
     select $1, x.opportunity_id, x.ordem, x.grupo, x.texto from jsonb_to_recordset($2::jsonb) as x(opportunity_id text, ordem smallint, grupo text, texto text)`,
    linhas(deals.flatMap((d) => d.motivos.map((m) => ({ opportunity_id: d.opportunity_id, ...m })))),
  );
  await sql(
    `insert into score_fit_vendedores (execucao_id, vendedor_nome, cohort, produto_nome, taxa_media_movel, casos, fit, janela_inicio, janela_fim)
     select $1, x.vendedor_nome, x.cohort, x.produto_nome, x.taxa_media_movel, x.casos, x.fit, x.janela_inicio, x.janela_fim
       from jsonb_to_recordset($2::jsonb) as x(vendedor_nome text, cohort text, produto_nome text, taxa_media_movel numeric, casos integer, fit smallint,
            janela_inicio date, janela_fim date)`,
    linhas(fits),
  );
  await sql(
    `insert into score_padroes_conta (execucao_id, conta_nome, compras_ganhas, receita_ganha, ultima_compra, na_janela, bonus, explicacao)
     select $1, x.conta_nome, x.compras_ganhas, x.receita_ganha, x.ultima_compra, x.na_janela, x.bonus, x.explicacao
       from jsonb_to_recordset($2::jsonb) as x(conta_nome text, compras_ganhas integer, receita_ganha integer, ultima_compra date, na_janela boolean,
            bonus smallint, explicacao text)`,
    linhas(padroes),
  );
  await sql("select score_ativar_execucao($1::uuid, $2::bigint)", [correlationId, id]);
  return { id, deals: deals.length, fits: fits.length, padroes: padroes.length };
}

export const motorScore: MotorScore = {
  async semanal(ctx): Promise<ResumoJob> {
    const base = await lerBase(ctx.sql);
    const c = calcularDoDia(base, ctx.dataNegocio);
    const ativa = await execucaoAtiva(ctx.sql);
    if (ativa === null) return { redistribuidos: 0, motivo: "sem execução ativa" };
    // Elegíveis = os vendedores ativos do time (decisão 49), não só os que têm histórico na janela.
    const ativos = await vendedoresAtivos(ctx.sql);
    if (!ativos.length) return { redistribuidos: 0, motivo: "sem vendedores ativos" };
    const plano = planejarRedistribuicao(c.leads, c.notas, c.cel, TRAVADOS, ativos);
    const feitos = await repassar(ctx.sql, ctx.correlationId, chamadasRedistribuicao(plano.trocas, ativa));
    return { referencia_fit: c.refFit, elegiveis: plano.elegiveis.length, limite: plano.limite, avaliados: plano.trocas.length, redistribuidos: feitos };
  },

  async diario(ctx): Promise<ResumoJob> {
    const base = await lerBase(ctx.sql);
    const c = calcularDoDia(base, ctx.dataNegocio);
    // 1) Repasse por mudança de faixa sem contato, com os parâmetros e as contagens do banco. Vem antes da execução
    //    nova para que a nota de hoje já saia com o dono novo (a reatribuição aponta para a execução ativa).
    const ativa = await execucaoAtiva(ctx.sql);
    const [par, contagens, penalidades, repassadosHoje] = await Promise.all([
      parametrosRepasse(ctx.sql),
      ctx.sql<{ opportunity_id: string; n: number }>(
        "select opportunity_id, count(*)::int as n from acao_reatribuicoes where origem in ('repasse_janela', 'redistribuicao') group by opportunity_id",
      ),
      ctx.sql<{ vendedor_nome: string; pontos: number }>(
        "select vendedor_nome, sum(pontos)::float as pontos from system_penalidades where now() between inicio and fim group by vendedor_nome",
      ),
      // Lead já repassado por janela hoje não é repassado de novo (rodada forçada no mesmo dia).
      ctx.sql<{ opportunity_id: string }>(
        `select distinct opportunity_id from acao_reatribuicoes
          where origem = 'repasse_janela' and (criado_em at time zone coalesce(config_texto('fuso_horario'), 'UTC'))::date = system_dia_real()`,
      ),
    ]);
    const r = planejarRepasses(c.leads, c.notas, c.cel, ctx.dataNegocio, ativa ?? 0, {
      parametros: par,
      travados: new Set([...TRAVADOS, ...repassadosHoje.map((x) => x.opportunity_id)]),
      repassesPorLead: new Map(contagens.map((x) => [x.opportunity_id, Number(x.n)])),
      penalidades: new Map(penalidades.map((x) => [x.vendedor_nome, Number(x.pontos)])),
    });
    const feitos = await repassar(ctx.sql, ctx.correlationId, r.chamadas);
    // 2) Execução nova (HEAT e nota de hoje), com os donos depois do repasse, e ativação.
    const baseFinal = feitos ? await lerBase(ctx.sql) : base;
    const ex = await gravarExecucao(ctx, feitos ? calcularDoDia(baseFinal, ctx.dataNegocio) : c, baseFinal);
    // Lead novo sem dono: core_deals.vendedor_nome é obrigatório e o banco já roteia na criação (core_rotear_lead).
    const [semDono] = await ctx.sql<{ n: number }>("select count(*)::int as n from core_deals where vendedor_nome is null");
    return {
      execucao_id: ex.id, deals: ex.deals, fit_vendedores: ex.fits, padroes_conta: ex.padroes, referencia_fit: c.refFit,
      repasses: feitos, fila_manager: r.filaManager.length, sem_dono: Number(semDono?.n ?? 0),
    };
  },
};
