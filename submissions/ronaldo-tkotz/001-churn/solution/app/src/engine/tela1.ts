/**
 * Screen 1 — "Algo não bate? As três afirmações" (design blocks B1.0–B1.3).
 * Every number comes from a query on the RavenStack database; each block returns its SQL.
 *
 * Definitions: churn = churn_events (D20); accounts with an event as headline, events as
 * volume, active month = a subscription in force (D21); each number on its own identifier
 * (D23); plan filter and lost MRR as decided in D27.
 */
import { runQuery } from "./warehouse";
import { type Filtros, whereConta, whereAssinatura } from "./filtros";

const num = (v: unknown): number => Number(v ?? 0);

/** Months from parametros.data_inicio to data_corte, as in vw_mes. */
export const MESES_CTE = `m(ini) AS (
  SELECT (SELECT valor FROM parametros WHERE nome = 'data_inicio')
  UNION ALL
  SELECT datetime(ini, '+1 month') FROM m
  WHERE datetime(ini, '+1 month') <= (SELECT valor FROM parametros WHERE nome = 'data_corte')
),
mm AS (SELECT ini, datetime(ini, '+1 month', '-1 second') AS fim FROM m)`;

// ── B1.1 · O churn subiu? ────────────────────────────────────────────────────

export interface B11 {
  meses: string[];
  contasAtivas: number[];
  contasComEvento: number[];
  eventos: number[];
  /** % of active accounts with an event in the month (all accounts with an event). */
  taxa: number[];
  /** Same, counting only accounts with a subscription in force that month. */
  taxaNaBase: number[];
  mesesQueDiferem: number;
  contasForaDaBase: number;
  totalEventos: number;
  mrrPerdido: { contas: number; mrr: number; sql: string };
  sql: string;
}

export function b11(f: Filtros): B11 {
  const sql = `WITH RECURSIVE ${MESES_CTE},
ca AS (SELECT a.account_id FROM accounts a WHERE ${whereConta(f)}),
ativa AS (
  SELECT mm.ini, s.account_id FROM mm JOIN subscriptions s
    ON s.start_date <= mm.fim AND (s.end_date IS NULL OR s.end_date >= mm.ini)
  WHERE s.account_id IN (SELECT account_id FROM ca)
  GROUP BY mm.ini, s.account_id
),
ev AS (
  SELECT mm.ini, c.account_id, count(*) AS n FROM mm JOIN churn_events c
    ON c.churn_date BETWEEN mm.ini AND mm.fim
  WHERE c.account_id IN (SELECT account_id FROM ca)
  GROUP BY mm.ini, c.account_id
)
SELECT
  substr(mm.ini, 1, 7) AS mes,
  (SELECT count(*) FROM ativa a WHERE a.ini = mm.ini) AS contas_ativas,
  (SELECT count(*) FROM ev WHERE ev.ini = mm.ini) AS churn_contas,
  (SELECT coalesce(sum(n), 0) FROM ev WHERE ev.ini = mm.ini) AS churn_eventos,
  (SELECT count(*) FROM ev WHERE ev.ini = mm.ini
     AND NOT EXISTS (SELECT 1 FROM ativa a WHERE a.ini = ev.ini AND a.account_id = ev.account_id)) AS fora_da_base,
  round(100.0 * (SELECT count(*) FROM ev WHERE ev.ini = mm.ini)
        / nullif((SELECT count(*) FROM ativa a WHERE a.ini = mm.ini), 0), 1) AS taxa_pct,
  round(100.0 * (SELECT count(*) FROM ev WHERE ev.ini = mm.ini
                   AND EXISTS (SELECT 1 FROM ativa a WHERE a.ini = ev.ini AND a.account_id = ev.account_id))
        / nullif((SELECT count(*) FROM ativa a WHERE a.ini = mm.ini), 0), 1) AS taxa_na_base_pct
FROM mm ORDER BY mes`;
  const r = runQuery(sql);
  const col = (k: string) => r.rows.map((row) => num(row[k]));

  const mrrSql = `SELECT count(*) AS contas, coalesce(sum(a.assin_soma_mrr), 0) AS mrr
FROM vw_conta a WHERE a.churn_rotulo = 1 AND ${whereConta(f)}`;
  const m = runQuery(mrrSql).rows[0] ?? {};

  const taxa = col("taxa_pct");
  const taxaNaBase = col("taxa_na_base_pct");
  return {
    meses: r.rows.map((row) => String(row.mes)),
    contasAtivas: col("contas_ativas"),
    contasComEvento: col("churn_contas"),
    eventos: col("churn_eventos"),
    taxa,
    taxaNaBase,
    mesesQueDiferem: taxa.filter((t, i) => t !== taxaNaBase[i]).length,
    contasForaDaBase: col("fora_da_base").reduce((a, b) => a + b, 0),
    totalEventos: col("churn_eventos").reduce((a, b) => a + b, 0),
    mrrPerdido: { contas: num(m.contas), mrr: num(m.mrr), sql: mrrSql },
    sql: r.sql,
  };
}

// ── B1.2 · A satisfação está ok? ─────────────────────────────────────────────

