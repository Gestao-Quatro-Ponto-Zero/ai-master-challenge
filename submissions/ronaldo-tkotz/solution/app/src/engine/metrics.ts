/**
 * Semantic layer — vetted SQL over the RavenStack views (solution/sql/04_views.sql).
 *
 * Each metric maps to a block of the dashboard design (process-log/dashboard/desenho-dashboard-v1.png)
 * and follows the human decisions in process-log/decisions.md:
 *  - D20: churn = a row in churn_events.
 *  - D21: headline in accounts with an event, volume in events; every event counts in its month;
 *         "active in month" = at least one subscription in force; alerts → show both numbers.
 *  - D23: each number stays on its own identifier (account_id or subscription_id); MRR/ARR reach
 *         the account only as the total of its own subscriptions.
 * These are descriptive queries, not conclusions.
 */

export interface Metric {
  id: string;
  title: string;
  description: string;
  /** Dashboard block(s) this metric feeds. */
  blocks: string[];
  sql: string;
}

export const METRICS: Record<string, Metric> = {
  base_resumo: {
    id: "base_resumo",
    title: "Base: contas, assinaturas, MRR e churn",
    description:
      "Tamanho da base no corte: contas, assinaturas, assinaturas sem data de fim e seu MRR/ARR, contas com evento de churn e eventos.",
    blocks: ["B1.0", "B5.3"],
    sql: `SELECT
  (SELECT count(*) FROM accounts)                                   AS contas,
  (SELECT count(*) FROM subscriptions)                              AS assinaturas,
  (SELECT count(*) FROM subscriptions WHERE end_date IS NULL)       AS assinaturas_sem_fim,
  (SELECT sum(mrr_amount) FROM subscriptions WHERE end_date IS NULL) AS mrr_sem_fim,
  (SELECT sum(arr_amount) FROM subscriptions WHERE end_date IS NULL) AS arr_sem_fim,
  (SELECT count(DISTINCT account_id) FROM churn_events)             AS contas_com_evento,
  (SELECT count(*) FROM churn_events)                               AS eventos_churn`,
  },
  churn_mensal: {
    id: "churn_mensal",
    title: "Churn por mês (contas, eventos e as duas taxas)",
    description:
      "Uma linha por mês: contas ativas, eventos, contas com evento, contas com evento fora da base e as duas taxas (todas e só na base).",
    blocks: ["B1.1"],
    sql: `SELECT mes, contas_ativas, churn_eventos, churn_contas, churn_contas_fora_da_base,
       taxa_churn_contas, taxa_churn_contas_na_base
FROM vw_mes ORDER BY mes`,
  },
  motivos_churn: {
    id: "motivos_churn",
    title: "Motivos declarados de churn",
    description: "Por reason_code: eventos, contas, reativações e refund total (nível de conta, D23).",
    blocks: ["B2.2"],
    sql: `SELECT reason_code,
       count(*)                   AS eventos,
       count(DISTINCT account_id) AS contas,
       sum(is_reactivation)       AS reativacoes,
       round(sum(refund_amount_usd), 2) AS refund_usd
FROM churn_events GROUP BY reason_code ORDER BY eventos DESC`,
  },
  mrr_por_plano: {
    id: "mrr_por_plano",
    title: "MRR e ARR por plano e cobrança (assinaturas)",
    description: "Nível de assinatura (D23): por plano da assinatura e cobrança, total e só assinaturas sem data de fim.",
    blocks: ["B5.4"],
    sql: `SELECT plan_tier, billing_frequency,
       count(*)                                                AS assinaturas,
       sum(end_date IS NULL)                                   AS assinaturas_sem_fim,
       round(sum(mrr_amount), 2)                               AS mrr_total,
       round(sum(CASE WHEN end_date IS NULL THEN mrr_amount ELSE 0 END), 2) AS mrr_sem_fim,
       round(sum(CASE WHEN end_date IS NULL THEN arr_amount ELSE 0 END), 2) AS arr_sem_fim
FROM subscriptions GROUP BY plan_tier, billing_frequency ORDER BY plan_tier, billing_frequency`,
  },
  satisfacao_trimestral: {
    id: "satisfacao_trimestral",
    title: "Satisfação dos tickets por trimestre",
    description: "Tickets por trimestre de abertura com nota 3, 4, 5 e sem nota (825 dos 2.000 não têm nota).",
    blocks: ["B1.2"],
    sql: `SELECT substr(submitted_at, 1, 4) || '-T' || ((CAST(substr(submitted_at, 6, 2) AS INTEGER) + 2) / 3) AS trimestre,
       count(*)                       AS tickets,
       sum(satisfaction_score = 3)    AS nota_3,
       sum(satisfaction_score = 4)    AS nota_4,
       sum(satisfaction_score = 5)    AS nota_5,
       sum(satisfaction_score IS NULL) AS sem_nota
FROM support_tickets GROUP BY trimestre ORDER BY trimestre`,
  },
  uso_mensal: {
    id: "uso_mensal",
    title: "Uso por mês (com e sem registros fora do período da assinatura)",
    description:
      "Registros, usage_count, duração e erros por mês. Mostra quantos registros têm data fora do período da própria assinatura (alerta T06, política D21).",
    blocks: ["B1.3"],
    sql: `SELECT substr(u.usage_date, 1, 7) AS mes,
       count(*)                 AS registros,
       sum(u.usage_count)       AS usage_count,
       sum(u.usage_duration_secs) AS duracao_secs,
       sum(u.error_count)       AS erros,
       sum(u.usage_date < s.start_date OR (s.end_date IS NOT NULL AND u.usage_date > s.end_date)) AS registros_fora_assinatura
FROM feature_usage u JOIN subscriptions s ON s.subscription_id = u.subscription_id
GROUP BY mes ORDER BY mes`,
  },
  contas_por_setor: {
    id: "contas_por_setor",
    title: "Contas por setor: com e sem evento de churn",
    description: "Nível de conta: contas, contas com evento e MRR das assinaturas sem data de fim de cada conta, por setor.",
    blocks: ["B3.1"],
    sql: `SELECT industry,
       count(*)                                  AS contas,
       sum(churn_rotulo)                         AS contas_com_evento,
       round(sum(assin_soma_mrr_sem_end_date), 2) AS mrr_sem_fim,
       round(sum(CASE WHEN churn_rotulo = 1 THEN assin_soma_mrr_sem_end_date ELSE 0 END), 2) AS mrr_sem_fim_contas_com_evento
FROM vw_conta GROUP BY industry ORDER BY contas DESC`,
  },
  alertas_qualidade: {
    id: "alertas_qualidade",
    title: "Alertas de qualidade dos dados",
    description: "Checagens de severidade alerta com ocorrências (dq_checks). Os registros afetados ficam nas análises; os dois números aparecem quando mudam o resultado (D21).",
    blocks: ["B5.1"],
    sql: `SELECT check_id, tabela, regra, violacoes, base
FROM dq_checks WHERE severidade = 'alerta' AND violacoes > 0 ORDER BY check_id`,
  },
};

export function listMetrics(): Metric[] {
  return Object.values(METRICS);
}
