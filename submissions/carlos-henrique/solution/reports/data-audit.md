# RavenStack data audit

## 1. Objective

Validate the five raw source tables for structural use in a future temporal event log. This report contains no churn diagnosis or business conclusion.

## 2. Audited files

| table | file | bytes | SHA-256 | encoding | delimiter |
|---|---|---|---|---|---|
| accounts | ravenstack_accounts.csv | 36649 | 348d8ba906b7776894b5236b2e7aa91a503d41670dbc9aad30c37b503c9abef5 | utf-8 | , |
| churn_events | ravenstack_churn_events.csv | 44630 | 6391c41d8291b7b4845ec9a84d3837c2ed230a33a32a854ec33d4e66dc150940 | utf-8 | , |
| feature_usage | ravenstack_feature_usage.csv | 1400898 | c081da2be8caf987d07f0f79ceb0619aba523d819529230ed6df77984fa21d4e | utf-8 | , |
| subscriptions | ravenstack_subscriptions.csv | 437566 | dcf1d93ca9a35e0dcba0ab686d255f0e9ec26512970bbf0944cf19cbef2d751a | utf-8 | , |
| support_tickets | ravenstack_support_tickets.csv | 145598 | ba0006951479771ee9f93c98789c96bc5fec892cf11f867afb28194f0b76d220 | utf-8 | , |

## 3. Methodology

Read-only loading, deterministic hashing, schema profiling, null and uniqueness checks, key tests, regex-only privacy checks, referential audits, key-only join simulations, temporal consistency checks, and explicit leakage classification.

## 4. Table overview and observed grain

| table | records | columns | physical lines | exact duplicates | observed grain | status |
|---|---|---|---|---|---|---|
| accounts | 500 | 10 | 501 | 0 | one row per account_id in this snapshot | CANDIDATE |
| subscriptions | 5000 | 14 | 5001 | 0 | one row per subscription_id in this snapshot | CANDIDATE |
| feature_usage | 25000 | 8 | 25001 | 0 | usage event row; supplied IDs and tested business composite are not unique | INCONCLUSIVE |
| support_tickets | 2000 | 9 | 2001 | 0 | one row per ticket_id in this snapshot | CANDIDATE |
| churn_events | 600 | 9 | 601 | 0 | one row per churn_event_id in this snapshot | CANDIDATE |

## 5. Real schema by table

