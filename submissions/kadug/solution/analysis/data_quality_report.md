# RavenStack Data Quality Report

Generated: 2026-06-28
Dataset source: Kaggle `rivalytics/saas-subscription-and-churn-analytics-dataset`
Local raw files: `data/raw/ravenstack/`

## Executive Summary

The five CSVs are present, readable, and match the expected row volumes:

| File | Rows | Status |
|---|---:|---|
| `ravenstack_accounts.csv` | 500 | OK |
| `ravenstack_subscriptions.csv` | 5,000 | OK |
| `ravenstack_feature_usage.csv` | 25,000 | Usable with caveats |
| `ravenstack_support_tickets.csv` | 2,000 | OK |
| `ravenstack_churn_events.csv` | 600 | OK |

All declared foreign-key joins are referentially complete: there are no orphan `account_id` values and no orphan `subscription_id` values.

There are two important caveats before analysis:

1. `ravenstack_feature_usage.usage_id` is not a reliable primary key. It has 21 duplicate rows by `usage_id` across different subscriptions/events.
2. Feature usage dates are not consistently inside the subscription lifecycle. There are 19,142 usage rows before the subscription `start_date` and 290 after `end_date`. Canonical usage metrics must carry a validity flag and default to in-window usage only.

`accounts.churn_flag` also does not align one-to-one with `churn_events`: 110 accounts have `accounts.churn_flag = True`, while 352 accounts have at least one churn event. Treat these as different concepts: account-level current/source flag vs. event-level historical churn.

## Real Schema

### `ravenstack_accounts.csv`

Grain: one row per account.
Primary key candidate: `account_id`.

| Column | Type | Nulls | Notes |
|---|---|---:|---|
| `account_id` | string | 0 | 500 distinct, unique |
| `account_name` | string | 0 | 500 distinct |
| `industry` | categorical | 0 | 5 values: DevTools, FinTech, Cybersecurity, HealthTech, EdTech |
| `country` | categorical | 0 | 7 values, US is largest |
| `signup_date` | date | 0 | 2023-01-02 to 2024-12-31 |
| `referral_source` | categorical | 0 | organic, other, ads, event, partner |
| `plan_tier` | categorical | 0 | Basic, Pro, Enterprise |
| `seats` | integer | 0 | min 1, max 163 |
| `is_trial` | boolean | 0 | True/False |
| `churn_flag` | boolean | 0 | True/False |

### `ravenstack_subscriptions.csv`

Grain: one row per subscription lifecycle.
Primary key: `subscription_id`.
Foreign key: `account_id -> accounts.account_id`.

| Column | Type | Nulls | Notes |
|---|---|---:|---|
| `subscription_id` | string | 0 | 5,000 distinct, unique |
| `account_id` | string | 0 | 500 distinct, all matched to accounts |
| `start_date` | date | 0 | 2023-01-09 to 2024-12-31 |
| `end_date` | date | 4,514 | Nullable for active subscriptions |
| `plan_tier` | categorical | 0 | Basic, Pro, Enterprise |
| `seats` | integer | 0 | min 1, max 189 |
| `mrr_amount` | integer/currency | 0 | min 0, max 33,830 |
| `arr_amount` | integer/currency | 0 | min 0, max 405,960 |
| `is_trial` | boolean | 0 | True/False |
| `upgrade_flag` | boolean | 0 | True/False |
| `downgrade_flag` | boolean | 0 | True/False |
| `churn_flag` | boolean | 0 | Matches `end_date` presence |
| `billing_frequency` | categorical | 0 | monthly, annual |
| `auto_renew_flag` | boolean | 0 | True/False |

### `ravenstack_feature_usage.csv`

Grain: one feature usage event row.
Primary key candidate in README: `usage_id`, but actual data violates uniqueness.
Foreign key: `subscription_id -> subscriptions.subscription_id`.

| Column | Type | Nulls | Notes |
|---|---|---:|---|
| `usage_id` | string | 0 | 24,979 distinct across 25,000 rows; 21 duplicate rows |
| `subscription_id` | string | 0 | 4,967 distinct, all matched to subscriptions |
| `usage_date` | date | 0 | 2023-01-01 to 2024-12-31 |
| `feature_name` | categorical | 0 | 40 features |
| `usage_count` | integer | 0 | min 0, max 26 |
| `usage_duration_secs` | integer | 0 | min 0, max 12,696 |
| `error_count` | integer | 0 | min 0, max 8 |
| `is_beta_feature` | boolean | 0 | True/False |

Recommended ingestion key: generate a surrogate row id, for example `feature_usage_row_id`, and preserve `usage_id` as a source event id. If a composite natural key is required, use at least `usage_id`, `subscription_id`, `usage_date`, and `feature_name`.

### `ravenstack_support_tickets.csv`

