-- Views da camada analítica. Regra de construção: cada view só junta "para cima" (filho -> pai, N:1)
-- ou agrega a tabela filha no grão do pai ANTES de juntar. Assim nenhuma linha se multiplica.
-- No fim, checagens V* (bloqueantes) comparam os totais de cada view com as tabelas de origem.
-- Nomes: atributos da conta com prefixo conta_, da assinatura com prefixo assin_.

DROP VIEW IF EXISTS vw_uso_detalhe;
DROP VIEW IF EXISTS vw_ticket_detalhe;
DROP VIEW IF EXISTS vw_churn_detalhe;
DROP VIEW IF EXISTS vw_assinatura;
DROP VIEW IF EXISTS vw_conta;
DROP VIEW IF EXISTS vw_dq_ocorrencias;

-- ================= 1. Detalhe enriquecido (uma linha por evento) =================
CREATE VIEW vw_uso_detalhe AS
SELECT u.usage_pk, u.usage_id, u.subscription_id, s.account_id,
       u.usage_date, u.feature_name, u.usage_count, u.usage_duration_secs, u.error_count, u.is_beta_feature,
       s.plan_tier AS assin_plan_tier, s.billing_frequency AS assin_billing_frequency,
       s.start_date AS assin_start_date, s.end_date AS assin_end_date, s.is_trial AS assin_is_trial,
       s.mrr_amount AS assin_mrr_amount,
       a.industry AS conta_industry, a.country AS conta_country, a.plan_tier AS conta_plan_tier,
       a.referral_source AS conta_referral_source, a.signup_date AS conta_signup_date, a.churn_flag AS conta_churn_flag
FROM feature_usage u
JOIN subscriptions s ON s.subscription_id = u.subscription_id
JOIN accounts a      ON a.account_id = s.account_id;

CREATE VIEW vw_ticket_detalhe AS
SELECT t.*,
       a.industry AS conta_industry, a.country AS conta_country, a.plan_tier AS conta_plan_tier,
       a.referral_source AS conta_referral_source, a.signup_date AS conta_signup_date, a.churn_flag AS conta_churn_flag
FROM support_tickets t
JOIN accounts a ON a.account_id = t.account_id;

CREATE VIEW vw_churn_detalhe AS
SELECT e.*,
       a.industry AS conta_industry, a.country AS conta_country, a.plan_tier AS conta_plan_tier,
       a.referral_source AS conta_referral_source, a.signup_date AS conta_signup_date, a.churn_flag AS conta_churn_flag
FROM churn_events e
JOIN accounts a ON a.account_id = e.account_id;

-- ================= 2. Uma linha por assinatura =================
-- Tickets e eventos de churn não entram: eles só se ligam à conta.
CREATE VIEW vw_assinatura AS
WITH uso AS (
  SELECT subscription_id,
         count(*)                     AS uso_registros,
         sum(usage_count)             AS uso_soma_usage_count,
         sum(usage_duration_secs)     AS uso_soma_duracao_secs,
         sum(error_count)             AS uso_soma_erros,
         sum(is_beta_feature)         AS uso_registros_beta,
         count(DISTINCT feature_name) AS uso_recursos_distintos,
         min(usage_date)              AS uso_primeira_data,
         max(usage_date)              AS uso_ultima_data
  FROM feature_usage GROUP BY subscription_id)
