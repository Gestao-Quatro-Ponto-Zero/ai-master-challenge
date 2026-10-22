import { act } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import type { Analysis, BusinessInvestigation, ContractChurn, DailyPortfolioChurn, G4CustomerChurn, HistoricalChurn, Reconciliation, Scenario } from './contracts'

const analysis: Analysis = {
  dataset: { source: 'test fixture', synthetic: true, window: 'test', license_note: 'test-only fixture' },
  record_counts: { accounts: 2, subscriptions: 2, usage: 2, tickets: 2, churn_events: 1 },
  metrics: {
    recorded_ticket_satisfaction_mean: { value: 4.2, status: 'OBSERVED', definition: 'Test fixture', denominator: '2/2' },
    recorded_refunds_usd: { value: 25, status: 'OBSERVED_FIELD_SUM', definition: 'Test fixture', denominator: '1/1' },
  },
  data_quality: {
    account_churn_flags_true: 1,
    usage_rows_before_subscription_start: 1,
    ticket_satisfaction_missing: 1,
  },
  monthly: [{
    month: '2024-01', churn_event_rows: 1, unique_event_accounts: 1,
    nonreactivation_event_rows: 1, reactivation_event_rows: 0, usage_accounts: 1,
    usage_rows: 2, usage_count: 120, ticket_count: 2, satisfaction_n: 1, satisfaction_mean: 4.2,
  }],
  reasons: [{ reason: 'features', event_rows: 1, unique_accounts: 1, recorded_refunds_usd: 25, interpretation: 'Test only' }],
  support_comparison: [
    {
      group: 'accounts_with_any_event', accounts: 1, ticket_rows: 1,
      first_response_n: 1, first_response_median_minutes: 30,
      resolution_n: 1, resolution_median_hours: 4,
      satisfaction_n: 1, satisfaction_mean: 3.98, satisfaction_missing: 0,
      escalation_n: 1, escalated_tickets: 0, escalation_rate: 0,
    },
    {
      group: 'accounts_without_event', accounts: 1, ticket_rows: 1,
      first_response_n: 1, first_response_median_minutes: 35,
      resolution_n: 1, resolution_median_hours: 5,
      satisfaction_n: 0, satisfaction_mean: null, satisfaction_missing: 1,
      escalation_n: 1, escalated_tickets: 0, escalation_rate: 0,
    },
  ],
  segments: {
    industry: [{ name: 'Test', accounts: 2, churn_flag_true: 1, churn_flag_rate: 0.5, event_accounts: 1, event_account_rate: 0.5 }],
    country: [], referral_source: [], plan_tier: [],
  },
  findings: [],
  methodology: [],
}

const reconciliation: Reconciliation = {
  warning: 'Test fixture only; not a risk score or verified revenue exposure.',
  returned: 1,
  accounts: [{
    account_id: 'acct-test', account_name: 'Test Account', industry: 'Test', country: 'US',
    churn_flag: true, churn_event_count: 1, status_comparison: 'flag_and_event',
    active_subscription_rows: 1, active_record_mrr_sum: 0,
    interpretation: 'Test reconciliation example only.',
  }],
}

const business: BusinessInvestigation = {
  metadata: { generated_by: 'fixture', source: 'test fixture', outcome_note: 'not rates', max_event_date: '2024-12-31' },
  record_counts: { accounts: 2, subscriptions: 2, usage_rows: 2, support_tickets: 2, event_rows: 1 },
  labels: { account_positive_counts: { account_flag: 1, any_event: 1, nonreactivation_event: 1, subscription_flag_account: 1 }, accounts: 2, any_label_disagreement_accounts: 1, pairwise_crosstabs: { account_flag_vs_any_event: { '1:1': 1, '1:0': 0, '0:1': 0, '0:0': 1 } }, event_rows_before_signup: 0, event_rows_missing_date: 0, event_rows_by_year: { '2024': 1 } },
  segments: [{ dimension: 'industry', segment: 'Test', label: 'nonreactivation_event', accounts: 2, positive_accounts: 1, prevalence: 0.5, wilson_95: [0.1, 0.9], small_sample: true }],
  subscription_segments: [], segment_exploratory_rankings_min_30: [],
  cohorts: { definition: 'signup quarter', rows: [], first_subscription_start_definition: 'Earliest listed start', first_subscription_start_rows: [], retention_heatmap: null, status: 'NOT_IDENTIFIABLE', reason: 'Test fixture' },
  usage: { concentration: { valid_interval_usage_rows: 1, valid_unique_usage_ids_with_any_valid_row: 1, valid_unique_usage_count_sum: 1, valid_rows_after_first_source_occurrence: 1, valid_usage_count_after_first_source_occurrence: 1, valid_rows_with_duplicate_ids: 0, valid_rows_after_excluding_all_rows_in_duplicate_id_groups: 1, accounts_with_any_valid_interval_usage: 1, accounts_without_valid_interval_usage: 1, valid_interval_usage_count_sum: 1, top_10_accounts_share: 1, top_50_accounts_share: 1, top_decile_accounts_share: 1, valid_interval_rows_excluded_by_reason: {}, duplicate_usage_id_groups: 0, rows_in_duplicate_usage_id_groups: 0, excess_rows_after_one_per_usage_id: 0 }, by_label: [], feature_adoption: [], activation_proxy: { status: 'CONDITIONAL', definition: 'test proxy', account_count_with_proxy: 1, median_days_from_signup: 4, accounts_first_use_before_signup: 0, accounts_first_use_within_7_days: 1, accounts_first_use_within_30_days: 1, limitation: 'Test fixture' }, monthly_source_trend: [], yearly_source_trend: [{ year: 2023, source_rows: 1, distinct_accounts_observed: 1, observed_account_months: 1, recorded_usage_count: 100, usage_count_per_observed_account_month: 100, mean_recorded_usage_count_per_account: 100, median_recorded_usage_count_per_account: 100, source_rows_after_first_duplicate_occurrence: 1, usage_count_after_first_duplicate_occurrence: 100, valid_interval_rows: 1, valid_interval_distinct_accounts: 1, valid_interval_usage_count: 100, classification: 'fixture' }, { year: 2024, source_rows: 1, distinct_accounts_observed: 1, observed_account_months: 1, recorded_usage_count: 120, usage_count_per_observed_account_month: 120, mean_recorded_usage_count_per_account: 120, median_recorded_usage_count_per_account: 120, source_rows_after_first_duplicate_occurrence: 1, usage_count_after_first_duplicate_occurrence: 120, valid_interval_rows: 1, valid_interval_distinct_accounts: 1, valid_interval_usage_count: 120, classification: 'fixture' }], segment_yearly_source_trend: [] },
  support: { by_label: ['account_flag', 'any_event', 'nonreactivation_event', 'subscription_flag_account'].flatMap((label) => (['positive', 'negative'] as const).map((group) => ({ label: label as 'account_flag' | 'any_event' | 'nonreactivation_event' | 'subscription_flag_account', group, account_count: 1, accounts_with_tickets: 1, ticket_rows: 1, satisfaction_mean_ticket: group === 'positive' ? 3.98 : null, satisfaction_scored_tickets: group === 'positive' ? 1 : 0, satisfaction_missing_tickets: group === 'positive' ? 0 : 1, satisfaction_mean_account_average: group === 'positive' ? 3.98 : null, accounts_with_satisfaction: group === 'positive' ? 1 : 0, first_response_median_minutes: 30, first_response_n: 1, resolution_median_hours: 4, resolution_n: 1, escalated_ticket_rows: 0, escalation_ticket_rows_n: 1, mean_account_escalation_rate: 0, accounts_with_escalation_data: 1 }))), ticket_priority_by_label: [], satisfaction_missing_all_tickets: 1, satisfaction_missing_share: 0.5, interpretation: 'Test only' },
  revenue: { subscription_rows: 2, accounts_represented: 2, mrr_recorded_rows_n: 2, mrr_row_min: 0, mrr_row_median: 0, mrr_row_max: 0, mrr_zero_rows: 2, arr_recorded_rows_n: 2, arr_row_min: 0, arr_row_median: 0, arr_row_max: 0, arr_zero_rows: 2, mrr_row_sum_not_revenue: 0, arr_row_sum_not_revenue: 0, refund_observed_sum_usd: 25, refund_nonzero_event_rows: 1, current_mrr_lost_revenue_grr_nrr_ltv_exposure: null, limitation: 'Test only' },
  account_investigation_candidates: [{ account_id: 'acct-test', account_name: 'Test Account', industry: 'Test', country: 'US', referral_source: 'partner', plan_tier: 'Pro', seats: 5, is_trial: false, labels: { account_flag: true, any_event: true, nonreactivation_event: true, subscription_flag_account: true }, event_rows: 3, nonreactivation_event_rows: 3, ticket_rows: 2, escalated_ticket_rows: 1, valid_interval_usage_rows: 1, valid_interval_usage_count: 5, selection_reason: 'reconciliation only' }],
  hypotheses: [{ hypothesis: 'Test hypothesis', classification: 'UNKNOWN', evidence: 'Test evidence', counterevidence: 'Test limit', priority: 'P0', next_test: 'Test' }],
  recommendations: [{ priority: 1, action: 'Test action', function: 'Analytics', target: 'Eligible accounts', evidence: 'Test evidence', effort: 'Low', success_metric: 'Retention', validation: 'Holdout', impact: 'Unknown' }],
  limitations: ['Test only'],
}