Grain: one support ticket.
Primary key: `ticket_id`.
Foreign key: `account_id -> accounts.account_id`.

| Column | Type | Nulls | Notes |
|---|---|---:|---|
| `ticket_id` | string | 0 | 2,000 distinct, unique |
| `account_id` | string | 0 | 492 distinct, all matched to accounts |
| `submitted_at` | date | 0 | Actual file contains date-only values |
| `closed_at` | datetime | 0 | 2023-01-03 03:00:00 to 2024-12-31 19:00:00 |
| `resolution_time_hours` | decimal | 0 | min 1, max 72; matches `closed_at - submitted_at` |
| `priority` | categorical | 0 | low, medium, high, urgent |
| `first_response_time_minutes` | integer | 0 | min 1, max 180 |
| `satisfaction_score` | decimal | 825 | 41.25% missing; valid values are 3, 4, 5 |
| `escalation_flag` | boolean | 0 | True/False |

### `ravenstack_churn_events.csv`

Grain: one churn event.
Primary key: `churn_event_id`.
Foreign key: `account_id -> accounts.account_id`.

| Column | Type | Nulls | Notes |
|---|---|---:|---|
| `churn_event_id` | string | 0 | 600 distinct, unique |
| `account_id` | string | 0 | 352 distinct, all matched to accounts |
| `churn_date` | date | 0 | 2023-01-25 to 2024-12-31 |
| `reason_code` | categorical | 0 | features, budget, support, unknown, competitor, pricing |
| `refund_amount_usd` | decimal/currency | 0 | min 0, max 392.92 |
| `preceding_upgrade_flag` | boolean | 0 | True/False |
| `preceding_downgrade_flag` | boolean | 0 | True/False |
| `is_reactivation` | boolean | 0 | True/False |
| `feedback_text` | string | 148 | 24.67% missing |

## Join Validation

Canonical join graph:

```text
accounts.account_id
  -> subscriptions.account_id
       -> feature_usage.subscription_id
  -> support_tickets.account_id
  -> churn_events.account_id
```

| Join | Checked rows | Orphan rows | Result |
|---|---:|---:|---|
| `subscriptions.account_id -> accounts.account_id` | 5,000 | 0 | OK |
| `support_tickets.account_id -> accounts.account_id` | 2,000 | 0 | OK |
| `churn_events.account_id -> accounts.account_id` | 600 | 0 | OK |
| `feature_usage.subscription_id -> subscriptions.subscription_id` | 25,000 | 0 | OK |

Cardinality:

| Relationship | Min | Median | P90 | Max | Zero-count parents |
|---|---:|---:|---:|---:|---:|
| Subscriptions per account | 2 | 10 | 15 | 19 | 0 accounts |
| Support tickets per account | 0 | 4 | 7 | 11 | 8 accounts |
| Churn events per account | 0 | 1 | 3 | 5 | 148 accounts |
| Usage events per subscription | 0 | 5 | 8 | 16 | 33 subscriptions |

Rules:

- Join `feature_usage` to accounts only through `subscriptions`.
- Use left joins from `accounts` for account-level exports so accounts without tickets or churn events are retained.
- Aggregate many-side tables before joining into account-level exports to avoid multiplying rows.

## Quality Findings

### Passes

- All five expected CSVs are present.
- Row counts match the dataset README.
- Declared FK relationships have zero orphan rows.
- Primary keys are unique for accounts, subscriptions, support tickets, and churn events.
- Boolean fields contain only `True`/`False`.
- Numeric fields checked have no negative values.
- Subscription temporal checks pass:
  - `start_date` is never before account `signup_date`.
  - `end_date` is never before `start_date`.
  - `subscriptions.churn_flag` matches `end_date` presence.
- Support temporal checks pass:
  - `closed_at` is never before `submitted_at`.
  - `resolution_time_hours` matches the date difference.
- Churn dates are never before account signup dates.

### Caveats

| Severity | Finding | Evidence | Required handling |
|---|---|---|---|
| High | `feature_usage.usage_id` is not unique | 21 duplicate rows by `usage_id` | Do not use `usage_id` as the sole PK; generate a surrogate row id |
| High | Usage dates often fall outside subscription windows | 19,142 before `start_date`, 290 after `end_date` | Add `usage_in_subscription_window_flag`; default derived usage metrics to valid rows |
| Medium | `accounts.churn_flag` conflicts with event history | 110 accounts flagged true, 352 accounts have churn events, 277 event accounts have account flag false | Preserve both labels and document which one is used per analysis |
| Medium | `support_tickets.satisfaction_score` has missing values | 825 nulls, 41.25% | Track response rate; do not treat missing satisfaction as neutral or zero |
| Low | `churn_events.feedback_text` has missing values | 148 nulls, 24.67% | Use text fields as supporting evidence only |
| Low | `support_tickets.submitted_at` is date-only | README describes datetime, file is date-only | Use midnight as implied time for duration validation |