| table | column | dtype | candidate role | key status | leakage |
|---|---|---|---|---|---|
| accounts | account_id | str | TECHNICAL_IDENTIFIER | CANDIDATE | NONE_IDENTIFIED |
| accounts | account_name | str | TEXT_OR_LABEL | — | NONE_IDENTIFIED |
| accounts | industry | str | CATEGORICAL_ATTRIBUTE | — | NONE_IDENTIFIED |
| accounts | country | str | CATEGORICAL_ATTRIBUTE | — | NONE_IDENTIFIED |
| accounts | signup_date | str | TEMPORAL_FIELD | — | TEMPORAL |
| accounts | referral_source | str | CATEGORICAL_ATTRIBUTE | — | NONE_IDENTIFIED |
| accounts | plan_tier | str | CATEGORICAL_ATTRIBUTE | — | NONE_IDENTIFIED |
| accounts | seats | int64 | NUMERIC_MEASURE | — | NONE_IDENTIFIED |
| accounts | is_trial | bool | NUMERIC_MEASURE | — | NONE_IDENTIFIED |
| accounts | churn_flag | bool | NUMERIC_MEASURE | — | EXPLICIT |
| subscriptions | subscription_id | str | TECHNICAL_IDENTIFIER | CANDIDATE | NONE_IDENTIFIED |
| subscriptions | account_id | str | TECHNICAL_IDENTIFIER | INVALID | NONE_IDENTIFIED |
| subscriptions | start_date | str | TEMPORAL_FIELD | — | TEMPORAL |
| subscriptions | end_date | str | TEMPORAL_FIELD | — | PROXY |
| subscriptions | plan_tier | str | CATEGORICAL_ATTRIBUTE | — | NONE_IDENTIFIED |
| subscriptions | seats | int64 | NUMERIC_MEASURE | — | NONE_IDENTIFIED |
| subscriptions | mrr_amount | int64 | NUMERIC_MEASURE | — | NONE_IDENTIFIED |
| subscriptions | arr_amount | int64 | NUMERIC_MEASURE | — | NONE_IDENTIFIED |
| subscriptions | is_trial | bool | NUMERIC_MEASURE | — | NONE_IDENTIFIED |
| subscriptions | upgrade_flag | bool | NUMERIC_MEASURE | — | NONE_IDENTIFIED |
| subscriptions | downgrade_flag | bool | NUMERIC_MEASURE | — | NONE_IDENTIFIED |
| subscriptions | churn_flag | bool | NUMERIC_MEASURE | — | EXPLICIT |
| subscriptions | billing_frequency | str | CATEGORICAL_ATTRIBUTE | — | NONE_IDENTIFIED |
| subscriptions | auto_renew_flag | bool | NUMERIC_MEASURE | — | NONE_IDENTIFIED |
| feature_usage | usage_id | str | TECHNICAL_IDENTIFIER | INVALID | NONE_IDENTIFIED |
| feature_usage | subscription_id | str | TECHNICAL_IDENTIFIER | INVALID | NONE_IDENTIFIED |
| feature_usage | usage_date | str | TEMPORAL_FIELD | — | TEMPORAL |
| feature_usage | feature_name | str | CATEGORICAL_ATTRIBUTE | — | NONE_IDENTIFIED |
| feature_usage | usage_count | int64 | NUMERIC_MEASURE | — | NONE_IDENTIFIED |
| feature_usage | usage_duration_secs | int64 | NUMERIC_MEASURE | — | NONE_IDENTIFIED |
| feature_usage | error_count | int64 | NUMERIC_MEASURE | — | NONE_IDENTIFIED |
| feature_usage | is_beta_feature | bool | NUMERIC_MEASURE | — | NONE_IDENTIFIED |
| support_tickets | ticket_id | str | TECHNICAL_IDENTIFIER | CANDIDATE | NONE_IDENTIFIED |
| support_tickets | account_id | str | TECHNICAL_IDENTIFIER | INVALID | NONE_IDENTIFIED |
| support_tickets | submitted_at | str | TEMPORAL_FIELD | — | TEMPORAL |
| support_tickets | closed_at | str | TEMPORAL_FIELD | — | TEMPORAL |
| support_tickets | resolution_time_hours | float64 | NUMERIC_MEASURE | — | TEMPORAL |
| support_tickets | priority | str | CATEGORICAL_ATTRIBUTE | — | NONE_IDENTIFIED |
| support_tickets | first_response_time_minutes | int64 | NUMERIC_MEASURE | — | TEMPORAL |
| support_tickets | satisfaction_score | float64 | NUMERIC_MEASURE | — | TEMPORAL |
| support_tickets | escalation_flag | bool | NUMERIC_MEASURE | — | TEMPORAL |
| churn_events | churn_event_id | str | TECHNICAL_IDENTIFIER | CANDIDATE | EXPLICIT |
| churn_events | account_id | str | TECHNICAL_IDENTIFIER | INVALID | NONE_IDENTIFIED |
| churn_events | churn_date | str | TEMPORAL_FIELD | — | EXPLICIT |
| churn_events | reason_code | str | CATEGORICAL_ATTRIBUTE | — | EXPLICIT |
| churn_events | refund_amount_usd | float64 | NUMERIC_MEASURE | — | EXPLICIT |
| churn_events | preceding_upgrade_flag | bool | NUMERIC_MEASURE | — | EXPLICIT |
| churn_events | preceding_downgrade_flag | bool | NUMERIC_MEASURE | — | EXPLICIT |
| churn_events | is_reactivation | bool | NUMERIC_MEASURE | — | EXPLICIT |
| churn_events | feedback_text | str | TEXT_OR_LABEL | — | EXPLICIT |

## 6. Granularity

Granularity is inferred from tested uniqueness and completeness in this snapshot. Technical identifiers marked `CANDIDATE` still require source-governance evidence for long-term stability.

## 7. Missingness

| table | column | missing | missing rate |
|---|---|---|---|
| subscriptions | end_date | 4514 | 0.9028 |
| support_tickets | satisfaction_score | 825 | 0.4125 |
| churn_events | feedback_text | 148 | 0.246667 |

## 8. Duplicates

Exact full-row duplicate counts are shown in the overview. Identifier and composite-key duplication is shown with affected key evidence below.

## 9. Candidate keys