const dailyPortfolio: DailyPortfolioChurn = {
  metadata: { status: 'CONDITIONAL_DATE_RECONSTRUCTION', grain: 'ACCOUNT × PLAN_TIER × CIVIL_DAY', observation_start: '2024-01-01', observation_end: '2024-01-31', earliest_subscription_start: '2024-01-01', interval_rule: '[start_date, end_date)', actual_product_identity: 'NOT_IDENTIFIABLE', plan_identity: 'PLAN-LEVEL PROXY', timezone: 'UNKNOWN', source_hashes_sha256: {}, source_schema: {} },
  summary: { daily_rows: 31, plan_relation_loss_events: 2, new_plan_relationships: 4, plan_relation_reactivations: 1, customer_churn_events: 1, new_customers: 2, customer_reactivations: 1, invalid_intervals: 0, merged_plan_relation_intervals: 4, portfolio_expansion_events: 1, portfolio_contraction_events: 1, possible_upgrade_pairs_30d: 2, possible_downgrade_pairs_30d: 1, plan_bridge_failure_days: 0, customer_bridge_failure_days: 0, unique_accounts_with_plan_loss: 2, plan_loss_events_with_customer_retained: 1, plan_loss_events_with_complete_customer_loss: 1, unique_accounts_retaining_other_plan_after_loss: 1, unique_accounts_losing_all_plans: 1, unique_accounts_with_portfolio_expansion: 1, unique_accounts_with_portfolio_contraction: 1, source_reported_upgrade_flag_rows: 2, source_reported_downgrade_flag_rows: 1 },
  reconciliation: { daily_plan_bridge_failures: [], daily_customer_bridge_failures: [] },
  calendar_boundary_snapshots: {
    '2023-01-01': { unique_active_accounts: 0, account_plan_proxy_relations: 0, classification: 'Fixture' },
    '2024-01-01': { unique_active_accounts: 3, account_plan_proxy_relations: 4, ledger_opening_accounts_before_date_transitions: 2, classification: 'Fixture' },
    '2024-12-31': { unique_active_accounts: 4, account_plan_proxy_relations: 5, classification: 'Fixture' },
  },
  periods: { MONTHLY: [{ period: '2024-01', period_type: 'MONTHLY', start_date: '2024-01-01', end_date: '2024-01-31', opening_plan_relations: 3, new_plan_relationships: 4, reactivated_plan_relationships: 1, gross_plan_relation_loss_events: 2, opening_relations_lost_any_time: 1, opening_relations_lost_at_close: 1, opening_relations_lost_then_active_at_close: 0, unique_plan_relations_with_loss_events: 2, closing_plan_relations: 4, net_change: 1, plan_relation_bridge_residual: 0, opening_cohort_churn_any_pct: 33.3, opening_cohort_churn_at_close_pct: 33.3, opening_customers: 2, closing_customers: 3, opening_customers_lost_any_time: 1, opening_customers_lost_at_close: 1, opening_cohort_customer_churn_any_pct: 50, opening_cohort_customer_churn_at_close_pct: 50, gross_customer_churn_events: 1, new_customers: 2, customer_reactivations: 1, customer_bridge_residual: 0, plan_reactivations: 1, possible_upgrade_candidates: 2, possible_downgrade_candidates: 1, portfolio_expansion_events: 1, portfolio_contraction_events: 1, methodology: 'Test fixture', plan_segments: [], account_segments: { industry: [{ segment: 'Test industry', opening_customers: 2, new_customers: 1, customer_reactivations: 0, opening_customers_lost_any_time: 1, opening_customers_lost_at_close: 1, closing_customers: 1, opening_customer_loss_rate_pct: 50, opening_plan_relations: 3, new_plan_relationships: 4, plan_reactivations: 1, gross_plan_loss_events: 2, opening_relations_lost_any_time: 1, opening_relations_lost_at_close: 1, closing_plan_relations: 4, opening_plan_loss_rate_pct: 33.3 }], country: [], referral_source: [] } }], WEEKLY: [], QUARTERLY: [], SEMIANNUAL: [], ANNUAL: [] },
  annual_monthly_summary: { '2023': { months: 12, opening_customers_first_month: 0, closing_customers_last_month: 1, opening_account_months: 1, new_customers: 1, customer_reactivations: 0, complete_customer_loss_events: 0, opening_plan_relations_first_month: 0, closing_plan_relations_last_month: 1, opening_plan_relation_months: 1, new_plan_relationships: 1, plan_reactivations: 0, gross_plan_loss_events: 0, opening_cohort_plan_losses_sum: 0, recorded_event_rows: 0, recorded_event_rows_per_100_opening_account_months: 0, customer_coverage_loss_events_per_100_opening_account_months: 0, plan_loss_events_per_100_opening_relation_months: 0, classification: 'fixture' }, '2024': { months: 12, opening_customers_first_month: 1, closing_customers_last_month: 3, opening_account_months: 2, new_customers: 2, customer_reactivations: 0, complete_customer_loss_events: 0, opening_plan_relations_first_month: 1, closing_plan_relations_last_month: 4, opening_plan_relation_months: 3, new_plan_relationships: 3, plan_reactivations: 1, gross_plan_loss_events: 2, opening_cohort_plan_losses_sum: 1, recorded_event_rows: 1, recorded_event_rows_per_100_opening_account_months: 50, customer_coverage_loss_events_per_100_opening_account_months: 0, plan_loss_events_per_100_opening_relation_months: 66.7, classification: 'fixture' } },
  event_reconciliation: { event_rows: 600, rows_on_account_plan_loss_date: 3, unique_event_accounts: 352, ambiguous_account_only_linkage: true, events_without_same_day_account_plan_loss: 597, window_counts: { '0': 3, '1': 3, '7': 6, '30': 20, '60': 30 }, by_reason: { features: { event_rows: 3, rows_on_plan_loss_date: 1, unique_accounts: 3, window_counts: { '0': 1, '1': 1, '7': 2, '30': 3, '60': 3 } } } },
  plan_proxy_summary: [{ plan_tier: 'Basic', source_subscription_rows: 10, distinct_accounts: 3, loss_events: 2, new_relations: 4, reactivations: 1, opening_2024_relations: 3, opening_2024_relations_lost_any_time: 1, opening_2024_relations_lost_at_close: 1, closing_2024_relations: 2, opening_2024_cohort_loss_pct: 33.3 }],
  plan_transition_analysis: { classification: 'POSSIBLE_ONLY', assumed_plan_order: { Basic: 1, Pro: 2, Enterprise: 3 }, plan_order_evidence: 'Fixture; not verified.', source_flags: { reported_upgrade_flag_rows: 2, reported_downgrade_flag_rows: 1 }, windows_days: { '0': { possible_upgrade_pairs: 1, possible_downgrade_pairs: 0, unique_accounts: 1 }, '1': { possible_upgrade_pairs: 1, possible_downgrade_pairs: 0, unique_accounts: 1 }, '7': { possible_upgrade_pairs: 2, possible_downgrade_pairs: 1, unique_accounts: 2 }, '30': { possible_upgrade_pairs: 2, possible_downgrade_pairs: 1, unique_accounts: 2 } }, candidate_transitions: [] },
  segment_summary: { industry: [{ segment: 'Tech', account_denominator: 2, accounts_with_plan_loss: 1, plan_loss_events: 2, accounts_with_customer_loss: 1, evidence: 'CONDITIONAL_DATE_RECONSTRUCTION' }] },
  account_movement_candidates: [{ account_id: 'acct-test', industry: 'Tech', country: 'US', referral_source: 'organic', account_plan_tier: 'Basic', plan_loss_events: 2, complete_customer_loss_events: 1, classification: 'DATE-RECONCILIATION CANDIDATE; not future risk' }],
  financial_metrics: { status: 'UNKNOWN', revenue_expansion: null, revenue_contraction: null, gross_revenue_churn: null, net_revenue_churn: null, reason: 'No verified ledger.' },
  daily: [{ date: '2024-01-01', opening_plan_relations: 3, plan_relation_losses: 0, new_plan_relationships: 1, plan_relation_reactivations: 0, closing_plan_relations: 4, retained_plan_relationships: 3, daily_plan_churn_rate_pct: 0, opening_customers: 2, customer_churn: 0, new_customers: 1, customer_reactivations: 0, closing_customers: 3, portfolio_expansion_accounts: 1, portfolio_contraction_accounts: 0, daily_customer_churn_rate_pct: 0 }],
  movements: [
    { date: '2024-04-01', type: 'CUSTOMER_CHURN', account_id: 'acct-return' },
    { date: '2024-04-04', type: 'CUSTOMER_REACTIVATION', account_id: 'acct-return' },
  ], invalid_intervals: [], assumptions: ['Plan is a proxy.'],
  key_moments: {
    classification: 'CONDITIONAL_DATE_RECONSTRUCTION · PLAN-LEVEL PROXY', months_analyzed: 24, criteria_note: 'Synthetic fixture.',
    moments: [{ id: 'loss_volume_peak:2024-12:gross_plan_relation_loss_events', type: 'LOSS_VOLUME_PEAK', month: '2024-12', metric: 'gross_plan_relation_loss_events', value: 11, numerator: 11, denominator: null, comparison: { opening_cohort_losses: 5, opening_denominator: 1279 }, criterion: 'Synthetic test case.', segments: [], accounts: [{ account_id: 'acct-moment', movement_types: ['PLAN_RELATION_LOSS'], plans: ['Enterprise'], dates: ['2024-12-10'] }], account_count: 1, accounts_truncated: false, evidence_classification: 'CONDITIONAL_DATE_RECONSTRUCTION · PLAN-LEVEL PROXY', executive_explanation: '11 gross date-derived account × plan-tier coverage loss events occurred in 2024-12; this count can include relationships that began after month opening.', investigation_action: 'Review the test account timeline.' }],
  },
}
const monthlyTemplate = dailyPortfolio.periods.MONTHLY[0]!
dailyPortfolio.periods.MONTHLY = Array.from({ length: 24 }, (_, index) => {
  const date = new Date(Date.UTC(2023, index, 1))
  const period = `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, '0')}`
  const openingCustomers = index === 0 ? 0 : 20 + index * 5
  const openingRelations = index === 0 ? 0 : 25 + index * 7
  const customerLosses = index === 0 ? 0 : 1
  const planLosses = index === 0 ? 0 : 1
  return {
    ...monthlyTemplate,
    period,
    period_type: 'MONTHLY',
    opening_customers: openingCustomers,
    closing_customers: openingCustomers + 2,
    opening_customers_lost_any_time: customerLosses,
    opening_customers_lost_at_close: customerLosses,
    opening_cohort_customer_churn_any_pct: openingCustomers === 0 ? null : customerLosses / openingCustomers * 100,
    opening_cohort_customer_churn_at_close_pct: openingCustomers === 0 ? null : customerLosses / openingCustomers * 100,
    new_customers: 2,
    customer_reactivations: 1,
    opening_plan_relations: openingRelations,
    closing_plan_relations: openingRelations + 3,
    opening_relations_lost_any_time: planLosses,
    opening_relations_lost_at_close: planLosses,
    opening_cohort_churn_any_pct: openingRelations === 0 ? null : planLosses / openingRelations * 100,
    opening_cohort_churn_at_close_pct: openingRelations === 0 ? null : planLosses / openingRelations * 100,
    gross_plan_relation_loss_events: planLosses,
    gross_customer_churn_events: customerLosses,
    new_plan_relationships: 3,
    plan_reactivations: 1,
  }
})
dailyPortfolio.periods.ANNUAL = [{
  ...dailyPortfolio.periods.MONTHLY[0]!, period: '2024', period_type: 'ANNUAL',
  opening_plan_relations: 374, opening_relations_lost_any_time: 7, opening_relations_lost_at_close: 3,
  opening_cohort_churn_any_pct: 7 / 374 * 100, opening_cohort_churn_at_close_pct: 3 / 374 * 100,
  opening_customers: 190, opening_customers_lost_any_time: 0, opening_cohort_customer_churn_any_pct: 0,
}]