Recommended clean-layer additions:

- `feature_usage_row_id`: generated stable row id at ingestion time.
- `usage_in_subscription_window_flag`: `usage_date >= start_date and (end_date is null or usage_date <= end_date)`.
- `has_churn_event`: derived from `churn_events`.
- `account_churn_flag`: original `accounts.churn_flag`.
- `churn_label_type`: explicit label source, for example `current_account_flag`, `historical_event`, or `future_window_event`.
- `satisfaction_response_flag`: `satisfaction_score is not null`.
- `data_quality_flags`: pipe-delimited or JSON array for row/account-level caveats.

## Canonical Exports

Build order:

1. `account_health`
2. `risk_segments`
3. `priority_accounts`
4. `action_backlog`
5. `executive_findings`

Use `2024-12-31` as the dataset reference date for recency windows unless a downstream analysis chooses a different reference date. This is the max observed date in the raw files.

### `account_health`

Purpose: one account-level health table for churn diagnostics, CS triage, and revenue-at-risk analysis.

Grain: one row per `account_id`.
Primary key: `account_id`.
Sources: all five CSVs.

Required columns:

| Column group | Columns |
|---|---|
| Account identity | `account_id`, `account_name`, `industry`, `country`, `signup_date`, `referral_source`, `initial_plan_tier`, `account_seats`, `account_is_trial`, `account_churn_flag` |
| Subscription health | `subscription_count`, `active_subscription_count`, `churned_subscription_count`, `latest_subscription_id`, `latest_plan_tier`, `latest_subscription_start_date`, `latest_subscription_end_date`, `current_mrr`, `current_arr`, `total_mrr_booked`, `total_arr_booked`, `any_upgrade_flag`, `any_downgrade_flag`, `active_auto_renew_flag` |
| Usage health | `raw_usage_event_count`, `valid_usage_event_count`, `invalid_usage_event_count`, `valid_usage_share`, `distinct_features_used_valid`, `total_usage_count_valid`, `usage_duration_secs_valid`, `error_count_valid`, `error_rate_per_100_valid_events`, `beta_usage_event_share_valid` |
| Support health | `support_ticket_count`, `high_urgent_ticket_count`, `escalated_ticket_count`, `avg_first_response_minutes`, `avg_resolution_hours`, `avg_satisfaction_score`, `satisfaction_response_rate` |
| Churn history | `has_churn_event`, `churn_event_count`, `latest_churn_date`, `latest_reason_code`, `refund_total_usd`, `reactivation_event_count` |
| Derived fields | `mrr_at_risk`, `account_health_score`, `risk_segment`, `primary_risk_driver`, `data_quality_flags` |

Derivation rules:

- Start from `accounts`.
- Aggregate `subscriptions` by `account_id` before joining.
- Aggregate `feature_usage` by `subscription_id`, then roll up to `account_id`.
- Usage metrics with suffix `_valid` must use only rows where `usage_in_subscription_window_flag = true`.
- Preserve raw usage counts separately so downstream users can inspect data quality impact.
- `current_mrr` and `current_arr` should include subscriptions where `end_date` is null.
- `mrr_at_risk` should default to `current_mrr`, not historical MRR.
- `risk_segment` must be deterministic and reproducible from transparent score bands.

Initial score bands:

| Segment | Score |
|---|---|
| Critical | `>= 80` |
| High | `60-79` |
| Medium | `35-59` |
| Low | `< 35` |

Suggested score components:

| Component | Max points | Examples |
|---|---:|---|
| Churn/reactivation history | 30 | Recent churn event, multiple events, reactivation |
| Subscription/commercial risk | 20 | Downgrade, inactive auto-renew, active trial, ended subscriptions |
| Support risk | 20 | Escalations, high/urgent tickets, low or missing satisfaction response rate |
| Product usage risk | 15 | Low valid usage share, elevated error rate, narrow feature adoption |
| Revenue exposure | 15 | High `current_mrr` or high active ARR concentration |

### `risk_segments`

Purpose: executive and CS segmentation view aggregated from `account_health`.

Grain: one row per `risk_segment`. Optional extension: one row per `risk_segment + primary_risk_driver`.

Primary key: `risk_segment` or composite `risk_segment, primary_risk_driver`.

Required columns:

| Column group | Columns |
|---|---|
| Segment identity | `risk_segment`, `primary_risk_driver` when using driver-level grain |
| Volume | `account_count`, `active_account_count`, `churned_account_flag_count`, `has_churn_event_count` |
| Revenue | `current_mrr`, `current_arr`, `mrr_at_risk`, `avg_mrr_at_risk` |
| Churn indicators | `event_based_churn_rate`, `account_flag_churn_rate`, `avg_churn_event_count`, `top_churn_reason` |
| Experience indicators | `avg_satisfaction_score`, `satisfaction_response_rate`, `high_urgent_ticket_rate`, `escalation_rate` |
| Product indicators | `avg_valid_usage_share`, `avg_error_rate_per_100_valid_events`, `avg_distinct_features_used_valid` |
| Context | `top_industry`, `top_plan_tier`, `top_country`, `recommended_playbook` |

Derivation rules:

- Source only from `account_health`.
- Report both event-based churn and account-flag churn because the raw labels differ.
- Do not average raw usage rows that failed subscription-window validation.

### `priority_accounts`

Purpose: ranked account list for action by CS, Product, Pricing, or Leadership.

Grain: one row per prioritized account.

Primary key: `priority_rank`; retain `account_id` as the business key.

Required columns:

| Column group | Columns |
|---|---|
| Ranking | `priority_rank`, `account_id`, `account_name`, `risk_segment`, `account_health_score` |
| Exposure | `current_mrr`, `current_arr`, `mrr_at_risk`, `plan_tier`, `industry`, `country` |
| Evidence | `primary_risk_driver`, `latest_reason_code`, `churn_event_count`, `high_urgent_ticket_count`, `escalated_ticket_count`, `avg_satisfaction_score`, `error_rate_per_100_valid_events`, `valid_usage_share`, `data_quality_flags` |
| Action | `next_best_action`, `action_owner`, `due_bucket`, `confidence_level` |

Inclusion rule:

- Include accounts where `risk_segment in ('Critical', 'High')`.
- Also include Medium-risk accounts when `mrr_at_risk` is above the portfolio P90.

Sort rule:

1. `account_health_score` descending
2. `mrr_at_risk` descending
3. `high_urgent_ticket_count` descending
4. `latest_churn_date` descending, nulls last

### `action_backlog`

Purpose: operational backlog derived from risk evidence.

Grain: one row per recommended action.

Primary key: `action_id`.
Foreign key: nullable `account_id` for account-scoped actions.

Required columns:

| Column group | Columns |
|---|---|
| Identity | `action_id`, `scope_type`, `account_id`, `risk_segment`, `source_export` |
| Action | `action_theme`, `recommended_action`, `owner_team`, `priority`, `due_bucket`, `status` |
| Trigger | `trigger_metric`, `trigger_value`, `evidence_summary`, `confidence_level` |
| Impact | `expected_impact_metric`, `mrr_at_risk`, `account_count_impacted`, `effort_size` |

Allowed `scope_type` values:

- `account`
- `segment`
- `product`
- `support`
- `pricing`
- `data_quality`

Allowed `owner_team` values:

- `CS`
- `Support`
- `Product`
- `Pricing`
- `RevOps`
- `Data`
- `Leadership`

Derivation rules:

- Account-scoped actions come from `priority_accounts`.
- Segment-scoped actions come from `risk_segments`.
- Data quality actions are allowed only for findings that affect analysis reliability, such as invalid usage windows or duplicate usage ids.

### `executive_findings`

Purpose: concise CEO-level findings that connect evidence, risk, and decision.

Grain: one row per finding.

Primary key: `finding_id`.

Required columns:

| Column group | Columns |
|---|---|
| Identity | `finding_id`, `finding_type`, `finding_title`, `confidence_level` |
| Metric evidence | `metric_name`, `metric_value`, `comparison_name`, `comparison_value`, `affected_accounts`, `mrr_at_risk` |
| Interpretation | `plain_language_finding`, `business_implication`, `recommended_decision` |
| Traceability | `supporting_exports`, `source_tables`, `data_quality_notes` |

Allowed `finding_type` values:

- `root_cause_candidate`
- `risk_segment`
- `revenue_exposure`
- `customer_experience`
- `product_usage`
- `data_quality`
- `recommended_action`

Rules:

- Every finding must trace to at least one canonical export.
- Any finding using feature usage must state whether it used valid-window usage only.
- Any finding using churn must state whether it used `account_churn_flag`, `has_churn_event`, or a future-window event label.

## Implementation Notes

Recommended pipeline:

1. Load raw CSVs unchanged.
2. Create a clean staging layer with typed columns and generated row ids where needed.
3. Add data-quality flags in staging, especially for feature usage temporal validity.
4. Build `account_health` from staged aggregates.
5. Build downstream exports only from `account_health`, except `executive_findings`, which may also reference `risk_segments`, `priority_accounts`, and `action_backlog`.

Minimum quality gates before analysis:

- Zero FK orphans.
- Zero unexpected nulls in required keys.
- `feature_usage_row_id` generated.
- `usage_in_subscription_window_flag` present.
- Churn label source declared.
- Canonical exports include `data_quality_flags`.
