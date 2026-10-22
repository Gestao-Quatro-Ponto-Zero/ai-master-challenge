export type Metric = { value: number | null; status: string; definition: string; denominator?: string | null }
export type MonthlyPoint = {
  month: string
  churn_event_rows: number
  unique_event_accounts: number
  nonreactivation_event_rows: number
  reactivation_event_rows: number
  usage_rows: number
  usage_accounts: number
  usage_count: number
  ticket_count: number
  satisfaction_n: number
  satisfaction_mean: number | null
}
export type SegmentPoint = {
  name: string
  accounts: number
  churn_flag_true: number
  churn_flag_rate: number
  event_accounts: number
  event_account_rate: number
}
export type Finding = {
  id: string
  title: string
  statement: string
  evidence: string[]
  interpretation: string
  confidence: string
}
export type SupportComparison = {
  group: string
  accounts: number
  ticket_rows: number
  first_response_n: number
  first_response_median_minutes: number | null
  resolution_n: number
  resolution_median_hours: number | null
  satisfaction_n: number
  satisfaction_mean: number | null
  satisfaction_missing: number
  escalation_n: number
  escalated_tickets: number
  escalation_rate: number | null
}
export type Analysis = {
  dataset: { source: string; synthetic: boolean; window: string; license_note: string }
  record_counts: Record<string, number>
  metrics: Record<string, Metric>
  data_quality: Record<string, unknown>
  monthly: MonthlyPoint[]
  reasons: { reason: string; event_rows: number; unique_accounts: number; recorded_refunds_usd: number; interpretation: string }[]
  support_comparison: SupportComparison[]
  segments: Record<string, SegmentPoint[]>
  findings: Finding[]
  methodology: string[]
}
export type BusinessLabel = 'account_flag' | 'any_event' | 'nonreactivation_event' | 'subscription_flag_account'
export type BusinessSegment = {
  dimension: string
  segment: string
  label: BusinessLabel
  accounts: number
  positive_accounts: number
  prevalence: number
  wilson_95: [number, number] | null
  small_sample: boolean
}
export type BusinessCohort = {
  cohort: string
  accounts: number
  interpretation: string
  event_window_days_from_cohort_start_to_last_event?: number | null
  account_flag_accounts: number
  account_flag_share: number
  any_event_accounts: number
  any_event_share: number
  nonreactivation_event_accounts: number
  nonreactivation_event_share: number
  subscription_flag_account_accounts: number
  subscription_flag_account_share: number
}
export type BusinessSupportGroup = {
  label: BusinessLabel
  group: 'positive' | 'negative'
  account_count: number
  accounts_with_tickets: number
  ticket_rows: number
  satisfaction_mean_ticket: number | null
  satisfaction_scored_tickets: number
  satisfaction_missing_tickets: number
  satisfaction_mean_account_average: number | null
  accounts_with_satisfaction: number
  first_response_median_minutes: number | null
  first_response_n: number
  resolution_median_hours: number | null
  resolution_n: number
  escalated_ticket_rows: number
  escalation_ticket_rows_n: number
  mean_account_escalation_rate: number | null
  accounts_with_escalation_data: number
}
export type BusinessAccountCandidate = {
  account_id: string
  account_name: string
  industry: string
  country: string
  referral_source: string
  plan_tier: string
  seats: number | null
  is_trial: boolean
  labels: Record<BusinessLabel, boolean>
  event_rows: number
  nonreactivation_event_rows: number
  ticket_rows: number
  escalated_ticket_rows: number
  valid_interval_usage_rows: number
  valid_interval_usage_count: number
  selection_reason: string
}
export type BusinessInvestigation = {
  metadata: { generated_by: string; source: string; outcome_note: string; max_event_date: string | null }
  record_counts: Record<string, number>
  labels: { account_positive_counts: Record<BusinessLabel, number>; accounts: number; any_label_disagreement_accounts: number; pairwise_crosstabs: Record<string, Record<string, number>>; event_rows_before_signup: number; event_rows_missing_date: number; event_rows_by_year: Record<string, number> }
  segments: BusinessSegment[]
  subscription_segments: Array<{ dimension: string; segment: string; label: string; subscriptions: number; flagged_subscriptions: number; prevalence: number | null; wilson_95: [number, number] | null }>
  segment_exploratory_rankings_min_30: BusinessSegment[]
  cohorts: { definition: string; rows: BusinessCohort[]; first_subscription_start_definition: string; first_subscription_start_rows: BusinessCohort[]; retention_heatmap: null; status: string; reason: string }
  usage: {
    concentration: { valid_interval_usage_rows: number; valid_unique_usage_ids_with_any_valid_row: number; valid_unique_usage_count_sum: number; valid_rows_after_first_source_occurrence: number; valid_usage_count_after_first_source_occurrence: number; valid_rows_with_duplicate_ids: number; valid_rows_after_excluding_all_rows_in_duplicate_id_groups: number; accounts_with_any_valid_interval_usage: number; accounts_without_valid_interval_usage: number; valid_interval_usage_count_sum: number; top_10_accounts_share: number | null; top_50_accounts_share: number | null; top_decile_accounts_share: number | null; valid_interval_rows_excluded_by_reason: Record<string, number>; duplicate_usage_id_groups: number; rows_in_duplicate_usage_id_groups: number; excess_rows_after_one_per_usage_id: number }
    by_label: Array<{ label: BusinessLabel; group: 'positive' | 'negative'; accounts: number; accounts_with_valid_interval_usage: number; valid_interval_usage_count_sum: number; mean_usage_count_per_account: number | null; median_usage_count_per_account: number | null; mean_usage_count_among_users: number | null; mean_errors_per_account: number | null; temporal_note: string }>
    feature_adoption: Array<{ feature: string; accounts: number; share_of_all_accounts: number; valid_usage_rows: number; usage_count_sum: number; error_count_sum: number; beta_usage_rows: number }>
    activation_proxy: { status: string; definition: string; account_count_with_proxy: number; median_days_from_signup: number | null; accounts_first_use_before_signup: number; accounts_first_use_within_7_days: number; accounts_first_use_within_30_days: number; limitation: string }
    monthly_source_trend: Array<{ month: string; source_rows: number; distinct_accounts_observed: number; recorded_usage_count: number; rows_after_first_source_occurrence: number; usage_count_after_first_source_occurrence: number; valid_interval_rows: number; valid_interval_usage_count: number; interpretation: string }>
    yearly_source_trend: Array<{ year: number; source_rows: number; distinct_accounts_observed: number; observed_account_months: number; recorded_usage_count: number; usage_count_per_observed_account_month: number | null; mean_recorded_usage_count_per_account: number | null; median_recorded_usage_count_per_account: number | null; source_rows_after_first_duplicate_occurrence: number; usage_count_after_first_duplicate_occurrence: number; valid_interval_rows: number; valid_interval_distinct_accounts: number; valid_interval_usage_count: number; classification: string }>
    segment_yearly_source_trend: Array<{ dimension: string; segment: string; year: number; account_denominator: number; accounts_with_observed_usage: number; recorded_usage_count: number; mean_recorded_usage_count_per_segment_account: number | null; median_recorded_usage_count_per_segment_account: number | null; prior_year_mean_recorded_usage_count_per_segment_account: number | null; change_from_prior_year_pct: number | null; classification: string }>
  }
  support: { by_label: BusinessSupportGroup[]; ticket_priority_by_label: Array<{ label: BusinessLabel; group: 'positive' | 'negative'; priority: string; accounts: number; ticket_rows: number }>; satisfaction_missing_all_tickets: number; satisfaction_missing_share: number | null; interpretation: string }
  revenue: { subscription_rows: number; accounts_represented: number; mrr_recorded_rows_n: number; mrr_row_min: number | null; mrr_row_median: number | null; mrr_row_max: number | null; mrr_zero_rows: number; arr_recorded_rows_n: number; arr_row_min: number | null; arr_row_median: number | null; arr_row_max: number | null; arr_zero_rows: number; mrr_row_sum_not_revenue: number; arr_row_sum_not_revenue: number; refund_observed_sum_usd: number; refund_nonzero_event_rows: number; current_mrr_lost_revenue_grr_nrr_ltv_exposure: null; limitation: string }
  account_investigation_candidates: BusinessAccountCandidate[]
  hypotheses: Array<{ hypothesis: string; classification: string; evidence: string; counterevidence: string; priority: string; next_test: string }>
  recommendations: Array<{ priority: number; action: string; function: string; target: string; evidence: string; effort: string; success_metric: string; validation: string; impact: string }>
  limitations: string[]
}
export type HistoricalAnnual = {
  year: number
  opening_accounts: number
  opening_subscription_rows: number
  closing_accounts: number
  closing_subscription_rows: number
  accounts_first_subscription_started_during_year: number
  first_subscription_cohort_active_at_year_end: number
  first_subscription_cohort_inactive_at_year_end: number
  first_observed_acquisitions_active_at_year_end: number
  date_inferred_reactivations_active_at_year_end: number
  accounts_starting_exactly_at_closing_boundary: number
  gross_opening_account_exits_any_gap: number
  reactivated_opening_accounts_after_gap: number
  opening_accounts_inactive_at_year_end: number
  classical_logo_churn_rate_gross_exit: number | null
  classical_logo_churn_rate_year_end_lost: number | null
  opening_subscriptions_not_active_at_year_end: number
  opening_subscriptions_with_churn_flag: number
  subscription_end_rows_during_year: number
  subscription_churn_rate_opening_cohort: number | null
  event_rows: number
  reactivation_marked_event_rows: number
  nonreactivation_event_accounts: number
  reactivation_marked_event_accounts: number
  opening_accounts_with_account_churn_flag: number
  opening_accounts_with_nonreactivation_event: number
  opening_accounts_with_reactivation_marked_event: number
  movement_equation: { opening: number; first_observed_new: number; reactivated_previously_seen: number; lost_at_year_end: number; boundary_starts_at_close: number; calculated_closing: number; observed_closing: number; residual: number; note: string }
  evidence_status: string
  assumptions: string[]
}
export type HistoricalChurn = {
  metadata: { generated_by: string; source_dir: string; source_hashes_sha256: Record<string, string>; latest_source_dates: Record<string, string | null> }
  source_counts: Record<string, number>
  snapshots: Record<string, { active_accounts: number; active_subscription_rows: number; accounts_with_multiple_active_subscription_rows: number }>
  annual: Record<string, HistoricalAnnual>
  monthly: Array<{ month: string; opening_accounts: number; gross_logo_exits_any_interval_gap: number; accounts_reactivated_after_gap: number; closing_accounts: number; logo_churn_rate: number | null; opening_subscriptions: number; opening_subscriptions_not_active_at_next_boundary: number; subscription_churn_rate: number | null; evidence_status: string }>
  cohorts: { definition: string; status: string; rows: Array<{ cohort: string; elapsed_month: number; initial_accounts: number; active_accounts: number; retention_rate: number | null; snapshot_date: string }>; latest_by_cohort: Array<{ cohort: string; elapsed_month: number; initial_accounts: number; active_accounts: number; retention_rate: number | null; snapshot_date: string }>; diagnostic: { cohort_count: number; cohort_month_points: number; points_below_100_percent: number; minimum_date_rule_retention: number | null; latest_boundary_all_cohorts_active: boolean; interim_gaps: Array<{ cohort: string; elapsed_month: number; initial_accounts: number; active_accounts: number; retention_rate: number; snapshot_date: string }> } }
  event_date_conflicts: Record<string, { nonreactivation_event_rows: number; rows_during_any_date_active_subscription: number; rows_without_any_date_active_subscription: number }>
  data_quality: Record<string, unknown>
}
export type G4CustomerChurn = {
  primary_customer_churn: {
    value: number | null
    period: string
    numerator: number | null
    denominator: number | null
    formula: string
    classification: string
    reason: string
    conditional_date_result_2023: number | null
    conditional_date_result_2024: number | null
    conditional_numerator_2024: number
    conditional_denominator_2024: number
  }
  annual: Record<string, {
    opening_active_accounts: number
    opening_accounts_with_any_date_coverage_gap: number
    opening_accounts_without_coverage_at_close: number
    conditional_gross_date_churn_rate: number | null
    conditional_subscription_churn_rate: number | null
    opening_accounts_with_nonreactivation_event: number
    nonreactivation_event_rows_with_active_subscription: number
    opening_accounts_with_account_churn_flag: number
  }>
  monthly: Array<{ period: string; opening_accounts: number; date_gap_accounts: number; accounts_without_coverage_at_close: number; conditional_date_gap_rate: number | null; evidence_classification: string }>
  quarterly: Array<{ period: string; opening_accounts: number; date_gap_accounts: number; accounts_without_coverage_at_close: number; conditional_date_gap_rate: number | null; evidence_classification: string }>
  snapshots: Record<string, { unique_active_accounts: number; active_subscription_rows: number }>
  cohorts: { status: string; definition: string; rows: Array<{ cohort: string; elapsed_month: number; initial_accounts: number; active_by_recorded_dates: number; conditional_retention: number | null; boundary_date: string; evidence_classification: string }>; limitation: string }
  reconciliation: {
    unique_account_flag_true_all_history: number
    unique_accounts_with_any_event_all_history: number
    unique_accounts_with_nonreactivation_event_all_history: number
    nonreactivation_event_rows_2024_with_active_subscription: number
    invalid_nonpositive_subscription_intervals: number
    movement_bridge: Record<string, number | string>
  }
  segments: Array<{ dimension: string; segment: string; accounts: number; account_flag_true: number; account_flag_prevalence: number | null; accounts_with_nonreactivation_event_all_history: number; all_history_event_prevalence: number | null; accounts_with_2024_nonreactivation_event: number; '2024_event_prevalence': number | null; label_note: string }>
  account_review_candidates: Array<{ account_id: string; industry: string; country: string; referral_source: string; plan_tier: string; account_churn_flag: boolean; nonreactivation_event_rows_all_history: number; nonreactivation_event_in_2024: boolean; opening_2024_date_active: boolean; classification: string }>
  methodology: string[]
}
export type PortfolioPeriod = {
  period: string
  period_type: string
  start_date: string
  end_date: string
  opening_plan_relations: number
  new_plan_relationships: number
  reactivated_plan_relationships: number
  gross_plan_relation_loss_events: number
  opening_relations_lost_any_time: number
  opening_relations_lost_at_close: number
  unique_plan_relations_with_loss_events: number
  closing_plan_relations: number
  net_change: number
  plan_relation_bridge_residual: number
  opening_cohort_churn_any_pct: number | null
  opening_cohort_churn_at_close_pct: number | null
  opening_relations_lost_then_active_at_close: number
  opening_customers: number
  closing_customers: number
  opening_customers_lost_any_time: number
  opening_customers_lost_at_close: number
  opening_cohort_customer_churn_any_pct: number | null
  opening_cohort_customer_churn_at_close_pct: number | null
  gross_customer_churn_events: number
  new_customers: number
  customer_reactivations: number
  customer_bridge_residual: number
  plan_reactivations: number
  possible_upgrade_candidates: number
  possible_downgrade_candidates: number
  portfolio_expansion_events: number
  portfolio_contraction_events: number
  methodology: string
  plan_segments: Array<{ plan_tier: string; opening_relations: number; new_relations: number; reactivations: number; gross_loss_events: number; opening_relations_lost_any_time: number; opening_relations_lost_at_close: number; closing_relations: number; opening_cohort_loss_rate_pct: number | null }>
  account_segments: Record<'industry' | 'country' | 'referral_source', Array<{ segment: string; opening_customers: number; new_customers: number; customer_reactivations: number; opening_customers_lost_any_time: number; opening_customers_lost_at_close: number; closing_customers: number; opening_customer_loss_rate_pct: number | null; opening_plan_relations: number; new_plan_relationships: number; plan_reactivations: number; gross_plan_loss_events: number; opening_relations_lost_any_time: number; opening_relations_lost_at_close: number; closing_plan_relations: number; opening_plan_loss_rate_pct: number | null }>>
  recorded_event_rows?: number
  recorded_event_accounts?: number
  recorded_nonreactivation_event_rows?: number
  recorded_reactivation_event_rows?: number
  recorded_events_per_opening_customer_pct?: number | null
}
export type KeyMoment = {
  id: string
  type: 'RATE_PEAK' | 'LOSS_VOLUME_PEAK' | 'ACQUISITION_CHANGE' | 'RECOVERY_MOMENT' | 'PORTFOLIO_CONTRACTION' | 'RATE_VS_VOLUME_DIVERGENCE' | 'DATA_QUALITY_EVENT'
  month: string
  metric: string
  value: number
  numerator: number | null
  denominator: number | null
  comparison: Record<string, string | number | null>
  criterion: string
  segments: Array<{ dimension: string; segment: string; numerator?: number; denominator?: number | null; rate_pct?: number | null; affected_accounts?: number; interpretation?: string }>
  accounts: Array<{ account_id: string; movement_types: string[]; plans: string[]; dates: string[] }>
  account_count: number
  accounts_truncated: boolean
  evidence_classification: string
  executive_explanation: string
  investigation_action: string
}
export type KeyMoments = { classification: string; months_analyzed: number; criteria_note: string; moments: KeyMoment[] }
export type DailyPortfolioChurn = {
  metadata: { status: string; grain: string; observation_start: string; observation_end: string; earliest_subscription_start: string; interval_rule: string; actual_product_identity: string; plan_identity: string; timezone: string; source_hashes_sha256: Record<string, string>; source_schema: Record<string, string[]> }
  summary: { daily_rows: number; plan_relation_loss_events: number; new_plan_relationships: number; plan_relation_reactivations: number; customer_churn_events: number; new_customers: number; customer_reactivations: number; invalid_intervals: number; merged_plan_relation_intervals: number; portfolio_expansion_events: number; portfolio_contraction_events: number; possible_upgrade_pairs_30d: number; possible_downgrade_pairs_30d: number; plan_bridge_failure_days: number; customer_bridge_failure_days: number; unique_accounts_with_plan_loss: number; plan_loss_events_with_customer_retained: number; plan_loss_events_with_complete_customer_loss: number; unique_accounts_retaining_other_plan_after_loss: number; unique_accounts_losing_all_plans: number; unique_accounts_with_portfolio_expansion: number; unique_accounts_with_portfolio_contraction: number; source_reported_upgrade_flag_rows: number; source_reported_downgrade_flag_rows: number }
  annual_monthly_summary: Record<string, { months: number; opening_customers_first_month: number; closing_customers_last_month: number; opening_account_months: number; new_customers: number; customer_reactivations: number; complete_customer_loss_events: number; opening_plan_relations_first_month: number; closing_plan_relations_last_month: number; opening_plan_relation_months: number; new_plan_relationships: number; plan_reactivations: number; gross_plan_loss_events: number; opening_cohort_plan_losses_sum: number; recorded_event_rows: number; recorded_event_rows_per_100_opening_account_months: number | null; customer_coverage_loss_events_per_100_opening_account_months: number | null; plan_loss_events_per_100_opening_relation_months: number | null; classification: string }>
  reconciliation: { daily_plan_bridge_failures: string[]; daily_customer_bridge_failures: string[] }
  calendar_boundary_snapshots: Record<string, { unique_active_accounts: number; account_plan_proxy_relations: number; classification: string; ledger_opening_accounts_before_date_transitions?: number }>
  periods: Record<string, PortfolioPeriod[]>
  event_reconciliation: { event_rows: number; rows_on_account_plan_loss_date: number; unique_event_accounts: number; ambiguous_account_only_linkage: boolean; events_without_same_day_account_plan_loss: number; window_counts: Record<string, number>; by_reason: Record<string, { event_rows: number; rows_on_plan_loss_date: number; unique_accounts: number; window_counts: Record<string, number> }> }
  plan_transition_analysis: { classification: string; assumed_plan_order: Record<string, number>; plan_order_evidence: string; source_flags: Record<string, number>; windows_days: Record<string, { possible_upgrade_pairs: number; possible_downgrade_pairs: number; unique_accounts: number }>; candidate_transitions: Array<{ date: string; type: string; account_id: string; from_plan: string; to_plan: string; days_between_loss_and_start: number; transition_timing: string; classification: string }> }
  plan_proxy_summary: Array<{ plan_tier: string; source_subscription_rows: number; distinct_accounts: number; loss_events: number; new_relations: number; reactivations: number; opening_2024_relations: number; opening_2024_relations_lost_any_time: number; opening_2024_relations_lost_at_close: number; closing_2024_relations: number; opening_2024_cohort_loss_pct: number | null }>
  segment_summary: Record<string, Array<{ segment: string; account_denominator: number; accounts_with_plan_loss: number; plan_loss_events: number; accounts_with_customer_loss: number; evidence: string }>>
  account_movement_candidates: Array<{ account_id: string; industry: string; country: string; referral_source: string; account_plan_tier: string; plan_loss_events: number; complete_customer_loss_events: number; classification: string }>
  financial_metrics: { status: string; revenue_expansion: number | null; revenue_contraction: number | null; gross_revenue_churn: number | null; net_revenue_churn: number | null; reason: string }
  daily: Array<{ date: string; opening_plan_relations: number; plan_relation_losses: number; new_plan_relationships: number; plan_relation_reactivations: number; closing_plan_relations: number; retained_plan_relationships: number; daily_plan_churn_rate_pct: number | null; opening_customers: number; customer_churn: number; new_customers: number; customer_reactivations: number; closing_customers: number; portfolio_expansion_accounts: number; portfolio_contraction_accounts: number; daily_customer_churn_rate_pct: number | null }>
  movements: Array<{ date: string; type: string; account_id: string; plan_tier?: string }>
  key_moments: KeyMoments
  invalid_intervals: Array<{ subscription_id: string; reason: string; start_date?: string; end_date?: string | null }>
  assumptions: string[]
}
export type MonthlyLabPlanInput = {
  plan_tier: string
  opening_relations: number
  new_relations: number
  loss_events: number
  reactivations: number
  opening_cohort_loss_any: number
  opening_cohort_loss_at_close: number
  assumed_monthly_value: number
}
export type MonthlyLabScenarioInput = {
  month: string
  plans: MonthlyLabPlanInput[]
  opening_customers: number
  new_customers: number
  customer_loss_events: number
  customer_reactivations: number
  opening_customer_loss_any: number
  opening_customer_loss_at_close: number
  portfolio_expansions: number
  portfolio_contractions: number
  possible_upgrades: number
  possible_downgrades: number
  assumed_customer_monthly_value: number
  assumed_acquisition_cost_per_customer: number
  assumed_retention_cost_per_account: number
  assumed_uptake_pct: number
  assumed_incremental_retention_lift_pct: number
  horizon_months: number
}
export type MonthlyLabScenario = {
  status: string
  evidence_classification: string
  month: string
  observed_baseline: Record<string, any>
  scenario: Record<string, any>
  comparison: Record<string, any>
  assumptions: MonthlyLabScenarioInput
  limitations: string[]
}
export type ContractChurnSubscription = {
  subscription_id: string; account_id: string; start_date: string; end_date: string; plan_tier: string
  billing_frequency: string; seats: number | null; mrr_amount_recorded: number | null; arr_amount_recorded: number | null
  subscription_churn_flag: boolean; upgrade_flag: boolean; downgrade_flag: boolean; account_churn_flag: boolean
  industry: string; country: string; referral_source: string; account_subscription_rows: number
  other_subscription_active_at_termination: boolean; other_active_subscription_ids_at_termination: string[]
  later_subscriptions_after_termination: string[]; successor_candidate_ids_unconfirmed: string[]
  account_coverage_continuous_during_2024: boolean; account_active_2025_01_01_by_date: boolean
  annual_account_event_rows: number; annual_account_nonreactivation_event_rows: number; exclusive_case_class: string
  classification_note: string
}
export type ContractChurnEvent = {
  churn_event_id: string; account_id: string; churn_date: string; reason_code: string; feedback_text: string | null
  account_churn_flag: boolean; account_plan_tier: string; industry: string; country: string; referral_source: string
  subscription_rows_for_account: number; active_subscription_count_on_event_date: number
  active_subscription_ids_on_event_date: string[]; nearest_same_account_end_date: string | null
  nearest_end_date_difference_days: number | null; event_days_after_nearest_end: number | null
  within_0_days_of_end: boolean; within_7_days_of_end: boolean; within_30_days_of_end: boolean
  within_60_days_of_end: boolean; event_subscription_link: string
}
export type ContractChurn = {
  metadata: { event_join_key: string; date_rule: string; files_sha256: Record<string, string> }
  revalidation: Record<string, any>
  ended_subscription_class_counts: Record<string, number>
  ended_subscriptions: ContractChurnSubscription[]
  event_end_proximity_counts: Record<string, Record<string, number>>
  event_reasons: Array<{ reason_code: string; nonreactivation_event_rows: number; events_with_active_subscription: number; events_with_same_account_end_within_30d: number; share_of_conflicting_443: number }>
  event_segments: Record<string, Array<{ segment: string; nonreactivation_event_rows: number; active_subscription_event_rows: number; share_of_472_nonreactivation_rows: number; share_of_443_conflicting_events: number }>>
  event_account_investigation_examples: Array<{ account_id: string; industry: string; country: string; referral_source: string; account_plan_tier: string; account_churn_flag: boolean; nonreactivation_event_rows: number; active_subscription_event_rows: number; event_reasons: Record<string, number>; subscription_end_dates_2024: string[] }>
  reactivation_summary: { event_rows: number; distinct_accounts: number; rows_with_active_subscription_on_event_date: number; rows_after_any_same_account_subscription_end: number; rows_with_later_same_account_subscription_start: number; rows_after_prior_nonreactivation_event: number; distinct_accounts_in_2024_opening_base: number; interpretation: string }
  reactivation_events: Array<{ churn_event_id: string; account_id: string; churn_date: string; reason_code: string; active_subscription_count_on_event_date: number; nearest_prior_end_date: string | null; days_since_nearest_prior_end: number | null; prior_nonreactivation_event_ids: string[]; event_subscription_link: string }>
  account_reconciliation: { cross_tab: Record<string, Record<string, number>>; account_rows: Array<Record<string, any>>; [key: string]: any }
  financial_descriptives: Record<string, any>
  conflicting_events: ContractChurnEvent[]
  limitations: string[]
}
export type ReconciliationAccount = {
  account_id: string
  account_name: string
  industry: string
  country: string
  churn_flag: boolean
  churn_event_count: number
  status_comparison: string
  active_subscription_rows: number
  active_record_mrr_sum: number
  interpretation: string
}
export type Reconciliation = { warning: string; returned: number; accounts: ReconciliationAccount[] }
export type ScenarioInput = {
  eligible_accounts: number
  operational_capacity: number
  budget: number
  cost_per_contact: number
  assumed_uptake_pct: number
  assumed_effectiveness: number
  assumed_monthly_value_per_retained_account: number
  retention_horizon_months: number
}
export type Scenario = {
  status: string
  currency_unit: string
  assumptions: ScenarioInput
  selected_accounts: number
  expected_participants: number
  hypothetical_incremental_retained_accounts: number
  intervention_cost: number
  hypothetical_retained_value: number | null
  hypothetical_net_value: number | null
  sensitivity: Record<string, number | null>
  scenario_cases: Record<'conservative' | 'base' | 'optimistic', { assumed_uptake_pct: number; assumed_incremental_lift_pct_points: number; expected_participants: number; hypothetical_incremental_retained_accounts: number; gross_hypothetical_value: number | null; intervention_cost: number; hypothetical_net_value: number | null; break_even_monthly_value_per_retained_account: number | null }>
  limitations: string[]
}
