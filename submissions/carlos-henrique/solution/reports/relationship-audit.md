# RavenStack relationship audit

## 1–5. Tested relations, match rates, cardinalities, and orphans

| source | target | match rate | orphan rows | cardinality | children/source min-med-max | sources without children | inflation risk | status |
|---|---|---|---|---|---|---|---|---|
| accounts.account_id | subscriptions.account_id | 1 | 0 | ONE_TO_MANY | 2-10.0-19 | 0 | HIGH | UNSAFE_WITHOUT_AGGREGATION |
| subscriptions.subscription_id | feature_usage.subscription_id | 1 | 0 | ONE_TO_MANY | 0-5.0-16 | 33 | HIGH | UNSAFE_WITHOUT_AGGREGATION |
| accounts.account_id | support_tickets.account_id | 1 | 0 | ONE_TO_MANY | 0-4.0-11 | 8 | HIGH | UNSAFE_WITHOUT_AGGREGATION |
| accounts.account_id | churn_events.account_id | 1 | 0 | ONE_TO_MANY | 0-1.0-5 | 148 | HIGH | UNSAFE_WITHOUT_AGGREGATION |

## 6. Controlled join inflation

Only keys were joined in memory; no consolidated table was saved.

| join | before | after | multiplier | entities preserved | many-to-many risk | strategy |
|---|---|---|---|---|---|---|
| accounts LEFT JOIN subscriptions | 500 | 5000 | 10 | true | false | Aggregate child events to the intended as-of grain before joining. |
| subscriptions LEFT JOIN feature_usage | 5000 | 25033 | 5.0066 | true | false | Aggregate child events to the intended as-of grain before joining. |
| accounts LEFT JOIN support_tickets | 500 | 2008 | 4.016 | true | false | Aggregate child events to the intended as-of grain before joining. |
| accounts LEFT JOIN churn_events | 500 | 748 | 1.496 | true | false | Aggregate child events to the intended as-of grain before joining. |
| accounts -> subscriptions -> feature_usage -> support_tickets -> churn_events | 500 | 147896 | 295.792 | true | true | Do not materialize a mega-table. Build source-specific temporal events and aggregate as-of features at an explicitly selected grain. |

## 7. Future integration strategy

Maintain source-specific event grains. Aggregate or select as-of child records before entity-level joins, and reconcile row counts and unique entities after every step.

## 8. Rejected relations

- None at the tested foreign-key level.

## 9. Gate for event-log construction

A naïve mega-join is explicitly prohibited whenever the measured multiplier exceeds 1. Event-log construction must union normalized source events rather than multiply child tables against each other.
