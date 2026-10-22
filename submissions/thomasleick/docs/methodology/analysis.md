# Methodology and evidence contract

## Source and reproducibility

The source consists of the five original CSV files from Rivalytics' public Kaggle dataset. The challenge README labels the dataset MIT and a read-only request to Kaggle public metadata returned licenseName=MIT. Its bundled dataset README uses “MIT-like (fully synthetic, no PII)” and requests credit to River @ Rivalytics. Keep that notice with the files. This package retains the original CSVs and source README. Their hashes and the reproduced profile hashes are recorded in process-log/evidence/.

Run from solution/ using Python 3.12 and apps/api/requirements.txt. The API analytics.engine.build_analysis(data_dir) reads every required CSV and fails visibly when one is missing. It converts date fields explicitly and aggregates event, subscription, account, usage and ticket facts at their own grain. The API never joins unaggregated usage/tickets/events onto subscription money.

## Definitions and evidence states

- **Event rows:** rows in ravenstack_churn_events.csv; may include repeated account lifecycle events.
- **Event accounts:** distinct account_id with one or more event rows over the full file; not period churn.
- **Account flag:** account rows with churn_flag=True; a separate source definition, not reconciled to events.
- **Ended subscription row share:** rows with non-null end_date divided by all subscription rows. Descriptive only; not a period rate.
- **Logo churn:** distinct eligible paying accounts lost in a period divided by eligible paying accounts at its beginning. UNKNOWN because eligibility, active status, cancellation, reactivation and censoring do not reconcile.
- **Gross revenue churn / GRR / NRR:** UNKNOWN without comparable opening and closing recurring revenue snapshots and account/subscription lifecycle mapping.
- **Refund sum:** sum of the event table refund_amount_usd; observed field only, never equated to recurring revenue lost.
- **Usage:** reported usage_count and record count; no exposure-normalized or valid account-month trend is asserted.
- **Satisfaction:** mean over non-null ticket scores with denominator disclosed. Cross-sectional grouping by any event history is retrospective and non-causal.

## Findings and statistical limits

The event history contains 600 rows, 352 distinct event accounts, and 61 reactivation-marked rows. Account flags mark 110/500 accounts. The reconciliation table is 75 flag+event, 35 flag only, 277 event only, and 113 neither. Consequently 312/500 definitions conflict. The raw event counts are 73 for 2023 and 527 for 2024, but no eligible-account-time denominator or trustworthy censoring/reactivation rule exists. This is event-record growth, not demonstrated churn-rate growth.

The raw monthly usage series remains in a similar volume range. Yet 19,142/25,000 usage rows precede the linked subscription start; 290 follow a non-null end date. There are 21 distinct duplicated `usage_id` values; 42 rows belong to those duplicate groups, of which 21 are excess rows beyond the first occurrence per ID. There are 825/2,000 tickets without satisfaction. On the retrospective split, scores average 3.980 (815 scored tickets associated with event accounts; 580 missing) and 3.983 (360 scored tickets for no-event accounts; 245 missing). In the 1,395 tickets tied to 347 accounts with any event history, median first response is 89 minutes, median resolution is 35 hours, and 71/1,395 tickets (5.09%) are escalated. In 605 tickets tied to 145 accounts without event history, the respective values are 87 minutes, 35 hours, and 24/605 (3.97%). These are all-time ticket-level summaries; account membership is not a pre-churn cohort. The denominators are ticket scores/tickets, not equal-sized account samples. These small descriptive differences do not support temporal deterioration, a protective effect, or causation.

Event reasons are descriptive labels, not independently verified explanations. A category count, including the largest category, cannot establish a root cause. The five sources are synthetically generated; observed inconsistencies constrain inference and external validity.

## Join/cardinality safeguards

account_id is one row per account in the account source. subscription_id maps usage many-to-one to subscription. Events and tickets are many-to-one to account only after aggregating at their respective grains. The analysis uses validated many_to_one or one_to_one account/subscription joins and calculates monetary sums from the subscription table before any event/usage/ticket comparisons. The event table has no subscription key; do not infer which contract an event ended.

## Prediction and causal analysis

No model is fit. There is no validated binary target or point-in-time training snapshot; post-outcome information and invalid usage timestamps make leakage likely. No temporal train/test evaluation or calibrated risk estimate is defensible. No intervention was performed. Scenarios in the Decision Room accept a user-supplied incremental percentage-point retention lift, generic currency units, cost and value and are explicitly hypothetical. The model assumes incremental retained accounts contribute the assumed monthly value for the full selected horizon. Sensitivity is arithmetic around user inputs, not a confidence interval or causal uplift.

## Unresolved data contract

A production-grade monthly ledger should contain stable account_id and subscription_id, effective start/end timestamps, paid eligibility, lifecycle event type, reactivation linkage, currency, MRR at each snapshot, expansion/contraction/cancellation movement, and a predeclared cutoff for feature and support signals. These allow lifecycle reconciliation and lagged, account-month comparisons before any risk model or ROI claim.
