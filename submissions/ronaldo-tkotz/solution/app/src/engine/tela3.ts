/**
 * Screen 3 — support and product usage (D34, built in D43). Every number comes from a query on the
 * RavenStack database; each block returns its SQL.
 *
 * Tickets belong to an account, so they follow the account filters (whereConta). Usage records
 * belong to a subscription, so they follow the subscription filters (whereAssinatura, D27).
 * With "sem registros em alerta", T08 tickets (opened before signup) and T06/E13 usage records
 * (outside the subscription, repeated usage_id) leave every block.
 */
import { runQuery } from "./warehouse";
import { type Filtros, whereConta, whereAssinatura } from "./filtros";

const num = (v: unknown): number => Number(v ?? 0);
const opt = (v: unknown): number | null => (v === null || v === undefined ? null : Number(v));

const T06 = `(u.usage_date < s.start_date OR (s.end_date IS NOT NULL AND u.usage_date > s.end_date))`;
const E13 = `u.usage_id IN (SELECT usage_id FROM feature_usage GROUP BY usage_id HAVING count(*) > 1)`;
export const semAlertaUso = (f: Filtros) => (f.alerta === "sem" ? ` AND NOT (${T06} OR ${E13})` : "");
export const semAlertaTicket = (f: Filtros) => (f.alerta === "sem" ? ` AND NOT (t.submitted_at < a.signup_date)` : "");

/** The filtered tickets, as a CTE named `tk`. */
const ticketsCte = (f: Filtros) => `tk AS (
  SELECT t.* FROM support_tickets t JOIN accounts a ON a.account_id = t.account_id
  WHERE ${whereConta(f)}${semAlertaTicket(f)}
)`;

/** The filtered usage records, as a CTE named `us`. */
const usoCte = (f: Filtros) => `us AS (
  SELECT u.* FROM feature_usage u JOIN subscriptions s ON s.subscription_id = u.subscription_id
  WHERE ${whereAssinatura(f)}${semAlertaUso(f)}
)`;

export interface Serie {
  dados: { label: string; value: number }[];
  sql: string;
}

function serie(sql: string): Serie {
  const r = runQuery(sql);
  return { dados: r.rows.map((row) => ({ label: String(row.label), value: num(row.valor) })), sql: r.sql };
}

// ── Headline numbers ─────────────────────────────────────────────────────────

export interface Indicadores3 {
  tickets: number;
  contasComTicket: number;
  escalados: number;
  satisfacao: number | null;
  semNotaPct: number;
  resolucaoH: number | null;
  respostaMin: number | null;
  usos: number;
  horasUso: number;
  erros: number;
  taxaErroPct: number;
  sql: string[];
}

export function indicadores3(f: Filtros): Indicadores3 {
  const tSql = `WITH ${ticketsCte(f)}
SELECT count(*) AS tickets, count(DISTINCT account_id) AS contas, coalesce(sum(escalation_flag), 0) AS escalados,
  round(avg(satisfaction_score), 2) AS satisfacao,
  round(100.0 * sum(satisfaction_score IS NULL) / nullif(count(*), 0), 1) AS sem_nota_pct,
  round(avg(resolution_time_hours), 1) AS resolucao_h,
  round(avg(first_response_time_minutes), 0) AS resposta_min
FROM tk`;
  const uSql = `WITH ${usoCte(f)}
SELECT coalesce(sum(usage_count), 0) AS usos, round(coalesce(sum(usage_duration_secs), 0) / 3600.0) AS horas,
  coalesce(sum(error_count), 0) AS erros,
  round(100.0 * sum(error_count) / nullif(sum(usage_count), 0), 2) AS taxa_erro_pct
FROM us`;
  const t = runQuery(tSql);
  const u = runQuery(uSql);
  const tr = t.rows[0] ?? {};
  const ur = u.rows[0] ?? {};
  return {
    tickets: num(tr.tickets),
    contasComTicket: num(tr.contas),
    escalados: num(tr.escalados),
    satisfacao: opt(tr.satisfacao),
    semNotaPct: num(tr.sem_nota_pct),
    resolucaoH: opt(tr.resolucao_h),
    respostaMin: opt(tr.resposta_min),
    usos: num(ur.usos),
    horasUso: num(ur.horas),
    erros: num(ur.erros),
    taxaErroPct: num(ur.taxa_erro_pct),
    sql: [t.sql, u.sql],
  };
}