const scenario: Scenario = {
  status: 'HYPOTHETICAL',
  currency_unit: 'user-supplied units',
  assumptions: {
    eligible_accounts: 25, operational_capacity: 25, budget: 2500, cost_per_contact: 100,
    assumed_uptake_pct: 1,
    assumed_effectiveness: 0.1, assumed_monthly_value_per_retained_account: 500,
    retention_horizon_months: 3,
  },
  selected_accounts: 25,
  expected_participants: 25,
  hypothetical_incremental_retained_accounts: 2.5,
  intervention_cost: 2500,
  hypothetical_retained_value: 3750,
  hypothetical_net_value: 1250,
  sensitivity: { low_net_value: -625, base_net_value: 1250, high_net_value: 3125 },
  scenario_cases: {
    conservative: { assumed_uptake_pct: 50, assumed_incremental_lift_pct_points: 5, expected_participants: 12.5, hypothetical_incremental_retained_accounts: 0.625, gross_hypothetical_value: 937.5, intervention_cost: 2500, hypothetical_net_value: -1562.5, break_even_monthly_value_per_retained_account: 1333.33 },
    base: { assumed_uptake_pct: 100, assumed_incremental_lift_pct_points: 10, expected_participants: 25, hypothetical_incremental_retained_accounts: 2.5, gross_hypothetical_value: 3750, intervention_cost: 2500, hypothetical_net_value: 1250, break_even_monthly_value_per_retained_account: 333.33 },
    optimistic: { assumed_uptake_pct: 100, assumed_incremental_lift_pct_points: 15, expected_participants: 25, hypothetical_incremental_retained_accounts: 3.75, gross_hypothetical_value: 5625, intervention_cost: 2500, hypothetical_net_value: 3125, break_even_monthly_value_per_retained_account: 222.22 },
  },
  limitations: ['Test fixture only.'],
}
const historical: HistoricalChurn = {
  metadata: { generated_by: 'fixture', source_dir: 'fixture', source_hashes_sha256: {}, latest_source_dates: {} },
  source_counts: { accounts: 500, subscriptions: 5000, churn_events: 600 },
  snapshots: {
    '2023-01-01': { active_accounts: 0, active_subscription_rows: 0, accounts_with_multiple_active_subscription_rows: 0 },
    '2024-01-01': { active_accounts: 191, active_subscription_rows: 655, accounts_with_multiple_active_subscription_rows: 164 },
    '2025-01-01': { active_accounts: 500, active_subscription_rows: 4514, accounts_with_multiple_active_subscription_rows: 500 },
  },
  annual: {
    '2023': { year: 2023, opening_accounts: 0, opening_subscription_rows: 0, closing_accounts: 191, closing_subscription_rows: 655, accounts_first_subscription_started_during_year: 191, first_subscription_cohort_active_at_year_end: 190, first_subscription_cohort_inactive_at_year_end: 1, first_observed_acquisitions_active_at_year_end: 190, date_inferred_reactivations_active_at_year_end: 0, accounts_starting_exactly_at_closing_boundary: 1, gross_opening_account_exits_any_gap: 0, reactivated_opening_accounts_after_gap: 0, opening_accounts_inactive_at_year_end: 0, classical_logo_churn_rate_gross_exit: null, classical_logo_churn_rate_year_end_lost: null, opening_subscriptions_not_active_at_year_end: 0, opening_subscriptions_with_churn_flag: 0, subscription_end_rows_during_year: 18, subscription_churn_rate_opening_cohort: null, event_rows: 73, reactivation_marked_event_rows: 6, nonreactivation_event_accounts: 59, reactivation_marked_event_accounts: 6, opening_accounts_with_account_churn_flag: 0, opening_accounts_with_nonreactivation_event: 0, opening_accounts_with_reactivation_marked_event: 0, movement_equation: { opening: 0, first_observed_new: 190, reactivated_previously_seen: 0, lost_at_year_end: 0, boundary_starts_at_close: 1, calculated_closing: 191, observed_closing: 191, residual: 0, note: 'Test fixture' }, evidence_status: 'UNDEFINED_ZERO_OPENING_BASE', assumptions: [] },
    '2024': { year: 2024, opening_accounts: 191, opening_subscription_rows: 655, closing_accounts: 500, closing_subscription_rows: 4514, accounts_first_subscription_started_during_year: 309, first_subscription_cohort_active_at_year_end: 308, first_subscription_cohort_inactive_at_year_end: 1, first_observed_acquisitions_active_at_year_end: 308, date_inferred_reactivations_active_at_year_end: 1, accounts_starting_exactly_at_closing_boundary: 0, gross_opening_account_exits_any_gap: 0, reactivated_opening_accounts_after_gap: 0, opening_accounts_inactive_at_year_end: 0, classical_logo_churn_rate_gross_exit: 0, classical_logo_churn_rate_year_end_lost: 0, opening_subscriptions_not_active_at_year_end: 66, opening_subscriptions_with_churn_flag: 66, subscription_end_rows_during_year: 468, subscription_churn_rate_opening_cohort: 66 / 655, event_rows: 527, reactivation_marked_event_rows: 55, nonreactivation_event_accounts: 311, reactivation_marked_event_accounts: 49, opening_accounts_with_account_churn_flag: 49, opening_accounts_with_nonreactivation_event: 103, opening_accounts_with_reactivation_marked_event: 9, movement_equation: { opening: 191, first_observed_new: 308, reactivated_previously_seen: 1, lost_at_year_end: 0, boundary_starts_at_close: 0, calculated_closing: 500, observed_closing: 500, residual: 0, note: 'Test fixture' }, evidence_status: 'CONDITIONAL_DATE_RECONSTRUCTION', assumptions: [] },
  },
  monthly: [
    { month: '2023-11', opening_accounts: 149, gross_logo_exits_any_interval_gap: 1, accounts_reactivated_after_gap: 0, closing_accounts: 172, logo_churn_rate: 1 / 149, opening_subscriptions: 421, opening_subscriptions_not_active_at_next_boundary: 7, subscription_churn_rate: 7 / 421, evidence_status: 'CONDITIONAL_DATE_RECONSTRUCTION' },
    { month: '2024-03', opening_accounts: 235, gross_logo_exits_any_interval_gap: 1, accounts_reactivated_after_gap: 1, closing_accounts: 264, logo_churn_rate: 1 / 235, opening_subscriptions: 914, opening_subscriptions_not_active_at_next_boundary: 7, subscription_churn_rate: 7 / 914, evidence_status: 'CONDITIONAL_DATE_RECONSTRUCTION' },
    { month: '2024-04', opening_accounts: 264, gross_logo_exits_any_interval_gap: 1, accounts_reactivated_after_gap: 1, closing_accounts: 282, logo_churn_rate: 1 / 264, opening_subscriptions: 1105, opening_subscriptions_not_active_at_next_boundary: 13, subscription_churn_rate: 13 / 1105, evidence_status: 'CONDITIONAL_DATE_RECONSTRUCTION' },
    { month: '2024-09', opening_accounts: 385, gross_logo_exits_any_interval_gap: 2, accounts_reactivated_after_gap: 1, closing_accounts: 415, logo_churn_rate: 2 / 385, opening_subscriptions: 2378, opening_subscriptions_not_active_at_next_boundary: 26, subscription_churn_rate: 26 / 2378, evidence_status: 'CONDITIONAL_DATE_RECONSTRUCTION' },
  ],
  cohorts: { definition: 'Test conditional cohorts', status: 'CONDITIONAL_DATE_RECONSTRUCTION', rows: [], latest_by_cohort: [], diagnostic: { cohort_count: 24, cohort_month_points: 300, points_below_100_percent: 4, minimum_date_rule_retention: 0.9333, latest_boundary_all_cohorts_active: true, interim_gaps: [] } },
  event_date_conflicts: { '2023': { nonreactivation_event_rows: 67, rows_during_any_date_active_subscription: 47, rows_without_any_date_active_subscription: 20 }, '2024': { nonreactivation_event_rows: 472, rows_during_any_date_active_subscription: 443, rows_without_any_date_active_subscription: 29 } },
  data_quality: {},
}
const contractChurn = {
  metadata: { event_join_key: 'account_id only', date_rule: 'date interval', files_sha256: {} },
  revalidation: { opening_accounts: 191, opening_subscription_ids: 655, subscription_rows_ended_before_2025_boundary: 66, distinct_accounts_in_66: 57, nonreactivation_event_rows: 472, events_with_any_active_subscription: 443, distinct_accounts_among_events_with_active_subscription: 302, events_with_multiple_active_subscriptions: 395, opening_accounts_with_any_2024_coverage_gap: 0, conflicting_events_near_same_account_end: { within_30_days: 104 } },
  ended_subscription_class_counts: { other_subscription_active_at_termination: 66 },
  ended_subscriptions: [{ subscription_id: 'S-test', account_id: 'A-test', start_date: '2023-01-01', end_date: '2024-06-01', plan_tier: 'Pro', billing_frequency: 'monthly', seats: 2, mrr_amount_recorded: 25, arr_amount_recorded: 300, subscription_churn_flag: true, upgrade_flag: false, downgrade_flag: false, account_churn_flag: false, industry: 'Test', country: 'US', referral_source: 'organic', account_subscription_rows: 2, other_subscription_active_at_termination: true, other_active_subscription_ids_at_termination: ['S-other'], later_subscriptions_after_termination: [], successor_candidate_ids_unconfirmed: [], account_coverage_continuous_during_2024: true, account_active_2025_01_01_by_date: true, annual_account_event_rows: 1, annual_account_nonreactivation_event_rows: 1, exclusive_case_class: 'other_subscription_active_at_termination', classification_note: 'Test only' }],
  event_end_proximity_counts: { all_472_nonreactivation_events: { within_30_days: 1 }, '443_events_with_active_subscription': { within_30_days: 1 } },
  event_reasons: [
    { reason_code: 'pricing', nonreactivation_event_rows: 2, events_with_active_subscription: 1, events_with_same_account_end_within_30d: 1, share_of_conflicting_443: 1 / 443 },
    { reason_code: 'support', nonreactivation_event_rows: 2, events_with_active_subscription: 1, events_with_same_account_end_within_30d: 1, share_of_conflicting_443: 1 / 443 },
  ],
  event_segments: {}, event_account_investigation_examples: [],
  reactivation_summary: { event_rows: 55, distinct_accounts: 49, rows_with_active_subscription_on_event_date: 51, rows_after_any_same_account_subscription_end: 20, rows_with_later_same_account_subscription_start: 45, rows_after_prior_nonreactivation_event: 33, distinct_accounts_in_2024_opening_base: 14, interpretation: 'Test only' },
  reactivation_events: [],
  account_reconciliation: { cross_tab: {}, account_rows: [] }, financial_descriptives: {},
  conflicting_events: [
    { churn_event_id: 'E-test', account_id: 'A-test', churn_date: '2024-05-20', reason_code: 'pricing', feedback_text: 'Test comment', account_churn_flag: false, account_plan_tier: 'Pro', industry: 'Test', country: 'US', referral_source: 'organic', subscription_rows_for_account: 2, active_subscription_count_on_event_date: 2, active_subscription_ids_on_event_date: ['S-test', 'S-other'], nearest_same_account_end_date: '2024-06-01', nearest_end_date_difference_days: 12, event_days_after_nearest_end: -12, within_0_days_of_end: false, within_7_days_of_end: false, within_30_days_of_end: true, within_60_days_of_end: true, event_subscription_link: 'UNKNOWN: no subscription foreign key.' },
    { churn_event_id: 'E-support', account_id: 'A-support', churn_date: '2024-07-20', reason_code: 'support', feedback_text: null, account_churn_flag: false, account_plan_tier: 'Basic', industry: 'Test', country: 'US', referral_source: 'organic', subscription_rows_for_account: 1, active_subscription_count_on_event_date: 1, active_subscription_ids_on_event_date: ['S-support'], nearest_same_account_end_date: null, nearest_end_date_difference_days: null, event_days_after_nearest_end: null, within_0_days_of_end: false, within_7_days_of_end: false, within_30_days_of_end: false, within_60_days_of_end: false, event_subscription_link: 'UNKNOWN: no subscription foreign key.' },
  ],
  limitations: ['Test fixture.'],
} as unknown as ContractChurn