export interface B12 {
  trimestres: string[];
  nota3: number[];
  nota4: number[];
  nota5: number[];
  semNota: number[];
  /** Totals with every ticket and without the T08 tickets (opened before signup). */
  comAlerta: { tickets: number; semNota: number };
  semAlerta: { tickets: number; semNota: number };
  ticketsT08: number;
  sql: string;
  totaisSql: string;
}

/** Tickets are account-level (D23): filtered by the account's attributes and plan. */
export function b12(f: Filtros): B12 {
  const base = `support_tickets t JOIN accounts a ON a.account_id = t.account_id WHERE ${whereConta(f)}`;
  const t08 = `t.submitted_at < a.signup_date`;
  const where = f.alerta === "sem" ? `${base} AND NOT (${t08})` : base;
  const sql = `SELECT substr(t.submitted_at, 1, 4) || '-T' || ((CAST(substr(t.submitted_at, 6, 2) AS INTEGER) + 2) / 3) AS trimestre,
  sum(t.satisfaction_score = 3) AS nota_3,
  sum(t.satisfaction_score = 4) AS nota_4,
  sum(t.satisfaction_score = 5) AS nota_5,
  sum(t.satisfaction_score IS NULL) AS sem_nota
FROM ${where}
GROUP BY trimestre ORDER BY trimestre`;
  const r = runQuery(sql);
  const col = (k: string) => r.rows.map((row) => num(row[k]));

  const totaisSql = `SELECT count(*) AS tickets, sum(t.satisfaction_score IS NULL) AS sem_nota,
  sum(${t08}) AS t08,
  sum(NOT (${t08})) AS tickets_sem_t08,
  sum(t.satisfaction_score IS NULL AND NOT (${t08})) AS sem_nota_sem_t08
FROM ${base}`;
  const t = runQuery(totaisSql).rows[0] ?? {};

  return {
    trimestres: r.rows.map((row) => String(row.trimestre)),
    nota3: col("nota_3"),
    nota4: col("nota_4"),
    nota5: col("nota_5"),
    semNota: col("sem_nota"),
    comAlerta: { tickets: num(t.tickets), semNota: num(t.sem_nota) },
    semAlerta: { tickets: num(t.tickets_sem_t08), semNota: num(t.sem_nota_sem_t08) },
    ticketsT08: num(t.t08),
    sql: r.sql,
    totaisSql,
  };
}

// ── B1.3 · O uso cresceu? Para todos? ────────────────────────────────────────

export interface B13 {
  meses: string[];
  /** Usage records per month, with every record and without the alert records (T06, E13). */
  comAlerta: number[];
  semAlerta: number[];
  totalCom: number;
  totalSem: number;
  registrosT06: number;
  registrosE13: number;
  /** Small multiples by sector, in the selected alert mode. */
  porSetor: { setor: string; valores: number[] }[];
  sql: string;
  setorSql: string;
}

/** Usage is subscription-level (D23): filtered by the subscription's plan. */
export function b13(f: Filtros): B13 {
  const t06 = `(u.usage_date < s.start_date OR (s.end_date IS NOT NULL AND u.usage_date > s.end_date))`;
  const e13 = `u.usage_id IN (SELECT usage_id FROM feature_usage GROUP BY usage_id HAVING count(*) > 1)`;
  const alerta = `(${t06} OR ${e13})`;
  const from = `feature_usage u JOIN subscriptions s ON s.subscription_id = u.subscription_id WHERE ${whereAssinatura(f)}`;

  const sql = `SELECT substr(u.usage_date, 1, 7) AS mes,
  count(*) AS registros,
  sum(NOT ${alerta}) AS registros_sem_alerta,
  sum(${t06}) AS t06,
  sum(${e13}) AS e13
FROM ${from}
GROUP BY mes ORDER BY mes`;
  const r = runQuery(sql);
  const col = (k: string) => r.rows.map((row) => num(row[k]));
  const meses = r.rows.map((row) => String(row.mes));
  const sum = (xs: number[]) => xs.reduce((a, b) => a + b, 0);

  const setorSql = `SELECT a.industry AS setor, substr(u.usage_date, 1, 7) AS mes, count(*) AS registros
FROM feature_usage u JOIN subscriptions s ON s.subscription_id = u.subscription_id
JOIN accounts a ON a.account_id = s.account_id
WHERE ${whereAssinatura(f)}${f.alerta === "sem" ? ` AND NOT ${alerta}` : ""}
GROUP BY setor, mes ORDER BY setor, mes`;
  const sr = runQuery(setorSql);
  const setores = [...new Set(sr.rows.map((row) => String(row.setor)))];
  const porSetor = setores.map((setor) => {
    const byMes = new Map(sr.rows.filter((row) => row.setor === setor).map((row) => [String(row.mes), num(row.registros)]));
    return { setor, valores: meses.map((m) => byMes.get(m) ?? 0) };
  });

  return {
    meses,
    comAlerta: col("registros"),
    semAlerta: col("registros_sem_alerta"),
    totalCom: sum(col("registros")),
    totalSem: sum(col("registros_sem_alerta")),
    registrosT06: sum(col("t06")),
    registrosE13: sum(col("e13")),
    porSetor,
    sql: r.sql,
    setorSql,
  };
}
