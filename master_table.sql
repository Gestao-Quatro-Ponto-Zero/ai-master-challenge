WITH
--nivel da conta/ cadastro do cliente
accounts as (
SELECT DISTINCT
account_id
,account_name
,industry
,country
,signup_date
,referral_source
,plan_tier
,seats
,is_trial
,churn_flag
  FROM
 `lucas-491004.case_g4.ravenstack_accounts`
 )

--quando e pq o cliente saiu
,churn_events as (
SELECT DISTINCT
churn_event_id
,account_id
,churn_date
,reason_code
,refund_amount_usd
,preceding_upgrade_flag
,preceding_downgrade_flag
,is_reactivation
,feedback_text

 FROM `lucas-491004.case_g4.ravenstack_churn_events`
 )

--comportamento dentro do produto
,feature_usage as (
SELECT DISTINCT
usage_id
,subscription_id
,usage_date
,feature_name
,usage_count
,usage_duration_secs
,error_count
,is_beta_feature

 FROM `lucas-491004.case_g4.ravenstack_feature_usage`
 )

--receita com comportamento
,subscriptions as (
SELECT DISTINCT
subscription_id
,account_id
,start_date
,end_date
,plan_tier
,seats
,mrr_amount
,arr_amount
,is_trial
,upgrade_flag
,downgrade_flag
,churn_flag
,billing_frequency
,auto_renew_flag

 FROM `lucas-491004.case_g4.ravenstack_subscriptions`
 )

--fricção e experiencia
,support_tickets as (
SELECT DISTINCT
ticket_id
,account_id
,submitted_at
,closed_at
,resolution_time_hours
,priority
,first_response_time_minutes
,satisfaction_score
,escalation_flag

 FROM `lucas-491004.case_g4.ravenstack_support_tickets`
 )

--AGREGAR POR ACCOUNT--

 ,churn_by_account as (
  SELECT
    account_id,
    1 as churned,
    MIN(churn_date) as churn_date,
    COUNT(*) as churn_event_count,
    SUM(refund_amount_usd) as total_refund_usd,
    MAX(CAST(preceding_upgrade_flag AS INT64)) as had_upgrade_before_churn,
    MAX(CAST(preceding_downgrade_flag AS INT64)) as had_downgrade_before_churn,
    MAX(CAST(is_reactivation AS INT64)) as was_reactivated_before_churn
  FROM churn_events
  GROUP BY 1
)

,subscriptions_by_account as (
  SELECT
    account_id,
    COUNT(DISTINCT subscription_id) as subscription_count,
    MAX(mrr_amount) as current_or_max_mrr,
    MAX(arr_amount) as current_or_max_arr,
    MAX(seats) as max_seats,
    MAX(CAST(is_trial AS INT64)) as ever_trial,
    SUM(CAST(upgrade_flag AS INT64)) as total_upgrades,
    SUM(CAST(downgrade_flag AS INT64)) as total_downgrades,
    MAX(CAST(churn_flag AS INT64)) as subscription_churn_flag,
    MAX(CAST(auto_renew_flag AS INT64)) as auto_renew_enabled
  FROM subscriptions
  GROUP BY 1
)

,usage_joined as (
  SELECT
    s.account_id,
    fu.subscription_id,
    fu.usage_date,
    fu.feature_name,
    fu.usage_count,
    fu.usage_duration_secs,
    fu.error_count,
    fu.is_beta_feature
  FROM feature_usage fu
  LEFT JOIN subscriptions s
    ON fu.subscription_id = s.subscription_id
)
,usage_by_account as (
  SELECT
    account_id,
    COUNT(*) as usage_event_count,
    SUM(usage_count) as total_usage_count,
    AVG(usage_count) as avg_usage_count,
    SUM(usage_duration_secs) as total_usage_duration_secs,
    AVG(usage_duration_secs) as avg_usage_duration_secs,
    SUM(error_count) as total_error_count,
    SAFE_DIVIDE(SUM(error_count), NULLIF(SUM(usage_count),0)) as error_rate_per_usage,
    COUNT(DISTINCT feature_name) as distinct_features_used,
    AVG(CAST(is_beta_feature AS INT64)) as beta_feature_ratio
  FROM usage_joined
  GROUP BY 1
)

,tickets_by_account as (
  SELECT
    account_id,
    COUNT(DISTINCT ticket_id) as ticket_count,
    AVG(resolution_time_hours) as avg_resolution_time_hours,
    MAX(resolution_time_hours) as max_resolution_time_hours,
    AVG(first_response_time_minutes) as avg_first_response_time_minutes,
    AVG(satisfaction_score) as avg_satisfaction_score,
    SUM(CAST(escalation_flag AS INT64)) as escalation_count,
    SAFE_DIVIDE(SUM(CAST(escalation_flag AS INT64)), COUNT(DISTINCT ticket_id)) as escalation_rate
  FROM support_tickets
  GROUP BY 1
)

-- MASTER TABLE

