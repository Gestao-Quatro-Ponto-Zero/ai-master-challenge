CREATE OR REPLACE MODEL `lucas-491004.case_g4.churn_tree_tiny_industry`
OPTIONS(
  model_type = 'boosted_tree_classifier',
  input_label_cols = ['churned'],
  max_iterations = 3,
  max_tree_depth = 2,
  learn_rate = 0.2,
  subsample = 0.7
) AS

SELECT
  churned,
  industry,
  error_rate_per_usage,
  ticket_count,
  avg_resolution_time_hours,
  escalation_rate,
  usage_per_seat,
  has_usage,
  has_tickets
FROM `lucas-491004.case_g4.model_base`
WHERE churned IS NOT NULL
  AND industry IS NOT NULL;