/**
 * Drill-down (D46, ISC-40): a click on a bar or slice opens that slice of the data — for example
 * "motivo = Recursos" on the reasons chart — and breaks it down by every other attribute, lists the
 * records behind it, compares the accounts in it with the rest of the base and crosses two
 * attributes the user picks. A click inside the drill adds one more condition (the path).
 *
 * Three universes, one per identifier (D23): churn events (account level), accounts, and
 * subscriptions. Each universe has a fixed catalogue of dimensions written here, never by the
 * client. A path value only enters SQL after it matched a value that query returns from the
 * database (the rule the global filters already follow), so no free text reaches a query.
 */
import { runQuery } from "./warehouse";
import { type Filtros, whereConta, whereAssinatura } from "./filtros";
import { motivoPt } from "./tela2";
import { semAlertaTicket, semAlertaUso } from "./tela3";

export type Universo = "evento" | "conta" | "assinatura" | "ticket" | "uso";

interface Dimensao {
  id: string;
  titulo: string;
  /** SQL expression over the universe's aliases (c = churn_events, a = accounts, s = subscriptions). Always TEXT. */
  expr: string;
  /** Natural order (months, years) instead of by size. */
  ordenarPorRotulo?: boolean;
  rotulo?: (v: string) => string;
}

const simNao = (col: string) => `CASE WHEN ${col} = 1 THEN 'Sim' ELSE 'Não' END`;

const CONTA: Dimensao[] = [
  { id: "setor", titulo: "indústria", expr: "a.industry" },
  { id: "pais", titulo: "país", expr: "a.country" },
  { id: "origem", titulo: "origem", expr: "a.referral_source" },
  { id: "plano_conta", titulo: "plano da conta", expr: "a.plan_tier" },
  { id: "trial_conta", titulo: "conta em teste", expr: simNao("a.is_trial") },
  { id: "coorte", titulo: "ano de entrada", expr: "substr(a.signup_date, 1, 4)", ordenarPorRotulo: true },
  {
    id: "porte",
    titulo: "porte (assentos)",
    expr: "CASE WHEN a.seats <= 5 THEN '01–05' WHEN a.seats <= 20 THEN '06–20' WHEN a.seats <= 50 THEN '21–50' ELSE '51+' END",
    ordenarPorRotulo: true,
  },
];

const EVENTO: Dimensao[] = [
  { id: "motivo", titulo: "motivo declarado", expr: "coalesce(c.reason_code, '(vazio)')", rotulo: motivoPt },
  { id: "mes", titulo: "mês do evento", expr: "substr(c.churn_date, 1, 7)", ordenarPorRotulo: true },
  { id: "feedback", titulo: "comentário do cliente", expr: "coalesce(nullif(trim(c.feedback_text), ''), '(sem comentário)')" },
  { id: "reativacao", titulo: "é reativação", expr: simNao("c.is_reactivation") },
  { id: "upgrade_antes", titulo: "upgrade antes", expr: simNao("c.preceding_upgrade_flag") },
  { id: "downgrade_antes", titulo: "downgrade antes", expr: simNao("c.preceding_downgrade_flag") },
  { id: "reembolso", titulo: "teve reembolso", expr: "CASE WHEN c.refund_amount_usd > 0 THEN 'Sim' ELSE 'Não' END" },
  ...CONTA,
];

const CONTA_UNIVERSO: Dimensao[] = [{ id: "churn_flag", titulo: "conta com churn (churn_flag)", expr: simNao("a.churn_flag") }, ...CONTA];

const ASSINATURA: Dimensao[] = [
  { id: "plano_assin", titulo: "plano da assinatura", expr: "s.plan_tier" },
  { id: "cobranca", titulo: "cobrança", expr: "CASE s.billing_frequency WHEN 'monthly' THEN 'Mensal' ELSE 'Anual' END" },
  { id: "trial_assin", titulo: "assinatura em teste", expr: simNao("s.is_trial") },
  { id: "renovacao", titulo: "renovação automática", expr: simNao("s.auto_renew_flag") },
  { id: "churn_assin", titulo: "assinatura com churn (churn_flag)", expr: simNao("s.churn_flag") },
  { id: "inicio", titulo: "ano de início", expr: "substr(s.start_date, 1, 4)", ordenarPorRotulo: true },
  ...CONTA,
];

