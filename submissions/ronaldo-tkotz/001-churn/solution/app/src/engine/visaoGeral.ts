/**
 * Executive overview (the first screen, D28): headline numbers and high-level breakdowns.
 * Every number comes from a query on the RavenStack database; each returns its SQL.
 *
 * Definitions: churn = churn_events (D20); accounts with an event as the headline (D21);
 * each number on its own identifier (D23): revenue is subscription-level, churn is
 * account-level; plan filter per identifier (D27).
 * - Revenue = MRR of subscriptions without end_date ("MRR ativo").
 * - Churn rate = accounts with an event ÷ active accounts in the last month of the period (vw_mes rule).
 */
import { runQuery } from "./warehouse";
import { type Filtros, whereConta, whereAssinatura } from "./filtros";
import { b11, MESES_CTE } from "./tela1";

const num = (v: unknown): number => Number(v ?? 0);

export interface Indicadores {
  contas: number;
  /** accounts.churn_flag = 1 (the accounts table's own flag; reconciliation only, D20). */
  contasFlag: number;
  assinaturas: number;
  assinaturasAtivas: number;
  /** subscriptions with end_date (= subscriptions.churn_flag = 1 in all 5,000, D22). */
  assinaturasEncerradas: number;
  contasComAssinaturaEncerrada: number;
  contasComChurn: number;
  eventos: number;
  taxaUltimoMes: number;
  ultimoMes: string;
  mediaTaxa2024: number;
  mrrAtivo: number;
  sql: string[];
}

export interface Serie {
  dados: { label: string; value: number; n?: number }[];
  sql: string;
}

export function indicadores(f: Filtros): Indicadores {
  const contasSql = `SELECT count(*) AS contas, sum(a.churn_flag = 1) AS com_flag,
  sum(a.churn_rotulo) AS com_churn, coalesce(sum(a.churn_eventos), 0) AS eventos
FROM vw_conta a WHERE ${whereConta(f)}`;
  const assinSql = `SELECT count(*) AS assinaturas, sum(s.end_date IS NULL) AS ativas,
  sum(s.end_date IS NOT NULL) AS encerradas,
  count(DISTINCT CASE WHEN s.end_date IS NOT NULL THEN s.account_id END) AS contas_com_encerrada,
  coalesce(sum(CASE WHEN s.end_date IS NULL THEN s.mrr_amount END), 0) AS mrr_ativo
FROM subscriptions s
WHERE ${whereAssinatura(f)}`;
  const c = runQuery(contasSql).rows[0] ?? {};
  const s = runQuery(assinSql).rows[0] ?? {};
  const mes = b11(f);
  const last = mes.meses.length - 1;
  const de2024 = mes.taxa.filter((_, i) => mes.meses[i].startsWith("2024"));
  const media = de2024.length ? Math.round((10 * de2024.reduce((a, b) => a + b, 0)) / de2024.length) / 10 : 0;
  return {
    contas: num(c.contas),
    contasFlag: num(c.com_flag),
    assinaturas: num(s.assinaturas),
    assinaturasAtivas: num(s.ativas),
    assinaturasEncerradas: num(s.encerradas),
    contasComAssinaturaEncerrada: num(s.contas_com_encerrada),
    contasComChurn: num(c.com_churn),
    eventos: num(c.eventos),
    taxaUltimoMes: mes.taxa[last] ?? 0,
    ultimoMes: mes.meses[last] ?? "",
    mediaTaxa2024: media,
    mrrAtivo: num(s.mrr_ativo),
    sql: [contasSql, assinSql, mes.sql],
  };
}

function serie(sql: string): Serie {
  const r = runQuery(sql);
  return { dados: r.rows.map((row) => ({ label: String(row.label), value: num(row.valor), ...(row.n !== undefined ? { n: num(row.n) } : {}) })), sql: r.sql };
}

/** Churn events by declared reason (account-level). */
export const motivosChurn = (f: Filtros): Serie =>
  serie(`SELECT coalesce(c.reason_code, '(vazio)') AS label, count(*) AS valor
FROM churn_events c JOIN accounts a ON a.account_id = c.account_id
WHERE ${whereConta(f)} GROUP BY label ORDER BY valor DESC`);

/** MRR ativo by an account attribute (subscription-level number, account attribute). */
const receitaPor = (f: Filtros, coluna: "industry" | "country" | "referral_source"): Serie =>
  serie(`SELECT a.${coluna} AS label, round(sum(s.mrr_amount)) AS valor
FROM subscriptions s JOIN accounts a ON a.account_id = s.account_id
WHERE s.end_date IS NULL AND ${whereAssinatura(f)} GROUP BY label ORDER BY valor DESC`);