| table | candidate | null rows | duplicate excess rows | status |
|---|---|---|---|---|
| accounts | account_id | 0 | 0 | CANDIDATE |
| subscriptions | subscription_id | 0 | 0 | CANDIDATE |
| subscriptions | account_id | 0 | 4500 | INVALID |
| feature_usage | usage_id | 0 | 21 | INVALID |
| feature_usage | subscription_id | 0 | 20033 | INVALID |
| feature_usage | subscription_id+usage_date+feature_name | 0 | 3 | INVALID |
| support_tickets | ticket_id | 0 | 0 | CANDIDATE |
| support_tickets | account_id | 0 | 1508 | INVALID |
| churn_events | churn_event_id | 0 | 0 | CANDIDATE |
| churn_events | account_id | 0 | 248 | INVALID |

## 10. Structural consistency

| check | count | evaluated | rate | severity | status | interpretation |
|---|---|---|---|---|---|---|
| account_churn_flag_false_with_churn_event | 277 | 500 | 0.554 | HIGH | WARNING | The account-level snapshot flag conflicts with the churn event table. |
| account_churn_flag_true_without_churn_event | 35 | 500 | 0.07 | HIGH | WARNING | The account-level target flag lacks a corresponding churn event. |
| subscription_churn_true_without_end_date | 0 | 5000 | 0 | HIGH | PASS | A churned subscription is expected to have a termination date. |
| subscription_churn_false_with_end_date | 0 | 5000 | 0 | HIGH | PASS | An ended subscription conflicts with a false churn flag in this schema. |
| arr_not_equal_to_mrr_times_twelve | 0 | 5000 | 0 | MEDIUM | PASS | ARR and MRR require a documented reconciliation rule before financial use. |
| ticket_resolution_hours_mismatch | 0 | 2000 | 0 | MEDIUM | PASS | Stored resolution duration should reconcile with submitted and closed timestamps. |
| satisfaction_score_outside_1_to_5 | 0 | 1175 | 0 | HIGH | PASS | Non-null satisfaction scores must remain in the documented 1-to-5 domain. |
| usage_id_duplicate_excess_rows | 21 | 25000 | 0.00084 | HIGH | WARNING | The supplied usage identifier is not a unique event key. |
| usage_business_composite_duplicate_excess_rows | 3 | 25000 | 0.00012 | HIGH | WARNING | The tested subscription-date-feature composite is also not unique. |
| negative_numeric_values | 0 | 97100 | 0 | MEDIUM | PASS | Negative values require domain-specific justification before analytical use. |

## 11. Text fields and privacy

No raw text is reproduced. Counts below are aggregate regex and length statistics only.

| table | column | missing rate | avg length | max length | email | phone | URL |
|---|---|---|---|---|---|---|---|
| accounts | account_name | 0 | 10.78 | 11 | 0 | 0 | 0 |
| churn_events | feedback_text | 0.246667 | 16.737 | 22 | 0 | 0 | 0 |

## 12. Leakage risks

