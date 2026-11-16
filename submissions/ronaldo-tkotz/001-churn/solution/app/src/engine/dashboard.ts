/**
 * Dashboard data — every KPI and chart on the overview is computed here from the RavenStack
 * database. Each function returns grounded numbers plus the SQL that produced them.
 *
 * Definitions follow process-log/decisions.md: churn = churn_events (D20); accounts with an
 * event as the headline and events as volume (D21); each number on its own identifier (D23).
 * Status tones stay neutral: these are descriptive numbers, not judgements.
 */
import { runQuery, type WarehouseContext } from "./warehouse";
import { METRICS } from "./metrics";

const num = (v: unknown): number => Number(v ?? 0);

export interface KpiDelta {
  pct: number;
  direction: "up" | "down" | "flat";
  label: string;
}

export interface KpiStatus {
  label: string;
  tone: "good" | "warn" | "bad" | "neutral";
}

export interface Kpi {
  id: string;
  label: string;
  value: number;
  format: "usd" | "int" | "pct" | "raw";
  accent: "neutral" | "critical" | "warning" | "opportunity";
  sub: string;
  sql: string;
  spark: number[];
  sparkSql: string;
  delta?: KpiDelta;
  status: KpiStatus;
}

/** A monthly grounded series → a sparkline. */
function sparkSeries(sql: string, field: string): { spark: number[]; sql: string } {
  const r = runQuery(sql);
  return { spark: r.rows.map((row) => num(row[field])), sql: r.sql };
}

/** Month-over-month change from the tail of a grounded series. */
function deltaOf(series: number[], label = "vs mês anterior"): KpiDelta | undefined {
  if (series.length < 2) return undefined;
  const cur = series[series.length - 1];
  const prev = series[series.length - 2];
  if (!prev) return undefined;
  const pct = Math.round(((cur - prev) / prev) * 1000) / 10;
  const direction = Math.abs(pct) < 0.5 ? "flat" : pct > 0 ? "up" : "down";
  return { pct, direction, label };
}

/** MRR of subscriptions in force in each month (same "in force" rule as vw_mes, D21). */
const MRR_MENSAL_SQL = `WITH m AS (SELECT mes, mes_inicio, mes_fim FROM vw_mes)
SELECT m.mes, sum(s.mrr_amount) AS mrr_vigente
FROM m JOIN subscriptions s ON s.start_date <= m.mes_fim AND (s.end_date IS NULL OR s.end_date >= m.mes_inicio)
GROUP BY m.mes ORDER BY m.mes`;