export const receitaPorSetor = (f: Filtros) => receitaPor(f, "industry");
export const receitaPorPais = (f: Filtros) => receitaPor(f, "country");

/** MRR ativo by the subscription's own plan (D23). */
export const receitaPorPlano = (f: Filtros): Serie =>
  serie(`SELECT s.plan_tier AS label, round(sum(s.mrr_amount)) AS valor
FROM subscriptions s WHERE s.end_date IS NULL AND ${whereAssinatura(f)} GROUP BY label ORDER BY valor DESC`);

/** % of accounts with churn_flag = 1, by an account attribute (D36: the account churn rate is the flag). */
const churnPor = (f: Filtros, coluna: "industry" | "plan_tier" | "referral_source" | "country"): Serie =>
  serie(`SELECT a.${coluna} AS label, round(100.0 * sum(a.churn_flag) / count(*), 1) AS valor, count(*) AS n
FROM vw_conta a WHERE ${whereConta(f)} GROUP BY label ORDER BY valor DESC`);

export const churnPorSetor = (f: Filtros) => churnPor(f, "industry");
export const churnPorPlano = (f: Filtros) => churnPor(f, "plan_tier");
export const churnPorOrigem = (f: Filtros) => churnPor(f, "referral_source");
export const churnPorPais = (f: Filtros) => churnPor(f, "country");

export interface Crescimento {
  meses: string[];
  /** % change of active accounts (a subscription in force, D21) over the previous month. */
  contas: number[];
  /** % change of accounts with a churn event (D21 headline unit) over the previous month. */
  churn: number[];
  /** Linear trend (least squares, in SQL) of each series, one value per month. */
  tendContas: number[];
  tendChurn: number[];
  /** Months left out at the start: the churn base was under MIN_BASE accounts, so a % is noise. */
  primeiroMes: string;
  sql: string;
}

/** Below this many accounts with an event in the previous month, a month-on-month % is noise. */
export const MIN_BASE = 5;

/**
 * Month-on-month growth (D30): how much the active base grew vs how much churn grew, each
 * against the previous month. Starts at the first month whose previous month had at least
 * MIN_BASE accounts with an event (early 2023 swings from 0 to 5 accounts read as +400%).
 */
export function crescimentoMensal(f: Filtros): Crescimento {
  const base = b11(f).sql;
  const sql = `WITH b AS (${base}),
g AS (
  SELECT mes, contas_ativas, churn_contas,
    lag(contas_ativas) OVER (ORDER BY mes) AS ativas_ant,
    lag(churn_contas) OVER (ORDER BY mes) AS churn_ant
  FROM b
),
inicio AS (SELECT min(mes) AS mes FROM g WHERE churn_ant >= ${MIN_BASE}),
r AS (
  SELECT row_number() OVER (ORDER BY g.mes) AS x, g.mes,
    round(100.0 * (contas_ativas - ativas_ant) / nullif(ativas_ant, 0), 1) AS cresc_contas_pct,
    round(100.0 * (churn_contas - churn_ant) / nullif(churn_ant, 0), 1) AS cresc_churn_pct
  FROM g, inicio WHERE g.mes >= inicio.mes
),
-- Least-squares line per series, y = a + b·x, x = month number (1, 2, 3…).
s AS (
  SELECT
    count(cresc_contas_pct) AS na, sum(CASE WHEN cresc_contas_pct IS NOT NULL THEN x END) AS sxa,
    sum(CASE WHEN cresc_contas_pct IS NOT NULL THEN x * x END) AS sxxa,
    sum(cresc_contas_pct) AS sya, sum(x * cresc_contas_pct) AS sxya,
    count(cresc_churn_pct) AS nc, sum(CASE WHEN cresc_churn_pct IS NOT NULL THEN x END) AS sxc,
    sum(CASE WHEN cresc_churn_pct IS NOT NULL THEN x * x END) AS sxxc,
    sum(cresc_churn_pct) AS syc, sum(x * cresc_churn_pct) AS sxyc
  FROM r
),
coef AS (
  SELECT
    (na * sxya - sxa * sya) / nullif(1.0 * na * sxxa - sxa * sxa, 0) AS ba, sya, sxa, na,
    (nc * sxyc - sxc * syc) / nullif(1.0 * nc * sxxc - sxc * sxc, 0) AS bc, syc, sxc, nc
  FROM s
)
SELECT r.mes, r.cresc_contas_pct, r.cresc_churn_pct,
  round((sya - ba * sxa) / na + ba * r.x, 1) AS tend_contas_pct,
  round((syc - bc * sxc) / nc + bc * r.x, 1) AS tend_churn_pct
FROM r, coef ORDER BY r.mes`;
  const r = runQuery(sql);
  return {
    meses: r.rows.map((row) => String(row.mes)),
    contas: r.rows.map((row) => num(row.cresc_contas_pct)),
    churn: r.rows.map((row) => num(row.cresc_churn_pct)),
    tendContas: r.rows.map((row) => num(row.tend_contas_pct)),
    tendChurn: r.rows.map((row) => num(row.tend_churn_pct)),
    primeiroMes: String(r.rows[0]?.mes ?? ""),
    sql: r.sql,
  };
}