SELECT s.*,
       a.industry AS conta_industry, a.country AS conta_country, a.plan_tier AS conta_plan_tier,
       a.referral_source AS conta_referral_source, a.signup_date AS conta_signup_date, a.churn_flag AS conta_churn_flag,
       coalesce(uso.uso_registros, 0)          AS uso_registros,
       coalesce(uso.uso_soma_usage_count, 0)   AS uso_soma_usage_count,
       coalesce(uso.uso_soma_duracao_secs, 0)  AS uso_soma_duracao_secs,
       coalesce(uso.uso_soma_erros, 0)         AS uso_soma_erros,
       coalesce(uso.uso_registros_beta, 0)     AS uso_registros_beta,
       coalesce(uso.uso_recursos_distintos, 0) AS uso_recursos_distintos,
       uso.uso_primeira_data, uso.uso_ultima_data,
       -- Features da assinatura (D23/D24): só números da própria assinatura.
       round(1.0 * s.mrr_amount / nullif(s.seats, 0), 4)                    AS assin_mrr_por_seat,
       round(1.0 * s.arr_amount / nullif(s.seats, 0), 4)                    AS assin_arr_por_seat,
       round(1.0 * uso.uso_soma_erros / nullif(uso.uso_soma_usage_count, 0), 6) AS uso_taxa_erro,
       -- Atributo da conta, só para filtro (rótulo de churn da conta = tem evento em churn_events, D20).
       EXISTS (SELECT 1 FROM churn_events c WHERE c.account_id = s.account_id) AS conta_churn_rotulo
FROM subscriptions s
JOIN accounts a  ON a.account_id = s.account_id
LEFT JOIN uso    ON uso.subscription_id = s.subscription_id;

-- ================= 3. Uma linha por conta =================
CREATE VIEW vw_conta AS
WITH assin AS (
  SELECT account_id,
         count(*)                 AS assin_total,
         count(end_date)          AS assin_com_end_date,
         sum(end_date IS NULL)    AS assin_sem_end_date,
         sum(mrr_amount)          AS assin_soma_mrr,
         sum(arr_amount)          AS assin_soma_arr,
         sum(CASE WHEN end_date IS NULL THEN mrr_amount ELSE 0 END) AS assin_soma_mrr_sem_end_date,
         sum(CASE WHEN end_date IS NULL THEN arr_amount ELSE 0 END) AS assin_soma_arr_sem_end_date,
         sum(seats)               AS assin_soma_seats,
         sum(CASE WHEN end_date IS NULL THEN seats ELSE 0 END) AS assin_soma_seats_sem_end_date,
         sum(is_trial)            AS assin_trial,
         sum(upgrade_flag)        AS assin_upgrade_flag,
         sum(downgrade_flag)      AS assin_downgrade_flag,
         sum(churn_flag)          AS assin_churn_flag,
         min(start_date)          AS assin_primeiro_start,
         max(start_date)          AS assin_ultimo_start,
         max(end_date)            AS assin_ultimo_end
  FROM subscriptions GROUP BY account_id),
uso AS (
  SELECT s.account_id,
         count(*)                   AS uso_registros,
         sum(u.usage_count)         AS uso_soma_usage_count,
         sum(u.usage_duration_secs) AS uso_soma_duracao_secs,
         sum(u.error_count)         AS uso_soma_erros,
         sum(u.is_beta_feature)     AS uso_registros_beta,
         count(DISTINCT u.feature_name) AS uso_recursos_distintos
  FROM feature_usage u JOIN subscriptions s ON s.subscription_id = u.subscription_id
  GROUP BY s.account_id),
tk AS (
  SELECT account_id,
         count(*)                   AS tickets_total,
         sum(escalation_flag)       AS tickets_escalados,
         count(satisfaction_score)  AS tickets_com_satisfacao,
         sum(satisfaction_score)    AS tickets_soma_satisfacao,
         avg(resolution_time_hours) AS tickets_media_resolucao_h,
         avg(first_response_time_minutes) AS tickets_media_1a_resposta_min
  FROM support_tickets GROUP BY account_id),
ch AS (
  SELECT account_id,
         count(*)               AS churn_eventos,
         sum(is_reactivation)   AS churn_reativacoes,
         sum(refund_amount_usd) AS churn_soma_refund_usd,
         min(churn_date)        AS churn_primeira_data,
         max(churn_date)        AS churn_ultima_data
  FROM churn_events GROUP BY account_id)