const TICKET: Dimensao[] = [
  { id: "prioridade", titulo: "prioridade", expr: "CASE t.priority WHEN 'low' THEN 'Baixa' WHEN 'medium' THEN 'Média' WHEN 'high' THEN 'Alta' ELSE 'Urgente' END" },
  { id: "nota", titulo: "nota de satisfação", expr: "coalesce('Nota ' || t.satisfaction_score, 'Sem nota')", ordenarPorRotulo: true },
  {
    id: "resolucao",
    titulo: "tempo de resolução",
    expr: "CASE WHEN t.resolution_time_hours IS NULL THEN 'Sem registro' WHEN t.resolution_time_hours <= 12 THEN 'Até 12 h' WHEN t.resolution_time_hours <= 24 THEN '12 a 24 h' WHEN t.resolution_time_hours <= 48 THEN '24 a 48 h' ELSE 'Mais de 48 h' END",
  },
  {
    id: "resposta",
    titulo: "tempo até a 1ª resposta",
    expr: "CASE WHEN t.first_response_time_minutes IS NULL THEN 'Sem registro' WHEN t.first_response_time_minutes <= 30 THEN 'Até 30 min' WHEN t.first_response_time_minutes <= 60 THEN '30 a 60 min' WHEN t.first_response_time_minutes <= 120 THEN '1 a 2 h' ELSE 'Mais de 2 h' END",
  },
  { id: "escalado", titulo: "escalado", expr: simNao("t.escalation_flag") },
  { id: "mes_ticket", titulo: "mês de abertura", expr: "substr(t.submitted_at, 1, 7)", ordenarPorRotulo: true },
  { id: "churn_flag", titulo: "conta com churn (churn_flag)", expr: simNao("a.churn_flag") },
  ...CONTA,
];

const USO: Dimensao[] = [
  { id: "recurso", titulo: "recurso", expr: "u.feature_name", rotulo: (v) => v.replace(/^feature_/, "Recurso ") },
  { id: "beta", titulo: "uso beta", expr: simNao("u.is_beta_feature") },
  { id: "mes_uso", titulo: "mês do uso", expr: "substr(u.usage_date, 1, 7)", ordenarPorRotulo: true },
  { id: "plano_assin", titulo: "plano da assinatura", expr: "s.plan_tier" },
  { id: "com_erro", titulo: "registro com erro", expr: "CASE WHEN u.error_count > 0 THEN 'Sim' ELSE 'Não' END" },
  { id: "churn_flag", titulo: "conta com churn (churn_flag)", expr: simNao("a.churn_flag") },
  ...CONTA,
];

interface Def {
  nome: string;
  unidade: string;
  dims: Dimensao[];
  from: string;
  where: (f: Filtros) => string;
  /** Measure columns: `valor` is the headline; `contas` the distinct accounts. */
  medida: string;
  conta: string;
  /** % with churn_flag = 1 (accounts and subscriptions; D36). */
  taxa?: string;
}

const UNIVERSOS: Record<Universo, Def> = {
  evento: {
    nome: "eventos de churn",
    unidade: "eventos",
    dims: EVENTO,
    from: "churn_events c JOIN accounts a ON a.account_id = c.account_id",
    where: (f) => whereConta(f),
    medida: "count(*)",
    conta: "c.account_id",
  },
  conta: {
    nome: "contas",
    unidade: "contas",
    dims: CONTA_UNIVERSO,
    from: "accounts a",
    where: (f) => whereConta(f),
    medida: "count(*)",
    conta: "a.account_id",
    taxa: "round(100.0 * avg(a.churn_flag), 1)",
  },
  assinatura: {
    nome: "assinaturas",
    unidade: "assinaturas",
    dims: ASSINATURA,
    from: "subscriptions s JOIN accounts a ON a.account_id = s.account_id",
    where: (f) => whereAssinatura(f),
    medida: "count(*)",
    conta: "s.account_id",
    taxa: "round(100.0 * avg(s.churn_flag), 1)",
  },
  ticket: {
    nome: "tickets de suporte",
    unidade: "tickets",
    dims: TICKET,
    from: "support_tickets t JOIN accounts a ON a.account_id = t.account_id",
    where: (f) => whereConta(f) + semAlertaTicket(f),
    medida: "count(*)",
    conta: "t.account_id",
  },
  uso: {
    nome: "uso do produto",
    unidade: "usos",
    dims: USO,
    from: "feature_usage u JOIN subscriptions s ON s.subscription_id = u.subscription_id JOIN accounts a ON a.account_id = s.account_id",
    where: (f) => whereAssinatura(f) + semAlertaUso(f),
    medida: "sum(u.usage_count)",
    conta: "s.account_id",
  },
};

