# RavenStack — Executive diagnostic

## Decision in one minute

The records show a sharp increase in **recorded event rows**, not a verified increase in customer churn rate. Account status and event history disagree for 312 of 500 accounts. Product activity totals are broadly stable, but their dates often precede the related subscription; satisfaction averages are nearly equal in an all-time split and 41.25% of ticket scores are missing. These files do not establish a root cause, recurring revenue loss, reliable risk segments or preventable revenue. Do not fund a broad save campaign from these labels. First reconcile account/subscription status and recurring value, then run a controlled pilot on verified eligible renewals.

## What is confirmed

| Observation | Evidence | What it means |
|---|---:|---|
| Five tables | 500 accounts; 5,000 subscriptions; 25,000 usage rows; 2,000 tickets; 600 churn-event rows | The files cover different entity grains and cannot be summed together blindly. |
| Conflicting churn labels | 352 event accounts; 110 account flags; 75 both, 35 flag only, 277 event only, 113 neither | 312/500 accounts disagree. Reconcile before targeting. |
| Recorded events grew | 73 event rows in 2023 and 527 in 2024 | Event volume grew 7.2×; eligible denominator and clean lifecycle are missing, so churn rate is UNKNOWN. |
| Usage timing is unreliable | 19,142 rows precede subscription start; 290 after a non-null end; 21 duplicated IDs (42 rows in those groups; 21 excess rows) | The data do not support a trustworthy account-level pre-churn usage trend or model. |
| Support evidence is all-time and mixed | Satisfaction missing in 825/2,000 tickets; means 3.980 (815 scored tickets, event accounts) vs 3.983 (360, no-event accounts). Median first response is 89 vs 87 minutes, median resolution 35 hours in both; escalations 71/1,395 (5.09%) vs 24/605 (3.97%). | Descriptive ticket-level groups, not pre-churn cohorts. The differences do not establish causes. |
| Financial bridge missing | USD 8,652.25 in recorded event refunds; 486/5,000 subscription rows have end dates, while every account also has at least one open-ended row | Refunds are not recurring revenue lost; neither MRR loss nor customer loss can be reconciled. |

## What is not confirmed

- The CEO's premise that **churn rate** increased.
- That usage or satisfaction increased over time for eligible active accounts.
- A causal driver behind events or a reliable at-risk segment.
- Specific accounts likely to churn. The app displays conflicting source records for reconciliation, not a risk ranking.
- Logo churn, subscription churn rate, GRR, NRR, MRR/ARR movement, exposed revenue or preventable loss.
- Predictive performance or intervention impact.

The public dataset describes itself as synthetic. Its values illustrate the investigation problem but do not establish RavenStack's real-world operating performance.

## Recommended actions

1. **Reconcile lifecycle data first.** Assign Data/RevOps responsibility to resolve 312 account-label conflicts; attach each lifecycle event to a subscription, normalize event timestamps, define reactivation and paid eligibility, and publish monthly account status.
2. **Restore a revenue ledger.** Preserve currency, opening/closing MRR snapshots, contracted value and movement reasons per account/subscription. Separate realized refunds from recurring revenue lost.
3. **Instrument pre-outcome product/support signals.** Store event time, subscription dates, active-account exposure, feature usage and support outcomes with stable denominators. Track ticket response and resolution as separate service measures.
4. **Then test one intervention.** On verified accounts renewing in 60 days, randomize at account level, stratify by plan and recurring value, and compare a defined CS/adoption treatment with a holdout. Use 90-day logo retention as primary outcome and verified MRR, satisfaction, discounting and complaints as guardrails. Predefine sample-size/power, exclusions, censoring and stopping rules before rollout.

## Economic implications

Observed recurring-revenue exposure is **UNKNOWN**. Do not equate subscription-row mrr_amount, a raw current-looking sum, refunds or event counts to lost/at-risk revenue. For planning only, the Decision Room calculates selected accounts × user-supplied incremental retention lift × assumed monthly value × assumed horizon − contact cost, in generic user-supplied units. Each input is editable, and outputs are hypothetical; the source dataset does not calibrate them. The arithmetic assumes every incrementally retained account contributes the assumed value through the full horizon.

## What to measure next

Build an account-month cohort with eligible paying accounts at period start, cancellations, reactivations, plan changes, opening/closing MRR, valid feature signals before renewal, and ticket outcomes in the same pre-renewal window. Reconcile counts to a finance/CRM system of record. For the pilot, report intention-to-treat retention lift with uncertainty and guardrails; do not scale based on treated-customer anecdotes.