| table | column | risk | reason | allowed | prohibited | decision |
|---|---|---|---|---|---|---|
| accounts | signup_date | TEMPORAL | Safe use requires an explicit as-of cutoff before the prediction time. | Audit, reconciliation, and retrospective description. | Pre-churn predictive feature without cutoff controls. | VALIDATED_WITH_WARNINGS |
| accounts | churn_flag | EXPLICIT | The field directly encodes the outcome or cancellation-time information. | Audit, reconciliation, and retrospective description. | Pre-churn predictive feature without cutoff controls. | VALIDATED_WITH_WARNINGS |
| subscriptions | start_date | TEMPORAL | Safe use requires an explicit as-of cutoff before the prediction time. | Audit, reconciliation, and retrospective description. | Pre-churn predictive feature without cutoff controls. | VALIDATED_WITH_WARNINGS |
| subscriptions | end_date | PROXY | Population or value may directly encode termination state. | Audit, reconciliation, and retrospective description. | Pre-churn predictive feature without cutoff controls. | VALIDATED_WITH_WARNINGS |
| subscriptions | churn_flag | EXPLICIT | The field directly encodes the outcome or cancellation-time information. | Audit, reconciliation, and retrospective description. | Pre-churn predictive feature without cutoff controls. | VALIDATED_WITH_WARNINGS |
| feature_usage | usage_date | TEMPORAL | Safe use requires an explicit as-of cutoff before the prediction time. | Audit, reconciliation, and retrospective description. | Pre-churn predictive feature without cutoff controls. | VALIDATED_WITH_WARNINGS |
| support_tickets | submitted_at | TEMPORAL | Safe use requires an explicit as-of cutoff before the prediction time. | Audit, reconciliation, and retrospective description. | Pre-churn predictive feature without cutoff controls. | VALIDATED_WITH_WARNINGS |
| support_tickets | closed_at | TEMPORAL | Safe use requires an explicit as-of cutoff before the prediction time. | Audit, reconciliation, and retrospective description. | Pre-churn predictive feature without cutoff controls. | VALIDATED_WITH_WARNINGS |
| support_tickets | resolution_time_hours | TEMPORAL | Safe use requires an explicit as-of cutoff before the prediction time. | Audit, reconciliation, and retrospective description. | Pre-churn predictive feature without cutoff controls. | VALIDATED_WITH_WARNINGS |
| support_tickets | first_response_time_minutes | TEMPORAL | Safe use requires an explicit as-of cutoff before the prediction time. | Audit, reconciliation, and retrospective description. | Pre-churn predictive feature without cutoff controls. | VALIDATED_WITH_WARNINGS |
| support_tickets | satisfaction_score | TEMPORAL | Safe use requires an explicit as-of cutoff before the prediction time. | Audit, reconciliation, and retrospective description. | Pre-churn predictive feature without cutoff controls. | VALIDATED_WITH_WARNINGS |
| support_tickets | escalation_flag | TEMPORAL | Safe use requires an explicit as-of cutoff before the prediction time. | Audit, reconciliation, and retrospective description. | Pre-churn predictive feature without cutoff controls. | VALIDATED_WITH_WARNINGS |
| churn_events | churn_event_id | EXPLICIT | The field belongs to the outcome event and is unavailable before churn. | Audit, reconciliation, and retrospective description. | Pre-churn predictive feature without cutoff controls. | VALIDATED_WITH_WARNINGS |
| churn_events | churn_date | EXPLICIT | The field belongs to the outcome event and is unavailable before churn. | Audit, reconciliation, and retrospective description. | Pre-churn predictive feature without cutoff controls. | VALIDATED_WITH_WARNINGS |
| churn_events | reason_code | EXPLICIT | The field belongs to the outcome event and is unavailable before churn. | Audit, reconciliation, and retrospective description. | Pre-churn predictive feature without cutoff controls. | VALIDATED_WITH_WARNINGS |
| churn_events | refund_amount_usd | EXPLICIT | The field belongs to the outcome event and is unavailable before churn. | Audit, reconciliation, and retrospective description. | Pre-churn predictive feature without cutoff controls. | VALIDATED_WITH_WARNINGS |
| churn_events | preceding_upgrade_flag | EXPLICIT | The field belongs to the outcome event and is unavailable before churn. | Audit, reconciliation, and retrospective description. | Pre-churn predictive feature without cutoff controls. | VALIDATED_WITH_WARNINGS |
| churn_events | preceding_downgrade_flag | EXPLICIT | The field belongs to the outcome event and is unavailable before churn. | Audit, reconciliation, and retrospective description. | Pre-churn predictive feature without cutoff controls. | VALIDATED_WITH_WARNINGS |
| churn_events | is_reactivation | EXPLICIT | The field belongs to the outcome event and is unavailable before churn. | Audit, reconciliation, and retrospective description. | Pre-churn predictive feature without cutoff controls. | VALIDATED_WITH_WARNINGS |
| churn_events | feedback_text | EXPLICIT | The field belongs to the outcome event and is unavailable before churn. | Audit, reconciliation, and retrospective description. | Pre-churn predictive feature without cutoff controls. | VALIDATED_WITH_WARNINGS |

## 13. Limitations

- A single snapshot validates observed completeness and uniqueness, not cross-snapshot key stability.
- Pandas dtypes are inferred load metadata, not an imposed canonical schema.
- No causal, churn-driver, risk-segmentation, revenue, or predictive analysis was performed.
- Text was assessed only through aggregate regex and length statistics; raw text is excluded.

## 14. Pending decisions

- Define the canonical event identity for feature usage because the preferred usage ID must be evaluated against duplicates.
- Define as-of cutoffs and lifecycle rules for multiple subscriptions, churn recurrence, and reactivation.
- Keep outcome and post-outcome fields outside pre-churn feature sets.

## 15. Gate for Phase 2

**PASS_WITH_WARNINGS**

- Non-unique preferred identifiers: feature_usage.usage_id.
- Confirmed temporal exceptions require explicit Phase 2 treatment.
- One-to-many relations require event-source separation or aggregation.
- High-severity cross-source consistency conflicts require explicit precedence rules.

The audit does not start or materialize the event log.