SELECT a.*,
       coalesce(assin.assin_total, 0) AS assin_total, coalesce(assin.assin_com_end_date, 0) AS assin_com_end_date,
       coalesce(assin.assin_sem_end_date, 0) AS assin_sem_end_date,
       coalesce(assin.assin_soma_mrr, 0) AS assin_soma_mrr, coalesce(assin.assin_soma_arr, 0) AS assin_soma_arr,
       coalesce(assin.assin_soma_mrr_sem_end_date, 0) AS assin_soma_mrr_sem_end_date,
       coalesce(assin.assin_trial, 0) AS assin_trial, coalesce(assin.assin_upgrade_flag, 0) AS assin_upgrade_flag,
       coalesce(assin.assin_downgrade_flag, 0) AS assin_downgrade_flag, coalesce(assin.assin_churn_flag, 0) AS assin_churn_flag,
       assin.assin_primeiro_start, assin.assin_ultimo_start, assin.assin_ultimo_end,
       coalesce(uso.uso_registros, 0) AS uso_registros, coalesce(uso.uso_soma_usage_count, 0) AS uso_soma_usage_count,
       coalesce(uso.uso_soma_duracao_secs, 0) AS uso_soma_duracao_secs, coalesce(uso.uso_soma_erros, 0) AS uso_soma_erros,
       coalesce(tk.tickets_total, 0) AS tickets_total, coalesce(tk.tickets_escalados, 0) AS tickets_escalados,
       coalesce(tk.tickets_com_satisfacao, 0) AS tickets_com_satisfacao, tk.tickets_soma_satisfacao,
       coalesce(ch.churn_eventos, 0) AS churn_eventos, coalesce(ch.churn_reativacoes, 0) AS churn_reativacoes,
       coalesce(ch.churn_soma_refund_usd, 0) AS churn_soma_refund_usd, ch.churn_primeira_data, ch.churn_ultima_data,
       -- Rótulo de churn da conta (D20) com os outros dois sinais ao lado, só para reconciliar (D22).
       (ch.account_id IS NOT NULL)                   AS churn_rotulo,
       a.churn_flag                                  AS churn_sinal_flag_conta,
       (coalesce(assin.assin_com_end_date, 0) > 0)   AS churn_sinal_fim_assinatura,
       -- Features da conta (D23/D24): totais das assinaturas, uso, tickets e eventos da própria conta.
       coalesce(assin.assin_soma_arr_sem_end_date, 0) AS assin_soma_arr_sem_end_date,
       coalesce(assin.assin_soma_seats, 0)            AS assin_soma_seats,
       coalesce(assin.assin_soma_seats_sem_end_date, 0) AS assin_soma_seats_sem_end_date,
       round(1.0 * assin.assin_soma_mrr / nullif(assin.assin_soma_seats, 0), 4) AS assin_mrr_por_seat,
       round(1.0 * assin.assin_soma_arr / nullif(assin.assin_soma_seats, 0), 4) AS assin_arr_por_seat,
       round(1.0 * assin.assin_soma_mrr_sem_end_date / nullif(assin.assin_soma_seats_sem_end_date, 0), 4) AS assin_mrr_por_seat_sem_end_date,
       coalesce(uso.uso_registros_beta, 0)     AS uso_registros_beta,
       coalesce(uso.uso_recursos_distintos, 0) AS uso_recursos_distintos,
       round(1.0 * uso.uso_soma_erros / nullif(uso.uso_soma_usage_count, 0), 6) AS uso_taxa_erro,
       round(1.0 * tk.tickets_escalados / nullif(tk.tickets_total, 0), 4)        AS tickets_taxa_escalacao,
       round(1.0 * tk.tickets_soma_satisfacao / nullif(tk.tickets_com_satisfacao, 0), 4) AS tickets_media_satisfacao,
       coalesce(tk.tickets_total, 0) - coalesce(tk.tickets_com_satisfacao, 0)   AS tickets_sem_satisfacao,
       round(tk.tickets_media_resolucao_h, 2)      AS tickets_media_resolucao_h,
       round(tk.tickets_media_1a_resposta_min, 2)  AS tickets_media_1a_resposta_min