export interface ReceitaNovaVsPerdida {
  /** Last 12 months of data, then the projection. */
  meses: string[];
  /** MRR of the first subscriptions of new accounts, per month (null in projected months). */
  nova: (number | null)[];
  /** MRR of subscriptions that ended in the month (null in projected months). */
  perdida: (number | null)[];
  /** Linear trends of the last 12 months, projected forward (null where the line is below zero). */
  tendNova: (number | null)[];
  tendPerdida: (number | null)[];
  /** Index of the first projected month. */
  inicioProjecao: number;
  /** First month in which the lost-revenue trend reaches the new-revenue trend, if the lines meet. */
  mesCruzamento: string | null;
  /** Months from the last month of data to the crossing. */
  mesesAteCruzamento: number | null;
  sql: string;
}

/**
 * Revenue won from new accounts vs revenue lost to cancellations, per month (D31).
 * - New: MRR of subscriptions an account starts in the month of its first subscription (a new logo).
 * - Lost: MRR of subscriptions whose end_date falls in the month (revenue that actually stopped;
 *   subscription-level, D23).
 * Both trends are least-squares lines over the last 12 months of data, projected until the lost
 * line reaches the new line (at most 36 months ahead). All of it is computed in SQL.
 */
export function receitaNovaVsPerdida(f: Filtros): ReceitaNovaVsPerdida {
  const sql = `WITH RECURSIVE
corte AS (SELECT valor AS d FROM parametros WHERE nome = 'data_corte'),
m(x, ini) AS (
  SELECT 1, datetime(substr((SELECT d FROM corte), 1, 7) || '-01 00:00:00', '-11 months')
  UNION ALL SELECT x + 1, datetime(ini, '+1 month') FROM m WHERE x < 48
),
primeira AS (SELECT account_id, substr(min(start_date), 1, 7) AS mes FROM subscriptions GROUP BY account_id),
nova AS (
  SELECT substr(s.start_date, 1, 7) AS mes, sum(s.mrr_amount) AS mrr
  FROM subscriptions s JOIN primeira pr ON pr.account_id = s.account_id AND pr.mes = substr(s.start_date, 1, 7)
  WHERE ${whereAssinatura(f)} GROUP BY 1
),
perdida AS (
  SELECT substr(s.end_date, 1, 7) AS mes, sum(s.mrr_amount) AS mrr
  FROM subscriptions s WHERE s.end_date IS NOT NULL AND ${whereAssinatura(f)} GROUP BY 1
),
dado AS (
  SELECT m.x, coalesce(nova.mrr, 0) AS nova, coalesce(perdida.mrr, 0) AS perdida
  FROM m LEFT JOIN nova ON nova.mes = substr(m.ini, 1, 7) LEFT JOIN perdida ON perdida.mes = substr(m.ini, 1, 7)
  WHERE m.ini <= (SELECT d FROM corte)
),
-- Least-squares line per series, y = a + b·x, over the months with data.
soma AS (
  SELECT count(*) AS n, sum(x) AS sx, sum(x * x) AS sxx,
    sum(nova) AS syn, sum(x * nova) AS sxyn, sum(perdida) AS syp, sum(x * perdida) AS sxyp
  FROM dado
),
reta AS (
  SELECT n,
    (n * sxyn - sx * syn) / (1.0 * n * sxx - sx * sx) AS bn,
    (syn - sx * (n * sxyn - sx * syn) / (1.0 * n * sxx - sx * sx)) / n AS an,
    (n * sxyp - sx * syp) / (1.0 * n * sxx - sx * sx) AS bp,
    (syp - sx * (n * sxyp - sx * syp) / (1.0 * n * sxx - sx * sx)) / n AS ap
  FROM soma
),
-- Where the lines meet: only when lost revenue grows faster than new revenue.
cruza AS (SELECT CASE WHEN bp > bn THEN (an - ap) / (bp - bn) END AS x FROM reta),
ate AS (SELECT min(48, max(n + 12, coalesce(CAST(ceil(cruza.x) AS INTEGER) + 2, 0))) AS x FROM reta, cruza)
SELECT substr(m.ini, 1, 7) AS mes, m.x, reta.n, dado.nova, dado.perdida,
  CASE WHEN an + bn * m.x >= 0 THEN round(an + bn * m.x) END AS tend_nova,
  CASE WHEN ap + bp * m.x >= 0 THEN round(ap + bp * m.x) END AS tend_perdida,
  CAST(ceil(cruza.x) AS INTEGER) AS x_cruzamento
FROM m CROSS JOIN reta CROSS JOIN cruza CROSS JOIN ate LEFT JOIN dado ON dado.x = m.x
WHERE m.x <= ate.x ORDER BY m.x`;
  const r = runQuery(sql);
  const opt = (v: unknown) => (v === null || v === undefined ? null : Number(v));
  const n = num(r.rows[0]?.n);
  const xc = opt(r.rows[0]?.x_cruzamento);
  const meses = r.rows.map((row) => String(row.mes));
  return {
    meses,
    nova: r.rows.map((row) => opt(row.nova)),
    perdida: r.rows.map((row) => opt(row.perdida)),
    tendNova: r.rows.map((row) => opt(row.tend_nova)),
    tendPerdida: r.rows.map((row) => opt(row.tend_perdida)),
    inicioProjecao: n,
    mesCruzamento: xc !== null && xc >= 1 && xc <= meses.length ? meses[xc - 1] : null,
    mesesAteCruzamento: xc !== null ? xc - n : null,
    sql: r.sql,
  };
}

