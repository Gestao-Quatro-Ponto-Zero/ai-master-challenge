WITH preds AS (
  SELECT
    account_id,
    predicted_churned_probs[OFFSET(1)].prob AS churn_probability
  FROM ML.PREDICT(
    MODEL `lucas-491004.case_g4.churn_tree_tiny`,
    (
      SELECT *
      FROM `lucas-491004.case_g4.model_base`
    )
  )
),

base AS (
  SELECT
    account_id,
    industry,
    error_rate_per_usage,
    ticket_count,
    avg_resolution_time_hours,
    escalation_rate,
    usage_per_seat,
    has_usage,
    has_tickets
  FROM `lucas-491004.case_g4.model_base`
),

fi AS (
  SELECT
    MAX(CASE WHEN feature = 'industry' THEN importance_gain END) AS w_industry,
    MAX(CASE WHEN feature = 'error_rate_per_usage' THEN importance_gain END) AS w_error_rate_per_usage,
    MAX(CASE WHEN feature = 'ticket_count' THEN importance_gain END) AS w_ticket_count,
    MAX(CASE WHEN feature = 'avg_resolution_time_hours' THEN importance_gain END) AS w_avg_resolution_time_hours,
    MAX(CASE WHEN feature = 'escalation_rate' THEN importance_gain END) AS w_escalation_rate,
    MAX(CASE WHEN feature = 'usage_per_seat' THEN importance_gain END) AS w_usage_per_seat,
    MAX(CASE WHEN feature = 'has_usage' THEN importance_gain END) AS w_has_usage,
    MAX(CASE WHEN feature = 'has_tickets' THEN importance_gain END) AS w_has_tickets
  FROM ML.FEATURE_IMPORTANCE(
    MODEL `lucas-491004.case_g4.churn_tree_tiny`
  )
)

SELECT
  b.account_id,
  p.churn_probability,
  ROUND(p.churn_probability * 100, 0) AS churn_score,

  -- valores das features
  b.industry,
  b.error_rate_per_usage,
  b.ticket_count,
  b.avg_resolution_time_hours,
  b.escalation_rate,
  b.usage_per_seat,
  b.has_usage,
  b.has_tickets,

  -- pesos globais do modelo
  fi.w_industry,
  fi.w_error_rate_per_usage,
  fi.w_ticket_count,
  fi.w_avg_resolution_time_hours,
  fi.w_escalation_rate,
  fi.w_usage_per_seat,
  fi.w_has_usage,
  fi.w_has_tickets

FROM base b
LEFT JOIN preds p
  ON b.account_id = p.account_id
CROSS JOIN fi
ORDER BY churn_score DESC, b.account_id;