FROM accounts a
LEFT JOIN assin ON assin.account_id = a.account_id
LEFT JOIN uso   ON uso.account_id   = a.account_id
LEFT JOIN tk    ON tk.account_id    = a.account_id
LEFT JOIN ch    ON ch.account_id    = a.account_id;

-- ================= 4. Qualidade: uma linha por ocorrência de cada checagem =================
-- chave = identificador da linha (ou do grupo) que entrou na contagem de dq_checks.
CREATE VIEW vw_dq_ocorrencias AS
          SELECT 'E13' AS check_id, 'feature_usage' AS tabela, usage_id AS chave FROM feature_usage GROUP BY usage_id HAVING count(*) > 1
UNION ALL SELECT 'R01', 'accounts', a.account_id FROM accounts a WHERE NOT EXISTS (SELECT 1 FROM subscriptions s WHERE s.account_id = a.account_id)
UNION ALL SELECT 'R02', 'accounts', a.account_id FROM accounts a WHERE NOT EXISTS (SELECT 1 FROM support_tickets t WHERE t.account_id = a.account_id)
UNION ALL SELECT 'R03', 'accounts', a.account_id FROM accounts a WHERE NOT EXISTS (SELECT 1 FROM churn_events c WHERE c.account_id = a.account_id)
UNION ALL SELECT 'R04', 'subscriptions', s.subscription_id FROM subscriptions s WHERE NOT EXISTS (SELECT 1 FROM feature_usage u WHERE u.subscription_id = s.subscription_id)
UNION ALL SELECT 'R05', 'accounts', account_id FROM churn_events GROUP BY account_id HAVING count(*) > 1
UNION ALL SELECT 'T01', 'subscriptions', subscription_id FROM subscriptions WHERE end_date < start_date
UNION ALL SELECT 'T02', 'support_tickets', ticket_id FROM support_tickets WHERE closed_at < submitted_at
UNION ALL SELECT 'T03', 'support_tickets', ticket_id FROM raw_support_tickets WHERE length(submitted_at) = 10
UNION ALL SELECT 'T04', 'support_tickets', ticket_id FROM support_tickets
          WHERE closed_at = datetime(submitted_at, '+' || CAST(resolution_time_hours AS INTEGER) || ' hours')
UNION ALL SELECT 'T05', 'support_tickets', ticket_id FROM support_tickets WHERE first_response_time_minutes > resolution_time_hours * 60
UNION ALL SELECT 'T06', 'feature_usage', CAST(u.usage_pk AS TEXT) FROM feature_usage u JOIN subscriptions s ON s.subscription_id = u.subscription_id
          WHERE u.usage_date < s.start_date OR (s.end_date IS NOT NULL AND u.usage_date > s.end_date)
