/**
 * Screen 2 — "O que está causando o churn?" (rebuilt on the user's review, D34).
 * Churn broken down by every attribute the base has, one chart each. Every number comes from a
 * query on the RavenStack database; each block returns its SQL.
 *
 * The column charts (industry, source, country) give "% of accounts with churn_flag = 1"
 * (D36) and live in visaoGeral.ts. The bottom row shows how the churn splits (D37).
 */
import { runQuery } from "./warehouse";
import { type Filtros, whereConta, whereAssinatura } from "./filtros";

const num = (v: unknown): number => Number(v ?? 0);

export interface Serie {
  dados: { label: string; value: number; n?: number }[];
  sql: string;
}

/** Reason codes in plain Portuguese (the codes stay in the SQL). */
export const MOTIVOS: Record<string, string> = {
  features: "Recursos",
  support: "Suporte",
  budget: "Orçamento",
  unknown: "Não informado",
  competitor: "Concorrente",
  pricing: "Preço",
  "(vazio)": "Sem motivo",
};
export const motivoPt = (m: string) => MOTIVOS[m] ?? m;

function serie(sql: string): Serie {
  const r = runQuery(sql);
  return { dados: r.rows.map((row) => ({ label: String(row.label), value: num(row.valor), ...(row.n !== undefined ? { n: num(row.n) } : {}) })), sql: r.sql };
}

/**
 * How the churn splits (D37): each donut shows what share of all churn each group holds.
 * Plan and trial count the accounts with churn_flag = 1 (D36) by the account's own plan and
 * trial flag; billing frequency exists only on the subscription, so it counts the subscriptions
 * with churn_flag = 1 by their billing frequency (human decision).
 */
export const composicaoPlano = (f: Filtros): Serie =>
  serie(`SELECT a.plan_tier AS label, count(*) AS valor
FROM accounts a WHERE a.churn_flag = 1 AND ${whereConta(f)} GROUP BY label ORDER BY valor DESC`);

export const composicaoTrial = (f: Filtros): Serie =>
  serie(`SELECT CASE a.is_trial WHEN 1 THEN 'Trial' ELSE 'Pagas' END AS label, count(*) AS valor
FROM accounts a WHERE a.churn_flag = 1 AND ${whereConta(f)} GROUP BY label ORDER BY valor DESC`);

export const composicaoCobranca = (f: Filtros): Serie =>
  serie(`SELECT CASE s.billing_frequency WHEN 'monthly' THEN 'Mensal' ELSE 'Anual' END AS label, count(*) AS valor
FROM subscriptions s WHERE s.churn_flag = 1 AND ${whereAssinatura(f)} GROUP BY label ORDER BY valor DESC`);