const g4CustomerChurn: G4CustomerChurn = {
  primary_customer_churn: { value: null, period: '2023 and 2024', numerator: null, denominator: null, formula: 'Unique eligible customers lost during period / unique active customers at period start × 100', classification: 'C — CUSTOMER CHURN NOT IDENTIFIABLE', reason: 'Event statuses conflict with date-active subscriptions.', conditional_date_result_2023: null, conditional_date_result_2024: 0, conditional_numerator_2024: 0, conditional_denominator_2024: 191 },
  annual: { '2023': { opening_active_accounts: 0, opening_accounts_with_any_date_coverage_gap: 0, opening_accounts_without_coverage_at_close: 0, conditional_gross_date_churn_rate: null, conditional_subscription_churn_rate: null, opening_accounts_with_nonreactivation_event: 0, nonreactivation_event_rows_with_active_subscription: 47, opening_accounts_with_account_churn_flag: 0 }, '2024': { opening_active_accounts: 191, opening_accounts_with_any_date_coverage_gap: 0, opening_accounts_without_coverage_at_close: 0, conditional_gross_date_churn_rate: 0, conditional_subscription_churn_rate: 0.1, opening_accounts_with_nonreactivation_event: 103, nonreactivation_event_rows_with_active_subscription: 443, opening_accounts_with_account_churn_flag: 49 } },
  monthly: [], quarterly: [],
  snapshots: { '2023-01-01': { unique_active_accounts: 0, active_subscription_rows: 0 }, '2024-01-01': { unique_active_accounts: 191, active_subscription_rows: 655 }, '2025-01-01': { unique_active_accounts: 500, active_subscription_rows: 4514 } },
  cohorts: { status: 'DIAGNOSTIC_ONLY_NOT_VALIDATED_RETENTION', definition: 'First-subscription start month', rows: [{ cohort: '2024-01', elapsed_month: 0, initial_accounts: 1, active_by_recorded_dates: 1, conditional_retention: 1, boundary_date: '2024-02-01', evidence_classification: 'conditional' }], limitation: 'Not validated.' },
  reconciliation: { unique_account_flag_true_all_history: 110, unique_accounts_with_any_event_all_history: 352, unique_accounts_with_nonreactivation_event_all_history: 339, nonreactivation_event_rows_2024_with_active_subscription: 443, invalid_nonpositive_subscription_intervals: 13, movement_bridge: { residual: 0 } },
  segments: [{ dimension: 'industry', segment: 'Test', accounts: 40, account_flag_true: 8, account_flag_prevalence: 0.2, accounts_with_nonreactivation_event_all_history: 10, all_history_event_prevalence: 0.25, accounts_with_2024_nonreactivation_event: 6, '2024_event_prevalence': 0.15, label_note: 'Descriptive only' }],
  account_review_candidates: [{ account_id: 'acct-test', industry: 'Test', country: 'US', referral_source: 'partner', plan_tier: 'Pro', account_churn_flag: true, nonreactivation_event_rows_all_history: 3, nonreactivation_event_in_2024: true, opening_2024_date_active: true, classification: 'RECONCILIATION_PRIORITY_NOT_PREDICTIVE_RISK' }],
  methodology: ['Test only'],
}

