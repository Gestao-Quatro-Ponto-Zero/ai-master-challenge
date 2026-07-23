# RavenStack temporal audit

## 1–4. Temporal columns, ranges, formats, and invalid dates

| field | format | timezone | grain | minimum | maximum | missing | invalid | future |
|---|---|---|---|---|---|---|---|---|
| accounts.signup_date | YYYY-MM-DD | NOT_DECLARED | DATE | 2023-01-02T00:00:00+00:00 | 2024-12-31T00:00:00+00:00 | 0 | 0 | 0 |
| subscriptions.start_date | YYYY-MM-DD | NOT_DECLARED | DATE | 2023-01-09T00:00:00+00:00 | 2024-12-31T00:00:00+00:00 | 0 | 0 | 0 |
| subscriptions.end_date | YYYY-MM-DD | NOT_DECLARED | DATE | 2023-04-05T00:00:00+00:00 | 2024-12-31T00:00:00+00:00 | 4514 | 0 | 0 |
| feature_usage.usage_date | YYYY-MM-DD | NOT_DECLARED | DATE | 2023-01-01T00:00:00+00:00 | 2024-12-31T00:00:00+00:00 | 0 | 0 | 0 |
| support_tickets.submitted_at | YYYY-MM-DD | NOT_DECLARED | DATE | 2023-01-02T00:00:00+00:00 | 2024-12-31T00:00:00+00:00 | 0 | 0 | 0 |
| support_tickets.closed_at | DATETIME_OR_MIXED | NOT_DECLARED | DATETIME | 2023-01-03T03:00:00+00:00 | 2024-12-31T19:00:00+00:00 | 0 | 0 | 0 |
| churn_events.churn_date | YYYY-MM-DD | NOT_DECLARED | DATE | 2023-01-25T00:00:00+00:00 | 2024-12-31T00:00:00+00:00 | 0 | 0 | 0 |

## 5. Temporal inconsistencies and occurrences

| check | count | evaluated | rate | classification | interpretation |
|---|---|---|---|---|---|
| subscription_before_account_signup | 0 | 5000 | 0 | CONFIRMED_ERROR | Subscription start must not precede account creation. |
| subscription_end_before_start | 0 | 486 | 0 | CONFIRMED_ERROR | A subscription end before its start is chronologically impossible. |
| usage_before_subscription_start | 19142 | 25000 | 0.76568 | CONFIRMED_ERROR | Usage before subscription start cannot enter the event log without remediation. |
| usage_after_subscription_end | 290 | 25000 | 0.0116 | SUSPICIOUS_OCCURRENCE | May reflect late events, wrong assignment, or an invalid subscription window. |
| ticket_before_account_signup | 1077 | 2000 | 0.5385 | CONFIRMED_ERROR | Ticket submission must not precede account creation. |
| ticket_closed_before_submitted | 0 | 2000 | 0 | CONFIRMED_ERROR | Ticket close must not precede submission. |
| churn_before_account_signup | 0 | 600 | 0 | CONFIRMED_ERROR | Churn must not precede account creation. |
| churn_before_first_subscription | 53 | 600 | 0.088333 | CONFIRMED_ERROR | Churn before the first subscription lacks a valid subscription lifecycle. |
| churn_without_active_subscription | 55 | 600 | 0.091667 | SUSPICIOUS_OCCURRENCE | Requires lifecycle rules for multiple subscriptions before event-log construction. |
| churn_without_any_subscription | 0 | 600 | 0 | CONFIRMED_ERROR | A churn event without any subscription cannot be placed in a subscription lifecycle. |
| churn_after_all_subscription_ends | 0 | 600 | 0 | SUSPICIOUS_OCCURRENCE | May reflect delayed churn registration or an incomplete subscription history. |
| ticket_after_first_churn | 386 | 1395 | 0.276703 | POSSIBLE_BEHAVIOR | May be post-cancellation support, delayed entry, reactivation, or another subscription. |
| subscription_started_after_prior_churn | 2117 | 3528 | 0.600057 | POSSIBLE_BEHAVIOR | Supports a reactivation hypothesis but does not define reactivation by itself. |
| open_subscription_on_churned_account | 3176 | 3528 | 0.900227 | SUSPICIOUS_OCCURRENCE | May represent parallel subscriptions, reactivation, or incomplete closure fields. |

## 6–7. Multiple churns and reactivation

| measure | value |
|---|---|
| accounts_with_zero_churn_events | 148 |
| accounts_with_one_churn_event | 177 |
| accounts_with_multiple_churn_events | 175 |
| maximum_churn_events_per_account | 5 |
| explicit_reactivation_events | 61 |
| subscriptions_started_after_prior_churn | 2117 |
| reactivation_classification | EXPLICIT |
| final_rule_status | DECISION_PENDING_PHASE_2 |
| accounts_without_usage_ticket_or_churn | 0 |

## 8. Simultaneous events

| check | affected rows |
|---|---|
| feature_usage_same_subscription_date | 156 |
| support_tickets_same_account_timestamp | 10 |
| churn_events_same_account_date | 2 |

## 9. Temporal leakage risks

Outcome dates and all events after an as-of cutoff are prohibited as pre-churn features. Tickets after churn are occurrences to investigate, not automatically data errors.

## 10. Decisions required for Phase 2

- Define event-time and source-time semantics.
- Define treatment for repeated usage identifiers and same-time events.
- Define subscription lifecycle precedence for overlapping or sequential subscriptions.
- Define the provisional reactivation rule using explicit flags plus subscription chronology.
- Enforce per-event as-of cutoffs and exclude outcome/post-outcome fields.
