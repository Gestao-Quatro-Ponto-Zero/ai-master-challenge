/**
 * Monthly churn (B1.1) and the month calendar, used by the overview. Screen 1 (the three
 * claims) left the app in D49: those answers now come from a deck built from marked charts.
 * Every number comes from a query on the RavenStack database and returns its SQL.
 *
 * Definitions: churn = churn_events (D20); accounts with an event as headline, events as
 * volume, active month = a subscription in force (D21); each number on its own identifier
 * (D23); plan filter and lost MRR as decided in D27.
 */
import { runQuery } from "./warehouse";
import { type Filtros, whereConta } from "./filtros";

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