const originalFetch = globalThis.fetch
let root: Root
let container: HTMLDivElement

function jsonResponse(body: unknown, ok = true, detail = 'Request failed'): Response {
  return {
    ok,
    status: ok ? 200 : 503,
    json: async () => (ok ? body : { detail }),
  } as Response
}

function setFetch(handler?: (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>) {
  globalThis.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    if (handler) return handler(input, init)
    const path = String(input)
    if (path === '/api/analysis') return jsonResponse(analysis)
    if (path.startsWith('/api/accounts/reconciliation')) return jsonResponse(reconciliation)
    if (path === '/api/business-investigation') return jsonResponse(business)
    if (path === '/api/historical-churn') return jsonResponse(historical)
    if (path === '/api/contract-churn') return jsonResponse(contractChurn)
    if (path === '/api/g4-customer-churn') return jsonResponse(g4CustomerChurn)
    if (path === '/api/daily-portfolio-churn') return jsonResponse(dailyPortfolio)
    if (path === '/api/scenarios/retention') return jsonResponse(scenario)
    throw new Error(`Unexpected request: ${path}`)
  })
}

async function renderApp() {
  await act(async () => {
    root.render(<App />)
    await new Promise((resolve) => setTimeout(resolve, 0))
  })
}

async function click(element: Element) {
  await act(async () => {
    element.dispatchEvent(new MouseEvent('click', { bubbles: true }))
  })
}