// ── Usage by plan and escalation by priority (D49) ───────────────────────

export interface PorPlano {
  planos: { label: string; usos: number; erros: number; taxaErro: number }[];
  sql: string;
}

/**
 * Usage volume and error rate (errors ÷ uses) per plan. A usage record belongs to a subscription, so
 * the plan is the subscription's plan (D27), Basic → Pro → Enterprise.
 */
export function usoPorPlano(f: Filtros): PorPlano {
  const r = runQuery(`WITH ${usoCte(f)}
SELECT s.plan_tier AS plano, coalesce(sum(us.usage_count), 0) AS usos, coalesce(sum(us.error_count), 0) AS erros,
  round(100.0 * sum(us.error_count) / nullif(sum(us.usage_count), 0), 2) AS taxa_erro_pct
FROM us JOIN subscriptions s ON s.subscription_id = us.subscription_id
GROUP BY s.plan_tier
ORDER BY CASE s.plan_tier WHEN 'Basic' THEN 1 WHEN 'Pro' THEN 2 ELSE 3 END`);
  return {
    planos: r.rows.map((row) => ({ label: String(row.plano), usos: num(row.usos), erros: num(row.erros), taxaErro: num(row.taxa_erro_pct) })),
    sql: r.sql,
  };
}

export interface Escalacao {
  prioridades: { label: string; chave: string; tickets: number; escalados: number; taxa: number }[];
  sql: string;
}

/** Share of the tickets escalated, per priority (low → urgent), with the escalated count. */
export function escalacaoPorPrioridade(f: Filtros): Escalacao {
  const r = runQuery(`WITH ${ticketsCte(f)}
SELECT priority AS chave,
  CASE priority WHEN 'low' THEN 'Baixa' WHEN 'medium' THEN 'Média' WHEN 'high' THEN 'Alta' ELSE 'Urgente' END AS label,
  count(*) AS tickets, coalesce(sum(escalation_flag), 0) AS escalados,
  round(100.0 * sum(escalation_flag) / nullif(count(*), 0), 1) AS taxa_pct
FROM tk GROUP BY priority
ORDER BY CASE priority WHEN 'low' THEN 1 WHEN 'medium' THEN 2 WHEN 'high' THEN 3 ELSE 4 END`);
  return {
    prioridades: r.rows.map((row) => ({
      label: String(row.label),
      chave: String(row.chave),
      tickets: num(row.tickets),
      escalados: num(row.escalados),
      taxa: num(row.taxa_pct),
    })),
    sql: r.sql,
  };
}

export interface ChurnSuporte {
  grupos: { label: string; contas: number; comChurn: number; taxa: number }[];
  sql: string;
}

/**
 * Churn by contact with support (D50): the accounts split into "had an escalated ticket", "only
 * non-escalated tickets" and "never opened a ticket"; for each, the % with a churn event (D20).
 */
export function churnPorSuporte(f: Filtros): ChurnSuporte {
  const r = runQuery(`WITH ${ticketsCte(f)},
ct AS (
  SELECT a.account_id,
    EXISTS (SELECT 1 FROM churn_events e WHERE e.account_id = a.account_id) AS churn,
    CASE WHEN EXISTS (SELECT 1 FROM tk WHERE tk.account_id = a.account_id AND tk.escalation_flag = 1) THEN 1
      WHEN EXISTS (SELECT 1 FROM tk WHERE tk.account_id = a.account_id) THEN 2 ELSE 3 END AS grupo
  FROM accounts a WHERE ${whereConta(f)}
)
SELECT grupo,
  CASE grupo WHEN 1 THEN 'Com escalação' WHEN 2 THEN 'Sem escalação' ELSE 'Sem ticket' END AS label,
  count(*) AS contas, sum(churn) AS com_churn, round(100.0 * sum(churn) / count(*), 1) AS taxa_pct
FROM ct GROUP BY grupo ORDER BY grupo`);
  return {
    grupos: r.rows.map((row) => ({ label: String(row.label), contas: num(row.contas), comChurn: num(row.com_churn), taxa: num(row.taxa_pct) })),
    sql: r.sql,
  };
}

// ── How the tickets split ────────────────────────────────────────────────────

/** Tickets by priority, in priority order. */
export const ticketsPorPrioridade = (f: Filtros): Serie =>
  serie(`WITH ${ticketsCte(f)}
SELECT CASE priority WHEN 'low' THEN 'Baixa' WHEN 'medium' THEN 'Média' WHEN 'high' THEN 'Alta' ELSE 'Urgente' END AS label,
  count(*) AS valor
FROM tk GROUP BY priority
ORDER BY CASE priority WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END`);