UNION ALL SELECT 'T07', 'subscriptions', s.subscription_id FROM subscriptions s JOIN accounts a ON a.account_id = s.account_id WHERE s.start_date < a.signup_date
UNION ALL SELECT 'T08', 'support_tickets', t.ticket_id FROM support_tickets t JOIN accounts a ON a.account_id = t.account_id WHERE t.submitted_at < a.signup_date
UNION ALL SELECT 'T09', 'churn_events', c.churn_event_id FROM churn_events c JOIN accounts a ON a.account_id = c.account_id WHERE c.churn_date < a.signup_date
UNION ALL SELECT 'N01', 'subscriptions', subscription_id FROM subscriptions WHERE arr_amount <> 12 * mrr_amount
UNION ALL SELECT 'N02', 'subscriptions', subscription_id FROM subscriptions WHERE churn_flag = 1 AND end_date IS NULL
UNION ALL SELECT 'N03', 'subscriptions', subscription_id FROM subscriptions WHERE churn_flag = 0 AND end_date IS NOT NULL
UNION ALL SELECT 'N04', 'accounts', a.account_id FROM accounts a WHERE churn_flag = 1 AND NOT EXISTS (SELECT 1 FROM churn_events c WHERE c.account_id = a.account_id)
UNION ALL SELECT 'N05', 'accounts', a.account_id FROM accounts a WHERE churn_flag = 0 AND EXISTS (SELECT 1 FROM churn_events c WHERE c.account_id = a.account_id)
UNION ALL SELECT 'N06', 'accounts', a.account_id FROM accounts a WHERE churn_flag = 1 AND EXISTS (SELECT 1 FROM subscriptions s WHERE s.account_id = a.account_id AND s.end_date IS NULL)
UNION ALL SELECT 'N07', 'subscriptions', s.subscription_id FROM subscriptions s JOIN accounts a ON a.account_id = s.account_id WHERE s.plan_tier <> a.plan_tier
UNION ALL SELECT 'N08', 'subscriptions', subscription_id FROM subscriptions WHERE is_trial = 1 AND mrr_amount > 0
UNION ALL SELECT 'N09', 'subscriptions', subscription_id FROM subscriptions WHERE mrr_amount = 0;

-- ================= 5. Uma linha por mês (D21) =================
-- Churn = churn_events (D20); todo evento vale, inclusive repetidos da mesma conta.
-- Conta ativa no mês = tem >= 1 assinatura com start_date <= fim do mês e (end_date nula ou >= início do mês).
-- Numerador por conta: contas distintas com evento no mês. Parte delas não tem assinatura vigente no mês
-- (churn_contas_fora_da_base); por isso a view traz as duas taxas (política de alertas, D21).
CREATE VIEW vw_mes AS
WITH RECURSIVE m(ini) AS (
  SELECT (SELECT valor FROM parametros WHERE nome = 'data_inicio')
  UNION ALL
  SELECT datetime(ini, '+1 month') FROM m
  WHERE datetime(ini, '+1 month') <= (SELECT valor FROM parametros WHERE nome = 'data_corte')
),
mm AS (SELECT ini, datetime(ini, '+1 month', '-1 second') AS fim FROM m),
ativa AS (
  SELECT mm.ini, s.account_id FROM mm JOIN subscriptions s
    ON s.start_date <= mm.fim AND (s.end_date IS NULL OR s.end_date >= mm.ini)
  GROUP BY mm.ini, s.account_id
),
ev AS (
  SELECT mm.ini, c.account_id, count(*) AS n FROM mm JOIN churn_events c
    ON c.churn_date BETWEEN mm.ini AND mm.fim
  GROUP BY mm.ini, c.account_id
)
SELECT
  substr(mm.ini, 1, 7)                                                     AS mes,
  mm.ini                                                                   AS mes_inicio,
  mm.fim                                                                   AS mes_fim,
  (SELECT count(*) FROM ativa a WHERE a.ini = mm.ini)                      AS contas_ativas,
  (SELECT coalesce(sum(n), 0) FROM ev WHERE ev.ini = mm.ini)               AS churn_eventos,
  (SELECT count(*) FROM ev WHERE ev.ini = mm.ini)                          AS churn_contas,
  (SELECT count(*) FROM ev WHERE ev.ini = mm.ini
     AND NOT EXISTS (SELECT 1 FROM ativa a WHERE a.ini = ev.ini AND a.account_id = ev.account_id)) AS churn_contas_fora_da_base,
  round(1.0 * (SELECT count(*) FROM ev WHERE ev.ini = mm.ini)
        / nullif((SELECT count(*) FROM ativa a WHERE a.ini = mm.ini), 0), 4) AS taxa_churn_contas,
  round(1.0 * (SELECT count(*) FROM ev WHERE ev.ini = mm.ini
                 AND EXISTS (SELECT 1 FROM ativa a WHERE a.ini = ev.ini AND a.account_id = ev.account_id))
        / nullif((SELECT count(*) FROM ativa a WHERE a.ini = mm.ini), 0), 4) AS taxa_churn_contas_na_base