async function changeSelect(element: HTMLSelectElement, value: string) {
  await act(async () => {
    Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set?.call(element, value)
    element.dispatchEvent(new Event('change', { bubbles: true }))
  })
}

beforeEach(() => {
  Object.defineProperty(globalThis, 'IS_REACT_ACT_ENVIRONMENT', { configurable: true, value: true })
  vi.spyOn(window, 'scrollTo').mockImplementation(() => {})
  container = document.createElement('div')
  document.body.append(container)
  const chartStyle = document.createElement('style')
  chartStyle.textContent = '.chart-wrap{width:800px;height:320px}'
  document.head.append(chartStyle)
  root = createRoot(container)
  setFetch()
  if (!globalThis.ResizeObserver) {
    globalThis.ResizeObserver = class {
      private callback: ResizeObserverCallback
      constructor(callback: ResizeObserverCallback) { this.callback = callback }
      observe(target: Element) {
        this.callback([{
          target,
          contentRect: { width: 800, height: 320, x: 0, y: 0, top: 0, left: 0, right: 800, bottom: 320, toJSON: () => ({}) },
        } as ResizeObserverEntry], this)
      }
      unobserve() {}
      disconnect() {}
    }
  }
})

afterEach(async () => {
  await act(async () => root.unmount())
  container.remove()
  document.head.querySelectorAll('style').forEach((style) => style.remove())
  globalThis.fetch = originalFetch
  vi.restoreAllMocks()
})