export interface Passo {
  dim: string;
  valor: string;
}

export interface PedidoRecorte {
  universo: Universo;
  caminho: Passo[];
  /** Two dimension ids to cross (optional). */
  cruzar?: [string, string];
}

export interface Quebra {
  dim: string;
  titulo: string;
  dados: { label: string; chave: string; value: number; contas: number; taxa?: number }[];
  sql: string;
}

export interface ResultadoRecorte {
  universo: Universo;
  nomeUniverso: string;
  unidade: string;
  caminho: (Passo & { tituloDim: string; rotulo: string })[];
  total: number;
  totalUniverso: number;
  contas: number;
  sqlTotal: string;
  quebras: Quebra[];
  registros: { colunas: string[]; linhas: Record<string, unknown>[]; total: number; sql: string };
  perfil: { linhas: { metrica: string; recorte: number | null; resto: number | null; formato: "int" | "dec" | "pct" | "usd" }[]; sql: string } | null;
  cruzamento: { linhas: string[]; colunas: string[]; celulas: number[][]; sql: string; titulo: string } | null;
  dimensoes: { id: string; titulo: string }[];
}

const lit = (v: string): string => `'${v.replace(/'/g, "''")}'`;
const num = (v: unknown): number => Number(v ?? 0);

export function isUniverso(u: unknown): u is Universo {
  return u === "evento" || u === "conta" || u === "assinatura" || u === "ticket" || u === "uso";
}

function dimensao(def: Def, id: string): Dimensao {
  const d = def.dims.find((x) => x.id === id);
  if (!d) throw new Error(`dimensão desconhecida: ${id}`);
  return d;
}

/**
 * The WHERE for the path, one condition at a time. Each value is checked against the values the
 * dimension really has inside the slice so far; an unknown value is refused.
 */
function whereCaminho(def: Def, f: Filtros, caminho: Passo[]): string[] {
  const conds = [def.where(f)];
  for (const p of caminho) {
    const d = dimensao(def, p.dim);
    const existe = runQuery(`SELECT 1 AS ok FROM ${def.from} WHERE ${conds.join(" AND ")} AND (${d.expr}) = ${lit(p.valor)} LIMIT 1`).rows.length > 0;
    if (!existe) throw new Error(`valor fora da base: ${d.titulo} = ${p.valor}`);
    conds.push(`(${d.expr}) = ${lit(p.valor)}`);
  }
  return conds;
}

const rotular = (d: Dimensao, v: string) => (d.rotulo ? d.rotulo(v) : v);

const RECORDS: Record<Universo, string> = {
  evento:
    "c.churn_date AS data, a.account_name AS conta, a.industry AS industria, a.country AS pais, a.plan_tier AS plano, coalesce(c.reason_code, '') AS motivo, c.refund_amount_usd AS reembolso_usd, coalesce(c.feedback_text, '') AS comentario",
  conta:
    "a.account_id AS id, a.account_name AS conta, a.industry AS industria, a.country AS pais, a.plan_tier AS plano, a.seats AS assentos, substr(a.signup_date, 1, 10) AS entrada, a.churn_flag AS churn_flag",
  assinatura:
    "s.subscription_id AS id, a.account_name AS conta, s.plan_tier AS plano, s.billing_frequency AS cobranca, s.mrr_amount AS mrr_usd, substr(s.start_date, 1, 10) AS inicio, substr(coalesce(s.end_date, ''), 1, 10) AS fim, s.churn_flag AS churn_flag",
  ticket:
    "t.ticket_id AS id, substr(t.submitted_at, 1, 10) AS aberto, a.account_name AS conta, t.priority AS prioridade, t.resolution_time_hours AS resolucao_h, t.first_response_time_minutes AS resposta_min, t.satisfaction_score AS nota, t.escalation_flag AS escalado",
  uso:
    "u.usage_id AS id, substr(u.usage_date, 1, 10) AS data, a.account_name AS conta, u.feature_name AS recurso, u.usage_count AS usos, u.error_count AS erros, u.is_beta_feature AS beta, s.plan_tier AS plano",
};
const ORDEM_REGISTROS: Record<Universo, string> = { evento: "c.churn_date DESC", conta: "a.signup_date DESC", assinatura: "s.start_date DESC", ticket: "t.submitted_at DESC", uso: "u.usage_date DESC" };