FROM mm;

-- ================= Reconciliação das views (bloqueante) =================
-- violacoes = número de medidas da view que não batem com a origem (0 = todas batem).
DELETE FROM dq_checks WHERE check_id LIKE 'V%';
INSERT INTO dq_checks (check_id, camada, tabela, regra, severidade, violacoes, base, tratamento)
SELECT 'V01','view','vw_uso_detalhe','linhas, usage_count, duração e erros iguais a feature_usage','bloqueante',
  ((SELECT count(*) FROM vw_uso_detalhe) <> (SELECT count(*) FROM feature_usage))
  + ((SELECT sum(usage_count) FROM vw_uso_detalhe) <> (SELECT sum(usage_count) FROM feature_usage))
  + ((SELECT sum(usage_duration_secs) FROM vw_uso_detalhe) <> (SELECT sum(usage_duration_secs) FROM feature_usage))
  + ((SELECT sum(error_count) FROM vw_uso_detalhe) <> (SELECT sum(error_count) FROM feature_usage)), 4, NULL
UNION ALL SELECT 'V02','view','vw_ticket_detalhe','linhas e tickets distintos iguais a support_tickets','bloqueante',
  ((SELECT count(*) FROM vw_ticket_detalhe) <> (SELECT count(*) FROM support_tickets))
  + ((SELECT count(DISTINCT ticket_id) FROM vw_ticket_detalhe) <> (SELECT count(*) FROM support_tickets)), 2, NULL
UNION ALL SELECT 'V03','view','vw_churn_detalhe','linhas e soma de refund iguais a churn_events','bloqueante',
  ((SELECT count(*) FROM vw_churn_detalhe) <> (SELECT count(*) FROM churn_events))
  + ((SELECT sum(refund_amount_usd) FROM vw_churn_detalhe) <> (SELECT sum(refund_amount_usd) FROM churn_events)), 2, NULL
UNION ALL SELECT 'V04','view','vw_assinatura','linhas, MRR, ARR, registros de uso e erros iguais à origem','bloqueante',
  ((SELECT count(*) FROM vw_assinatura) <> (SELECT count(*) FROM subscriptions))
  + ((SELECT sum(mrr_amount) FROM vw_assinatura) <> (SELECT sum(mrr_amount) FROM subscriptions))
  + ((SELECT sum(arr_amount) FROM vw_assinatura) <> (SELECT sum(arr_amount) FROM subscriptions))
  + ((SELECT sum(uso_registros) FROM vw_assinatura) <> (SELECT count(*) FROM feature_usage))
  + ((SELECT sum(uso_soma_erros) FROM vw_assinatura) <> (SELECT sum(error_count) FROM feature_usage)), 5, NULL
UNION ALL SELECT 'V05','view','vw_conta','linhas e 9 totais (assinaturas, MRR, ARR, uso, erros, tickets, escalados, eventos, refund) iguais à origem','bloqueante',
  ((SELECT count(*) FROM vw_conta) <> (SELECT count(*) FROM accounts))
  + ((SELECT sum(assin_total) FROM vw_conta) <> (SELECT count(*) FROM subscriptions))
  + ((SELECT sum(assin_soma_mrr) FROM vw_conta) <> (SELECT sum(mrr_amount) FROM subscriptions))
  + ((SELECT sum(assin_soma_arr) FROM vw_conta) <> (SELECT sum(arr_amount) FROM subscriptions))
  + ((SELECT sum(uso_registros) FROM vw_conta) <> (SELECT count(*) FROM feature_usage))
  + ((SELECT sum(uso_soma_erros) FROM vw_conta) <> (SELECT sum(error_count) FROM feature_usage))
  + ((SELECT sum(tickets_total) FROM vw_conta) <> (SELECT count(*) FROM support_tickets))
  + ((SELECT sum(tickets_escalados) FROM vw_conta) <> (SELECT sum(escalation_flag) FROM support_tickets))
  + ((SELECT sum(churn_eventos) FROM vw_conta) <> (SELECT count(*) FROM churn_events))
  + ((SELECT sum(churn_soma_refund_usd) FROM vw_conta) <> (SELECT sum(refund_amount_usd) FROM churn_events)), 10, NULL