,final_base as (
  SELECT
    a.account_id,
    a.account_name,
    a.industry,
    a.country,
    a.signup_date,
    a.referral_source,
    a.plan_tier as account_plan_tier,
    a.seats as account_seats,
    CAST(a.is_trial AS INT64) as account_is_trial,
    CAST(a.churn_flag AS INT64) as account_churn_flag,

    COALESCE(c.churned, 0) as churned,
    c.churn_date,
    c.churn_event_count,
    c.total_refund_usd,
    c.had_upgrade_before_churn,
    c.had_downgrade_before_churn,
    c.was_reactivated_before_churn,

    sb.subscription_count,
    sb.current_or_max_mrr,
    sb.current_or_max_arr,
    sb.max_seats,
    sb.ever_trial,
    sb.total_upgrades,
    sb.total_downgrades,
    sb.subscription_churn_flag,
    sb.auto_renew_enabled,

    ub.usage_event_count,
    ub.total_usage_count,
    ub.avg_usage_count,
    ub.total_usage_duration_secs,
    ub.avg_usage_duration_secs,
    ub.total_error_count,
    ub.error_rate_per_usage,
    ub.distinct_features_used,
    ub.beta_feature_ratio,

    tb.ticket_count,
    tb.avg_resolution_time_hours,
    tb.max_resolution_time_hours,
    tb.avg_first_response_time_minutes,
    tb.avg_satisfaction_score,
    tb.escalation_count,
    tb.escalation_rate,

    DATE_DIFF(CURRENT_DATE(), DATE(a.signup_date), DAY) as account_age_days,
    SAFE_DIVIDE(ub.total_usage_count, NULLIF(a.seats,0)) as usage_per_seat,
    SAFE_DIVIDE(tb.ticket_count, NULLIF(a.seats,0)) as tickets_per_seat,
    SAFE_DIVIDE(tb.ticket_count, NULLIF(ub.total_usage_count,0)) as ticket_per_usage_ratio
  FROM accounts a
  LEFT JOIN churn_by_account c
    ON a.account_id = c.account_id
  LEFT JOIN subscriptions_by_account sb
    ON a.account_id = sb.account_id
  LEFT JOIN usage_by_account ub
    ON a.account_id = ub.account_id
  LEFT JOIN tickets_by_account tb
    ON a.account_id = tb.account_id
)


-- identificado inconsistencias na base --
-- fonte da verdade ser´´a eventos de churna de origem base_churn_events. Ignorar: accounts.churn_flag e subscriptions.churn_flag ---

SELECT
  account_id,
  account_name,
  industry,
  country,
  signup_date,
  referral_source,
  account_plan_tier,
  account_seats,
  account_is_trial,

  -- target única
  COALESCE(churned, 0) AS churned,

  -- subscriptions / monetização
  COALESCE(subscription_count, 0) AS subscription_count,
  COALESCE(current_or_max_mrr, 0) AS current_or_max_mrr,
  COALESCE(current_or_max_arr, 0) AS current_or_max_arr,
  COALESCE(max_seats, 0) AS max_seats,
  COALESCE(ever_trial, 0) AS ever_trial,
  COALESCE(total_upgrades, 0) AS total_upgrades,
  COALESCE(total_downgrades, 0) AS total_downgrades,
  COALESCE(auto_renew_enabled, 0) AS auto_renew_enabled,

  -- uso
  COALESCE(usage_event_count, 0) AS usage_event_count,
  COALESCE(total_usage_count, 0) AS total_usage_count,
  COALESCE(avg_usage_count, 0) AS avg_usage_count,
  COALESCE(total_usage_duration_secs, 0) AS total_usage_duration_secs,
  COALESCE(avg_usage_duration_secs, 0) AS avg_usage_duration_secs,
  COALESCE(total_error_count, 0) AS total_error_count,
  COALESCE(error_rate_per_usage, 0) AS error_rate_per_usage,
  COALESCE(distinct_features_used, 0) AS distinct_features_used,
  COALESCE(beta_feature_ratio, 0) AS beta_feature_ratio,

  -- suporte
  COALESCE(ticket_count, 0) AS ticket_count,
  COALESCE(avg_resolution_time_hours, 0) AS avg_resolution_time_hours,
  COALESCE(max_resolution_time_hours, 0) AS max_resolution_time_hours,
  COALESCE(avg_first_response_time_minutes, 0) AS avg_first_response_time_minutes,

  -- manter score sem imputar
  avg_satisfaction_score,
  IF(avg_satisfaction_score IS NOT NULL, 1, 0) AS has_satisfaction,

  COALESCE(escalation_count, 0) AS escalation_count,
  COALESCE(escalation_rate, 0) AS escalation_rate,

  -- derivados
  COALESCE(account_age_days, 0) AS account_age_days,
  COALESCE(usage_per_seat, 0) AS usage_per_seat,
  COALESCE(tickets_per_seat, 0) AS tickets_per_seat,
  COALESCE(ticket_per_usage_ratio, 0) AS ticket_per_usage_ratio,

  -- flags auxiliares
  IF(COALESCE(total_usage_count, 0) > 0, 1, 0) AS has_usage,
  IF(COALESCE(ticket_count, 0) > 0, 1, 0) AS has_tickets

FROM final_base
ORDER BY account_id