/** The slice: total, breakdowns by every other dimension, records, profile and the optional cross. */
export function recorte(f: Filtros, pedido: PedidoRecorte): ResultadoRecorte {
  const def = UNIVERSOS[pedido.universo];
  if (!def) throw new Error("universo desconhecido");
  if (pedido.caminho.length > 6) throw new Error("caminho longo demais");
  const conds = whereCaminho(def, f, pedido.caminho);
  const where = conds.join(" AND ");
  const usados = new Set(pedido.caminho.map((p) => p.dim));

  const totalSql = `SELECT ${def.medida} AS valor, count(DISTINCT ${def.conta}) AS contas FROM ${def.from} WHERE ${where}`;
  const t = runQuery(totalSql).rows[0] ?? {};
  const totalUniverso = num(runQuery(`SELECT ${def.medida} AS valor FROM ${def.from} WHERE ${def.where(f)}`).rows[0]?.valor);

  const quebras: Quebra[] = def.dims
    .filter((d) => !usados.has(d.id))
    .map((d) => {
      const sql = `SELECT ${d.expr} AS chave, ${def.medida} AS valor, count(DISTINCT ${def.conta}) AS contas${def.taxa ? `, ${def.taxa} AS taxa` : ""}
FROM ${def.from}
WHERE ${where}
GROUP BY chave ORDER BY ${d.ordenarPorRotulo ? "chave" : "valor DESC, chave"}`;
      const r = runQuery(sql);
      return {
        dim: d.id,
        titulo: d.titulo,
        dados: r.rows.map((row) => ({ chave: String(row.chave), label: rotular(d, String(row.chave)), value: num(row.valor), contas: num(row.contas), ...(row.taxa !== undefined ? { taxa: num(row.taxa) } : {}) })),
        sql: r.sql,
      };
    })
    // A breakdown with one value says nothing (everyone is "Não"); dimensions with dozens of values
    // (months) stay, the chart handles them.
    .filter((q) => q.dados.length > 1);

  const regSql = `SELECT ${RECORDS[pedido.universo]} FROM ${def.from} WHERE ${where} ORDER BY ${ORDEM_REGISTROS[pedido.universo]} LIMIT 200`;
  const reg = runQuery(regSql);

  return {
    universo: pedido.universo,
    nomeUniverso: def.nome,
    unidade: def.unidade,
    caminho: pedido.caminho.map((p) => {
      const d = dimensao(def, p.dim);
      return { ...p, tituloDim: d.titulo, rotulo: rotular(d, p.valor) };
    }),
    total: num(t.valor),
    totalUniverso,
    contas: num(t.contas),
    sqlTotal: runQuery(totalSql).sql,
    quebras,
    registros: { colunas: reg.columns, linhas: reg.rows, total: num(t.valor), sql: reg.sql },
    perfil: pedido.caminho.length ? perfil(def, f, where) : null,
    cruzamento: pedido.cruzar ? cruzamento(def, where, pedido.cruzar) : null,
    dimensoes: def.dims.map((d) => ({ id: d.id, titulo: d.titulo })),
  };
}

/**
 * The accounts in the slice against the rest of the base (other data crossed in): revenue,
 * support and usage per account, from vw_conta (each number on its own identifier, D23).
 */