/** Paid vs trial accounts (accounts.is_trial), D32. */
export const contasPagasTrial = (f: Filtros): Serie =>
  serie(`SELECT CASE WHEN a.is_trial = 1 THEN 'Trial' ELSE 'Pagas' END AS label, count(*) AS valor
FROM accounts a WHERE ${whereConta(f)} GROUP BY label ORDER BY valor DESC`);

export interface IdadeMedia {
  meses: string[];
  /** Average age (months) of the active accounts at month end, counted from signup. */
  contas: number[];
  /** Average age (months) of the subscriptions in force at month end, counted from start. */
  assinaturas: number[];
  sql: string;
}

/** Days in an average month (365.25 / 12), to state ages in months. */
const DIAS_MES = 30.4375;

/**
 * Average age of the base, month by month (D40), jan/2023 to dez/2024. An account is active in a
 * month when it has a subscription in force in it (D21); its age at month end counts from
 * signup_date. The second line does the same for each subscription in force, from start_date.
 * A rising line means the base is ageing (keeping accounts); a falling one means it is renewed
 * by newcomers faster than it keeps the old ones.
 */
export function idadeMedia(f: Filtros): IdadeMedia {
  const sql = `WITH RECURSIVE ${MESES_CTE},
ca AS (SELECT a.account_id, a.signup_date FROM accounts a WHERE ${whereConta(f)}),
ativa AS (
  SELECT mm.ini, mm.fim, ca.account_id, ca.signup_date FROM mm
  JOIN subscriptions s ON s.start_date <= mm.fim AND (s.end_date IS NULL OR s.end_date >= mm.ini)
  JOIN ca ON ca.account_id = s.account_id
  GROUP BY mm.ini, ca.account_id
),
vigor AS (
  SELECT mm.ini, avg(julianday(mm.fim) - julianday(s.start_date)) / ${DIAS_MES} AS idade, count(*) AS n
  FROM mm JOIN subscriptions s ON s.start_date <= mm.fim AND (s.end_date IS NULL OR s.end_date >= mm.ini)
  WHERE ${whereAssinatura(f)}
  GROUP BY mm.ini
)
SELECT substr(mm.ini, 1, 7) AS mes,
  (SELECT count(*) FROM ativa a WHERE a.ini = mm.ini) AS contas_ativas,
  (SELECT round(avg(julianday(a.fim) - julianday(a.signup_date)) / ${DIAS_MES}, 2) FROM ativa a WHERE a.ini = mm.ini) AS idade_contas_meses,
  (SELECT n FROM vigor v WHERE v.ini = mm.ini) AS assinaturas_em_vigor,
  (SELECT round(idade, 2) FROM vigor v WHERE v.ini = mm.ini) AS idade_assinaturas_meses
FROM mm ORDER BY mes`;
  const r = runQuery(sql);
  return {
    meses: r.rows.map((row) => String(row.mes)),
    contas: r.rows.map((row) => num(row.idade_contas_meses)),
    assinaturas: r.rows.map((row) => num(row.idade_assinaturas_meses)),
    sql: r.sql,
  };
}
