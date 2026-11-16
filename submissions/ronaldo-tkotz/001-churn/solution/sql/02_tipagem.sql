-- Camada bruta (raw_*) -> camada tipada. Toda transformação está aqui, em SQL legível.
-- Regras:
--   vazio ''              -> NULL
--   'True'/'False'        -> 1/0 (qualquer outro valor vira NULL e o NOT NULL bloqueia a carga)
--   data 'YYYY-MM-DD'     -> 'YYYY-MM-DD 00:00:00'
--   data com hora         -> mantida como está
--   números               -> as tabelas são STRICT: texto não numérico é recusado, não vira 0
-- O script de carga confere, coluna a coluna, que nenhum valor não vazio do CSV virou NULL.

INSERT INTO accounts
SELECT account_id, account_name, industry, country,
       CASE WHEN signup_date = '' THEN NULL WHEN length(signup_date) = 10 THEN signup_date || ' 00:00:00' ELSE signup_date END,
       referral_source, plan_tier, NULLIF(seats, ''),
       CASE is_trial   WHEN 'True' THEN 1 WHEN 'False' THEN 0 END,
       CASE churn_flag WHEN 'True' THEN 1 WHEN 'False' THEN 0 END
FROM raw_accounts ORDER BY _linha;

INSERT INTO subscriptions
SELECT subscription_id, account_id,
       CASE WHEN start_date = '' THEN NULL WHEN length(start_date) = 10 THEN start_date || ' 00:00:00' ELSE start_date END,
       CASE WHEN end_date   = '' THEN NULL WHEN length(end_date)   = 10 THEN end_date   || ' 00:00:00' ELSE end_date   END,
       plan_tier, NULLIF(seats, ''), NULLIF(mrr_amount, ''), NULLIF(arr_amount, ''),
       CASE is_trial        WHEN 'True' THEN 1 WHEN 'False' THEN 0 END,
       CASE upgrade_flag    WHEN 'True' THEN 1 WHEN 'False' THEN 0 END,
       CASE downgrade_flag  WHEN 'True' THEN 1 WHEN 'False' THEN 0 END,
       CASE churn_flag      WHEN 'True' THEN 1 WHEN 'False' THEN 0 END,
       billing_frequency,
       CASE auto_renew_flag WHEN 'True' THEN 1 WHEN 'False' THEN 0 END
FROM raw_subscriptions ORDER BY _linha;

INSERT INTO feature_usage
SELECT _linha, usage_id, subscription_id,
       CASE WHEN usage_date = '' THEN NULL WHEN length(usage_date) = 10 THEN usage_date || ' 00:00:00' ELSE usage_date END,
       feature_name, NULLIF(usage_count, ''), NULLIF(usage_duration_secs, ''), NULLIF(error_count, ''),
       CASE is_beta_feature WHEN 'True' THEN 1 WHEN 'False' THEN 0 END
FROM raw_feature_usage ORDER BY _linha;

-- satisfaction_score vem como '3.0': vira inteiro só se não tiver parte fracionária.
INSERT INTO support_tickets
SELECT ticket_id, account_id,
       CASE WHEN submitted_at = '' THEN NULL WHEN length(submitted_at) = 10 THEN submitted_at || ' 00:00:00' ELSE submitted_at END,
       CASE WHEN closed_at    = '' THEN NULL WHEN length(closed_at)    = 10 THEN closed_at    || ' 00:00:00' ELSE closed_at    END,
       NULLIF(resolution_time_hours, ''), priority, NULLIF(first_response_time_minutes, ''),
       CASE WHEN satisfaction_score = '' THEN NULL
            WHEN CAST(satisfaction_score AS REAL) = CAST(CAST(satisfaction_score AS REAL) AS INTEGER)
            THEN CAST(CAST(satisfaction_score AS REAL) AS INTEGER) END,
       CASE escalation_flag WHEN 'True' THEN 1 WHEN 'False' THEN 0 END
FROM raw_support_tickets ORDER BY _linha;

INSERT INTO churn_events
SELECT churn_event_id, account_id,
       CASE WHEN churn_date = '' THEN NULL WHEN length(churn_date) = 10 THEN churn_date || ' 00:00:00' ELSE churn_date END,
       reason_code, NULLIF(refund_amount_usd, ''),
       CASE preceding_upgrade_flag   WHEN 'True' THEN 1 WHEN 'False' THEN 0 END,
       CASE preceding_downgrade_flag WHEN 'True' THEN 1 WHEN 'False' THEN 0 END,
       CASE is_reactivation          WHEN 'True' THEN 1 WHEN 'False' THEN 0 END,
       NULLIF(feedback_text, '')
FROM raw_churn_events ORDER BY _linha;