/** Tickets by satisfaction score, with the unrated ones as their own slice. */
export const notasSatisfacao = (f: Filtros): Serie =>
  serie(`WITH ${ticketsCte(f)}
SELECT coalesce('Nota ' || satisfaction_score, 'Sem nota') AS label, count(*) AS valor
FROM tk GROUP BY satisfaction_score ORDER BY satisfaction_score IS NULL, satisfaction_score DESC`);

/** Tickets by time to resolve, in hour bands. */
export const faixasResolucao = (f: Filtros): Serie =>
  serie(`WITH ${ticketsCte(f)}
SELECT CASE WHEN resolution_time_hours IS NULL THEN 'Sem registro' WHEN resolution_time_hours <= 12 THEN 'Até 12 h'
  WHEN resolution_time_hours <= 24 THEN '12 a 24 h' WHEN resolution_time_hours <= 48 THEN '24 a 48 h' ELSE 'Mais de 48 h' END AS label,
  count(*) AS valor
FROM tk GROUP BY label
ORDER BY min(CASE WHEN resolution_time_hours IS NULL THEN 9 WHEN resolution_time_hours <= 12 THEN 1
  WHEN resolution_time_hours <= 24 THEN 2 WHEN resolution_time_hours <= 48 THEN 3 ELSE 4 END)`);

/** Tickets by time to first response, in bands. */
export const faixasResposta = (f: Filtros): Serie =>
  serie(`WITH ${ticketsCte(f)}
SELECT CASE WHEN first_response_time_minutes IS NULL THEN 'Sem registro' WHEN first_response_time_minutes <= 30 THEN 'Até 30 min'
  WHEN first_response_time_minutes <= 60 THEN '30 a 60 min' WHEN first_response_time_minutes <= 120 THEN '1 a 2 h' ELSE 'Mais de 2 h' END AS label,
  count(*) AS valor
FROM tk GROUP BY label
ORDER BY min(CASE WHEN first_response_time_minutes IS NULL THEN 9 WHEN first_response_time_minutes <= 30 THEN 1
  WHEN first_response_time_minutes <= 60 THEN 2 WHEN first_response_time_minutes <= 120 THEN 3 ELSE 4 END)`);

// ── Features ─────────────────────────────────────────────────────────────────

/** The ten most used features, by uses in the period, each with its error rate (errors ÷ uses, D49). */
export function recursosMaisUsados(f: Filtros): Serie & { taxaErro: number[] } {
  const r = runQuery(`WITH ${usoCte(f)}
SELECT feature_name AS label, sum(usage_count) AS valor,
  round(100.0 * sum(error_count) / nullif(sum(usage_count), 0), 2) AS taxa_erro_pct
FROM us GROUP BY feature_name ORDER BY valor DESC LIMIT 10`);
  return {
    // "feature_12" reads "Recurso 12" (renamed here: the read-only guard refuses the word REPLACE in SQL).
    dados: r.rows.map((row) => ({ label: String(row.label).replace(/^feature_/, "Recurso "), value: num(row.valor) })),
    taxaErro: r.rows.map((row) => num(row.taxa_erro_pct)),
    sql: r.sql,
  };
}

export interface Recurso {
  recurso: string;
  usos: number;
  taxaErro: number;
  beta: boolean;
}

/**
 * One point per feature and phase: total uses × error rate (errors / uses). `is_beta_feature` marks
 * the usage record, not the feature (all 40 features have beta records), so each feature gives a
 * stable point and a beta point.
 */
export function recursosErros(f: Filtros): { recursos: Recurso[]; sql: string } {
  const sql = `WITH ${usoCte(f)}
SELECT feature_name AS recurso, is_beta_feature AS beta, sum(usage_count) AS usos,
  round(100.0 * sum(error_count) / nullif(sum(usage_count), 0), 2) AS taxa_erro_pct
FROM us GROUP BY feature_name, is_beta_feature ORDER BY taxa_erro_pct DESC`;
  const r = runQuery(sql);
  return {
    recursos: r.rows.map((row) => ({ recurso: String(row.recurso), usos: num(row.usos), taxaErro: num(row.taxa_erro_pct), beta: num(row.beta) === 1 })),
    sql: r.sql,
  };
}
