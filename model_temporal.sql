CREATE OR REPLACE MODEL `lucas-491004.case_g4.churn_temporal_model`
OPTIONS(
  model_type = 'boosted_tree_classifier',
  input_label_cols = ['churn_next_month'],
  max_iterations = 10,
  max_tree_depth = 3
) AS

SELECT
  churn_next_month,
  industry,
  current_or_max_mrr,
  total_usage_count,
  error_rate_per_usage,
  ticket_count,
  avg_resolution_time_hours,
  usage_per_seat,
  usage_growth_rate,
  error_growth_rate,
  ticket_growth_rate,
  mrr_growth_rate,
  has_usage,
  has_tickets
FROM `lucas-491004.case_g4.master_table_temporal_monthly`
WHERE snapshot_month IS NOT NULL;