describe('executive investigation UI', () => {
  it('announces its loading state while the API is pending', async () => {
    setFetch(() => new Promise<Response>(() => {}))
    await act(async () => root.render(<App />))
    expect(container.querySelector('[role="status"]')?.textContent).toContain('Loading the five source tables')
  })

  it('selects a deterministic key moment and opens that month in the laboratory', async () => {
    await renderApp()
    const tabs = [...container.querySelectorAll('.chapter-tab')]
    await click(tabs[1])
    const moment = container.querySelector('[data-testid="key-moments"] .key-moment-card')
    expect(moment).toBeTruthy()
    await click(moment!)
    expect(container.querySelector('[data-testid="selected-key-moment"]')?.textContent).toContain('11 gross date-derived account × plan-tier coverage loss events')
    expect(container.querySelector('[data-testid="selected-key-moment"]')?.textContent).toContain('opening cohort losses: 5')
    const openLab = [...container.querySelectorAll('button')].find((button) => button.textContent?.includes('Open 2024-12 in the Monthly Business Lab'))
    expect(openLab).toBeTruthy()
    await click(openLab!)
    expect(container.querySelector('[data-testid="monthly-business-lab"]')).toBeTruthy()
    expect((container.querySelector('[aria-label="Select observed month"]') as HTMLSelectElement).value).toBe('2024-12')
  })

  it('renders API support values and navigates across all four chapters', async () => {
    await renderApp()
    expect(container.textContent).toContain('More churn events.')
    expect(container.textContent).toContain('No verified increase in customer churn.')
    expect(container.textContent).toContain('Recorded churn events increased from 73 to 527, but the supplied records do not establish a comparable commercial customer-churn rate.')
    expect(container.querySelector('[data-testid="business-decision"]')?.textContent).toContain('Reconcile customer status, subscription dates and event records before treating event growth as worsening retention.')
    expect(container.querySelector('[data-testid="business-decision"]')?.textContent).toContain('Then validate segments and test targeted interventions.')
    expect(container.textContent).toContain('2024 plan-coverage loss · any time')
    expect(container.textContent).toContain('1.87%')
    expect(container.textContent).toContain('0.80%')
    expect(container.textContent).toContain('0.00%')
    expect(container.textContent).toContain('The supplied records do not establish a comparable commercial customer-churn rate.')
    expect(container.textContent).not.toContain('UNKNOWN')
    expect(container.textContent).toContain('0 / 190')
    expect(container.textContent).toContain('NO CAUSE ESTABLISHED')

    const tabs = [...container.querySelectorAll('.chapter-tab')]
    expect(tabs).toHaveLength(4)
    await click(tabs[1])
    expect(container.querySelector('[data-testid="monthly-churn-rate-chart"]')?.getAttribute('data-month-points')).toBe('24')
    expect(container.querySelector('[data-testid="monthly-churn-movement-chart"]')?.getAttribute('data-month-points')).toBe('24')
    expect(container.textContent).toContain('CONDITIONAL DATE RECONSTRUCTION')
    const monthlyRows = container.querySelectorAll('[data-testid="monthly-churn-table"] tbody tr')
    expect(monthlyRows).toHaveLength(24)
    expect(monthlyRows[0]?.textContent).toContain('2023-01')
    expect(monthlyRows[0]?.textContent).toContain('0/0 · UNDEFINED')
    expect(monthlyRows[0]?.querySelector('[title^="Customer gross"]')?.getAttribute('title')).toContain('0 / 0 × 100')
    expect(monthlyRows[1]?.textContent).toContain('1/25 · 4.00%')
    expect(monthlyRows[1]?.textContent).toContain('1/32 · 3.13%')
    expect(monthlyRows[1]?.querySelector('[title^="Customer gross"]')?.getAttribute('title')).toContain('1 / 25 × 100')
    expect(container.textContent).toContain('G4-STYLE CUSTOMER COHORT DIAGNOSTIC')
    expect(container.textContent).toContain('EVERY DAY, CUSTOMERS CHANGE THEIR PORTFOLIO')
    const monthlySegmentDetails = [...container.querySelectorAll('details summary')].find((node) => node.textContent?.includes('Compare monthly customer and plan movements by segment'))
    expect(monthlySegmentDetails).toBeTruthy()
    await click(monthlySegmentDetails!)
    expect(container.textContent).toContain('Monthly industry customer and plan-proxy flows')
    expect(container.textContent).toContain('Test industry')
    expect(container.textContent).toContain('PLAN-LEVEL PROXY')
    expect(container.textContent).toContain('3 of 600 event rows share an account and civil date')
    expect(container.textContent).toContain('acct-test')
    const returnDetails = [...container.querySelectorAll('details summary')].find((node) => node.textContent?.includes('Review complete coverage loss and return timelines'))
    expect(returnDetails).toBeTruthy()
    await click(returnDetails!)
    expect(container.textContent).toContain('acct-return')
    expect(container.textContent).toContain('2024-04-01')
    expect(container.textContent).toContain('2024-04-04')
    expect(container.textContent).toContain('QUESTION 2 · SEGMENTS AND ACCOUNT REVIEW')
    expect(container.textContent).toContain('The date rule yields a conditional 2024 rate')
    expect(container.textContent).toContain('Contract rows ended; account coverage continued')
    expect(container.textContent).toContain('66 / 655')
    expect(container.textContent).toContain('443 / 472')
    expect(container.textContent).toContain('Reactivation markers also do not reconcile automatically: 55 rows across 49 accounts')
    const contractDetails = [...container.querySelectorAll('details summary')].find((node) => node.textContent?.includes('Inspect 66 opening subscriptions'))
    expect(contractDetails).toBeTruthy()
    await click(contractDetails!)
    expect(container.textContent).toContain('S-test')
    expect(container.textContent).toContain('E-test')
    const eventFilter = [...container.querySelectorAll('label.select-label')].find((label) => label.textContent?.includes('Filter conflicting events by recorded reason'))?.querySelector('select')
    expect(eventFilter).toBeTruthy()
    await changeSelect(eventFilter!, 'support')
    expect(container.textContent).toContain('E-support')
    expect(container.textContent).not.toContain('E-test')
    expect(container.textContent).toContain('Four months show a full-account interval gap')
    expect(container.textContent).toContain('2024-09')
    expect(container.textContent).toContain('3.980 / 5 · n=1')
    expect(container.textContent).toContain('ACQUISITION & ICP DIAGNOSTIC')
    expect(container.textContent).toContain('ENGAGEMENT BY ALTERNATIVE LABEL')
    expect(container.textContent).toContain('does not settle retention')
    const portfolioSelect = [...container.querySelectorAll('label.select-label')].find((label) => label.textContent?.includes('Aggregate daily ledger'))?.querySelector('select')
    expect(portfolioSelect).toBeTruthy()
    await changeSelect(portfolioSelect!, 'ANNUAL')
    expect(container.textContent).toContain('ANNUAL MOVEMENTS')
    expect(container.textContent).toContain('7 / 374 · 1.87%')
    expect(container.textContent).toContain('3 / 374 · 0.80%')
    const selects = [...container.querySelectorAll('select')]
    await changeSelect(selects[3], 'any_event')
    expect(container.textContent).toContain('Any event (incl. reactivation)')
    await changeSelect(selects[4], 'subscription_start')
    expect(container.textContent).toContain('Earliest listed subscription start')
    expect(container.textContent).toContain('Missing scores')
    await click(tabs[2])
    expect(container.textContent).toContain('VERIFIED RECURRING REVENUE EXPOSURE')
    expect(container.textContent).toContain('Not established')
    expect(container.textContent).toContain('SPECIFIC ACCOUNTS TO REVIEW')
    expect(container.textContent).toContain('Test Account')
    await click(tabs[3])
    expect(container.textContent).toContain('Q1 · WHY ARE CUSTOMERS CHURNING?')
    expect(container.textContent).toContain('Q2 · WHO NEEDS ATTENTION?')
    expect(container.textContent).toContain('Q3 · WHAT SHOULD RAVENSTACK DO?')
    expect(container.textContent).toContain('Set scenario assumptions')
    expect(container.textContent).toContain('Evidence priority, not probability')
    expect(container.textContent).toContain('Test action')
  })

  it('shows API errors without substituting sample business metrics', async () => {
    setFetch((input) => String(input) === '/api/analysis'
      ? Promise.resolve(jsonResponse(null, false, 'API unavailable'))
      : Promise.resolve(jsonResponse(reconciliation)))
    await renderApp()
    expect(container.querySelector('[role="alert"]')?.textContent).toContain('API unavailable')
    expect(container.textContent).toContain('does not replace missing source evidence with sample metrics')
  })

  it('submits production scenario inputs and displays user-supplied units', async () => {
    const requests: RequestInit[] = []
    setFetch((input, init) => {
      if (String(input) === '/api/scenarios/retention') {
        requests.push(init ?? {})
        return Promise.resolve(jsonResponse(scenario))
      }
      if (String(input) === '/api/analysis') return Promise.resolve(jsonResponse(analysis))
      if (String(input).startsWith('/api/accounts/reconciliation')) return Promise.resolve(jsonResponse(reconciliation))
      if (String(input) === '/api/business-investigation') return Promise.resolve(jsonResponse(business))
      if (String(input) === '/api/g4-customer-churn') return Promise.resolve(jsonResponse(g4CustomerChurn))
      if (String(input) === '/api/daily-portfolio-churn') return Promise.resolve(jsonResponse(dailyPortfolio))
      return Promise.resolve(jsonResponse(historical))
    })
    await renderApp()
    await click(container.querySelectorAll('.chapter-tab')[3])

    const budgetLabel = [...container.querySelectorAll('label')].find((label) => label.textContent?.includes('Available budget'))
    const budgetInput = budgetLabel?.querySelector('input')
    expect(budgetInput).not.toBeNull()
    const valueSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set
    await act(async () => {
      valueSetter?.call(budgetInput, '2500')
      budgetInput?.dispatchEvent(new Event('input', { bubbles: true }))
      budgetInput?.dispatchEvent(new Event('change', { bubbles: true }))
    })
    const form = container.querySelector('form')
    await act(async () => form?.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })))

    expect(requests).toHaveLength(1)
    expect(JSON.parse(String(requests[0].body))).toMatchObject({ assumed_effectiveness: 0.1, assumed_uptake_pct: 0.6, budget: 2500 })
    expect(container.textContent).toContain('2.5')
    expect(container.textContent).toContain('3,750 units')
    expect(container.textContent).not.toContain('$3,750')
  })
})