UNION ALL SELECT 'V06','view','vw_dq_ocorrencias','checagens cuja contagem de ocorrências difere de dq_checks.violacoes','bloqueante',
  (SELECT count(*) FROM dq_checks d
    WHERE d.check_id IN ('E13','R01','R02','R03','R04','R05','T01','T02','T03','T04','T05','T06','T07','T08','T09',
                         'N01','N02','N03','N04','N05','N06','N07','N08','N09')
      AND d.violacoes <> (SELECT count(*) FROM vw_dq_ocorrencias o WHERE o.check_id = d.check_id)),
  24, 'cobre as 24 checagens com ocorrência por linha; E10-E12, E14 e E0* são contagens agregadas'
UNION ALL SELECT 'V07','view','vw_mes','24 meses, eventos, pares conta-mês com evento e contas ativas no último mês iguais à origem','bloqueante',
  ((SELECT count(*) FROM vw_mes) <> 24)
  + ((SELECT sum(churn_eventos) FROM vw_mes) <> (SELECT count(*) FROM churn_events
       WHERE churn_date <= (SELECT datetime(valor, '+1 day', '-1 second') FROM parametros WHERE nome = 'data_corte')))
  + ((SELECT sum(churn_contas) FROM vw_mes) <> (SELECT count(*) FROM (SELECT DISTINCT account_id, substr(churn_date, 1, 7) FROM churn_events)))
  + ((SELECT contas_ativas FROM vw_mes ORDER BY mes DESC LIMIT 1) <> (SELECT count(DISTINCT account_id) FROM subscriptions
       WHERE start_date <= '2024-12-31 23:59:59' AND (end_date IS NULL OR end_date >= '2024-12-01 00:00:00'))),
  4, NULL
UNION ALL SELECT 'V08','view','vw_conta + vw_assinatura','features novas (D24): rótulo e sinais de churn, seats, MRR/ARR ativos, beta, recursos, tickets','bloqueante',
  ((SELECT sum(churn_rotulo) FROM vw_conta) <> (SELECT count(DISTINCT account_id) FROM churn_events))
  + ((SELECT sum(churn_sinal_flag_conta) FROM vw_conta) <> (SELECT sum(churn_flag) FROM accounts))
  + ((SELECT sum(churn_sinal_fim_assinatura) FROM vw_conta) <> (SELECT count(DISTINCT account_id) FROM subscriptions WHERE end_date IS NOT NULL))
  + ((SELECT sum(assin_soma_seats) FROM vw_conta) <> (SELECT sum(seats) FROM subscriptions))
  + ((SELECT sum(assin_soma_arr_sem_end_date) FROM vw_conta) <> (SELECT sum(arr_amount) FROM subscriptions WHERE end_date IS NULL))
  + ((SELECT sum(uso_registros_beta) FROM vw_conta) <> (SELECT sum(is_beta_feature) FROM feature_usage))
  + ((SELECT count(*) FROM vw_conta WHERE uso_recursos_distintos > (SELECT count(DISTINCT feature_name) FROM feature_usage)) <> 0)
  + ((SELECT sum(tickets_sem_satisfacao) FROM vw_conta) <> (SELECT count(*) - count(satisfaction_score) FROM support_tickets))
  + ((SELECT sum(conta_churn_rotulo) FROM vw_assinatura) <> (SELECT count(*) FROM subscriptions s WHERE EXISTS (SELECT 1 FROM churn_events c WHERE c.account_id = s.account_id)))
  + ((SELECT count(*) FROM vw_assinatura WHERE abs(assin_mrr_por_seat * seats - mrr_amount) > 0.01 * seats) <> 0),
  10, NULL;
