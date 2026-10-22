# Executive summary — Contract churn forensics

## What the records show

- At 2024-01-01, the date rule identifies 191 accounts and 655 active subscription IDs.
- By 2025-01-01, 66 of those subscription IDs have an end date: 10.08% conditional subscription-row exits.
- Those 66 IDs belong to 57 accounts. Every ended row has another same-account subscription active on its end date; all 57 accounts maintain date-derived coverage through 2024 and appear active at the closing boundary.
- Of 472 non-reactivation event rows in 2024, 443 occur on dates when at least one same-account subscription is active. They represent 302 accounts; 395 rows have multiple active subscriptions that day.
- Only 104/443 conflicting rows fall within ±30 days of any same-account 2024 end date; 160/443 fall within ±60 days. This is timing proximity, not event-to-contract linkage.

## Leadership interpretation

The evidence supports contract-row endings and a serious lifecycle-definition mismatch. It does not establish that RavenStack lost 57 or 66 customers, that the event rows are false, or that a reason code caused churn. Revenue loss remains UNKNOWN. The recorded MRR/ARR sums are not defensible lost-revenue estimates.

## Decision

Separate subscription churn from account/logo churn. Reconcile all 66 contract rows and successor candidates to billing and entitlement records, add an explicit event-to-subscription link and lifecycle event type, then rebuild verified customer-month cohorts. Do not launch a broad save campaign using the current event labels. Use pricing, features, support and budget reasons to guide structured customer interviews and reason-code validation, not as proven causes.

Detailed row evidence, definitions, account examples, segment denominators and tests: [Contract churn forensics report](CONTRACT-CHURN-FORENSICS.md).