/** The four headline numbers — descriptive, grounded and inspectable. */
export function kpis(): Kpi[] {
  const base = runQuery(METRICS.base_resumo.sql);
  const b = (base.rows[0] ?? {}) as Record<string, number>;

  const ultimoMes = runQuery(
    `SELECT mes, contas_ativas, churn_contas, churn_eventos, round(100.0 * taxa_churn_contas, 1) AS taxa_pct
     FROM vw_mes ORDER BY mes DESC LIMIT 1`,
  );
  const u = (ultimoMes.rows[0] ?? {}) as Record<string, number | string>;

  const ativasSpark = sparkSeries("SELECT mes, contas_ativas FROM vw_mes ORDER BY mes", "contas_ativas");
  const churnSpark = sparkSeries("SELECT mes, churn_contas FROM vw_mes ORDER BY mes", "churn_contas");
  const mrrSpark = sparkSeries(MRR_MENSAL_SQL, "mrr_vigente");
  const taxaSpark = sparkSeries("SELECT mes, round(100.0 * taxa_churn_contas, 1) AS taxa_pct FROM vw_mes ORDER BY mes", "taxa_pct");

  return [
    {
      id: "contas",
      label: "Contas",
      value: num(b.contas),
      format: "int",
      accent: "neutral",
      sub: `${num(b.assinaturas).toLocaleString("pt-BR")} assinaturas · linha = contas ativas por mês`,
      sql: base.sql,
      spark: ativasSpark.spark,
      sparkSql: ativasSpark.sql,
      delta: deltaOf(ativasSpark.spark, "ativas vs mês anterior"),
      status: { label: "Base", tone: "neutral" },
    },
    {
      id: "contas_com_evento",
      label: "Contas com evento de churn",
      value: num(b.contas_com_evento),
      format: "int",
      accent: "neutral",
      sub: `${num(b.eventos_churn).toLocaleString("pt-BR")} eventos · linha = contas com evento por mês`,
      sql: base.sql,
      spark: churnSpark.spark,
      sparkSql: churnSpark.sql,
      delta: deltaOf(churnSpark.spark, "vs mês anterior"),
      status: { label: "Churn (D20)", tone: "neutral" },
    },
    {
      id: "mrr_sem_fim",
      label: "MRR das assinaturas sem data de fim",
      value: num(b.mrr_sem_fim),
      format: "usd",
      accent: "neutral",
      sub: `${num(b.assinaturas_sem_fim).toLocaleString("pt-BR")} assinaturas · linha = MRR vigente por mês`,
      sql: base.sql,
      spark: mrrSpark.spark,
      sparkSql: mrrSpark.sql,
      delta: deltaOf(mrrSpark.spark, "vs mês anterior"),
      status: { label: "Assinatura", tone: "neutral" },
    },
    {
      id: "taxa_ultimo_mes",
      label: `Taxa de churn em ${String(u.mes ?? "")}`,
      value: num(u.taxa_pct),
      format: "pct",
      accent: "neutral",
      sub: `${num(u.churn_contas)} contas com evento ÷ ${num(u.contas_ativas)} ativas · linha = taxa por mês`,
      sql: ultimoMes.sql,
      spark: taxaSpark.spark,
      sparkSql: taxaSpark.sql,
      delta: deltaOf(taxaSpark.spark, "vs mês anterior"),
      status: { label: "Conta", tone: "neutral" },
    },
  ];
}

export interface TrendResult {
  categories: string[];
  series: { name: string; values: number[]; color?: string }[];
  sql: string;
  lastPartial: boolean;
}

/** Monthly churn from vw_mes: accounts with an event and events (D21). */
export function churnTrend(): TrendResult {
  const r = runQuery("SELECT mes, churn_contas, churn_eventos FROM vw_mes ORDER BY mes");
  return {
    categories: r.rows.map((row) => String(row.mes)),
    series: [
      { name: "Contas com evento", values: r.rows.map((row) => num(row.churn_contas)), color: "#e3b341" },
      { name: "Eventos", values: r.rows.map((row) => num(row.churn_eventos)), color: "#5b9dd6" },
    ],
    sql: r.sql,
    lastPartial: false,
  };
}

export interface SegmentResult {
  data: { label: string; value: number; color?: string; assinaturas: number }[];
  sql: string;
}

/** MRR of subscriptions without an end date, by the subscription's own plan (D23). */
export function mrrByPlan(): SegmentResult {
  const r = runQuery(
    `SELECT plan_tier, count(*) AS assinaturas, sum(mrr_amount) AS mrr
     FROM subscriptions WHERE end_date IS NULL GROUP BY plan_tier ORDER BY mrr DESC`,
  );
  return {
    data: r.rows.map((row) => ({
      label: String(row.plan_tier),
      value: num(row.mrr),
      assinaturas: num(row.assinaturas),
    })),
    sql: r.sql,
  };
}

export interface TableInfo {
  name: string;
  rows: number;
}

/** The live data inventory — tables and views with their row counts (raw_* copies left out). */
export function tableInventory(ctx: WarehouseContext = {}): TableInfo[] {
  const names = runQuery(
    "SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'raw\\_%' ESCAPE '\\' ORDER BY type, name",
    ctx,
  ).rows.map((r) => String(r.name));
  return names.map((name) => ({
    name,
    rows: num((runQuery(`SELECT COUNT(*) AS c FROM "${name}"`, ctx).rows[0] as { c: number }).c),
  }));
}