function perfil(def: Def, f: Filtros, where: string): ResultadoRecorte["perfil"] {
  const sql = `WITH recorte AS (SELECT DISTINCT ${def.conta} AS account_id FROM ${def.from} WHERE ${where})
SELECT CASE WHEN v.account_id IN (SELECT account_id FROM recorte) THEN 'recorte' ELSE 'resto' END AS grupo,
  count(*) AS contas,
  round(avg(v.assin_soma_mrr_sem_end_date), 0) AS mrr_ativo_medio_usd,
  round(avg(v.assin_soma_seats), 1) AS assentos_medios,
  round(avg(v.tickets_total), 2) AS tickets_por_conta,
  round(avg(v.tickets_media_satisfacao), 2) AS satisfacao_media,
  round(100.0 * sum(v.tickets_escalados) / nullif(sum(v.tickets_total), 0), 1) AS escalacao_pct,
  round(avg(v.tickets_media_resolucao_h), 1) AS resolucao_media_h,
  round(avg(v.uso_soma_usage_count), 0) AS usos_por_conta,
  round(100.0 * sum(v.uso_soma_erros) / nullif(sum(v.uso_soma_usage_count), 0), 2) AS erro_pct,
  round(avg(v.churn_eventos), 2) AS eventos_churn_por_conta
FROM vw_conta v
WHERE ${whereConta(f, "v")}
GROUP BY grupo ORDER BY grupo`;
  const r = runQuery(sql);
  const g = (nome: string) => r.rows.find((x) => x.grupo === nome);
  const rec = g("recorte");
  const rest = g("resto");
  const val = (row: Record<string, unknown> | undefined, k: string) => (row && row[k] !== null && row[k] !== undefined ? Number(row[k]) : null);
  const linhas: NonNullable<ResultadoRecorte["perfil"]>["linhas"] = [
    { metrica: "Contas", k: "contas", formato: "int" as const },
    { metrica: "MRR ativo médio por conta", k: "mrr_ativo_medio_usd", formato: "usd" as const },
    { metrica: "Assentos médios por conta", k: "assentos_medios", formato: "dec" as const },
    { metrica: "Tickets por conta", k: "tickets_por_conta", formato: "dec" as const },
    { metrica: "Satisfação média (1–5)", k: "satisfacao_media", formato: "dec" as const },
    { metrica: "Tickets escalados", k: "escalacao_pct", formato: "pct" as const },
    { metrica: "Resolução média (horas)", k: "resolucao_media_h", formato: "dec" as const },
    { metrica: "Usos de recursos por conta", k: "usos_por_conta", formato: "int" as const },
    { metrica: "Taxa de erro no uso", k: "erro_pct", formato: "pct" as const },
    { metrica: "Eventos de churn por conta", k: "eventos_churn_por_conta", formato: "dec" as const },
  ].map(({ metrica, k, formato }) => ({ metrica, recorte: val(rec, k), resto: val(rest, k), formato }));
  return { linhas, sql: r.sql };
}

function cruzamento(def: Def, where: string, [ia, ib]: [string, string]): ResultadoRecorte["cruzamento"] {
  const a = dimensao(def, ia);
  const b = dimensao(def, ib);
  if (a.id === b.id) throw new Error("escolha duas dimensões diferentes");
  const sql = `SELECT ${a.expr} AS linha, ${b.expr} AS coluna, ${def.medida} AS valor
FROM ${def.from}
WHERE ${where}
GROUP BY linha, coluna ORDER BY linha, coluna`;
  const r = runQuery(sql);
  const totalPor = (k: "linha" | "coluna") => {
    const m = new Map<string, number>();
    for (const row of r.rows) m.set(String(row[k]), (m.get(String(row[k])) ?? 0) + num(row.valor));
    return m;
  };
  const ordenar = (d: Dimensao, m: Map<string, number>) => [...m.keys()].sort((x, y) => (d.ordenarPorRotulo ? x.localeCompare(y) : (m.get(y) ?? 0) - (m.get(x) ?? 0))).slice(0, 15);
  const linhas = ordenar(a, totalPor("linha"));
  const colunas = ordenar(b, totalPor("coluna"));
  const celulas = linhas.map((l) => colunas.map((c) => num(r.rows.find((row) => String(row.linha) === l && String(row.coluna) === c)?.valor)));
  return { linhas: linhas.map((l) => rotular(a, l)), colunas: colunas.map((c) => rotular(b, c)), celulas, sql: r.sql, titulo: `${a.titulo} × ${b.titulo}` };
}
