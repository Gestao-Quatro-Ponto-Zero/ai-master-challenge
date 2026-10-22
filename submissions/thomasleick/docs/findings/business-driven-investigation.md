# Business-driven investigation — independent audit and findings

**Generated from current source CSVs:** 2026-10-21. Reproduce with `cd solution && python analysis/business_drivers/run.py --data-dir data/raw --output-dir analysis/business_drivers/outputs`.

## Executive read

The strongest demonstrated issue is that RavenStack's records do not define one consistent customer outcome. Four account-level indicators disagree for 401/500 accounts on at least one pairwise comparison; the supplied account flag and “any event” membership differ for 312. This is an outcome/lifecycle reconciliation problem, not proof that 401 records are wrong. Event counts rise from 73 in 2023 to 527 in 2024, but eligible account-month denominators and reconciled cancellation states are unavailable, so rising churn rate remains **UNKNOWN**.

The two event-derived labels are more similar to one another: 339/352 accounts with any event have a non-reactivation event; 13 have only reactivation event rows. Some segment patterns are directionally similar under both event labels (UK, partner referral and DevTools), but are not stable under the separate account flag. These are candidate diagnostic cuts, not risk segments or proof of acquisition mismatch. No causal mechanism, validated account-level future risk, recurring revenue lost, or intervention effect is established.

## Independent outcome audit

| Outcome indicator | Positive accounts | Definition and limit |
|---|---:|---|
| Account flag | 110/500 (22.0%) | Supplied `accounts.churn_flag`; an operational label, not a period churn rate. |
| Any event | 352/500 (70.4%) | One or more event rows, including 61 reactivation rows. An account can have repeat rows. |
| Non-reactivation event | 339/500 (67.8%) | At least one row explicitly not marked reactivation. This does not prove a final cancellation or current state. |
| Flagged subscription account | 312/500 (62.4%) | Account membership with at least one flagged subscription; 486 subscription rows are flagged. |

The account flag vs. any-event table is 75 positive under both, 35 flag-only, 277 event-only, and 113 neither; its symmetric difference is 312. The other pairwise differences are 301 (account flag vs. non-reactivation membership), 278 (account flag vs. subscription-flag membership), and 13 (any-event vs. non-reactivation event membership). Across all four binary indicators, 401 accounts have at least one disagreement. The labels may describe different lifecycle concepts, so the discrepancy must be investigated against contract and source-system state rather than “cleaned” by selecting one as truth.

There are 600 event rows: 539 marked non-reactivation, 61 marked reactivation. Year totals are 73 rows in 2023 and 527 in 2024. The dataset has no eligible-customer population for those periods, and accounts have repeated event records. No churn rate or causal “increase” is calculated.

## Acquisition and ICP diagnostics

The script produces account-grain prevalence and 95% Wilson intervals by acquisition source, industry, country, plan and trial status under all four outcome indicators. This is an exploratory screen; it does not adjust for profile composition, cohort age, selection, or the synthetic data generation process.

Examples for account attributes with at least 30 accounts:

| Segment | Any-event label | Non-reactivation label | Account flag | Read-through |
|---|---:|---:|---:|---|
| UK (58 accounts) | 45/58 (77.6%) | 43/58 (74.1%) | 19/58 (32.8%) | Event-derived indicators are both above their overall prevalence, but confidence intervals are wide and label meaning is unresolved. |
| Partner referral (89) | 67/89 (75.3%) | 64/89 (71.9%) | 13/89 (14.6%) | Higher event membership and lower account-flag prevalence point in different directions; not proof of channel quality. |
| DevTools industry (113) | 83/113 (73.5%) | 81/113 (71.7%) | 35/113 (31.0%) | Direction is similar across three indicators, but it remains descriptive and not adjusted for other attributes. |
| Ads source (98) | 59/98 (60.2%) | 56/98 (57.1%) | 23/98 (23.5%) | Lower event membership than the event-label portfolio average, not proof that ads produce better customers. |

The primary event-label patterns (UK, partner, DevTools) are consistent between any-event and non-reactivation membership; the account flag tells a different story for partner referral. The source does not include acquisition cost, contribution margin, sales cycle, expected value or reliable outcomes by acquisition cohort. An ICP mismatch remains a hypothesis.

At subscription-row grain, annual billing has 247/2,461 flagged rows (10.0%, Wilson 95% 8.9–11.3%) and monthly billing 239/2,539 (9.4%, 8.3–10.6%). These intervals overlap and the measure is subscription-flag prevalence, not subscription churn during a billing period.

## Cohort and activation audit

Signup quarter can be constructed for all 500 accounts (eight cohorts, 53–80 accounts each). The output reports the mix of retrospective outcome flags by signup quarter and explicitly suppresses a retention heatmap. For example, the account-flag share is 29.1% for 2023-Q1 and 15.0% for 2024-Q4, while any-event share is 72.7% and 67.5%, respectively. These comparisons are not retention: the newest cohort has much less potential observation time, outcome state is not longitudinally reconstructed, and labels conflict. We also calculate quarter of the earliest listed subscription start per account as a second diagnostic anchor. Since accounts have multiple rows and “first eligible paid subscription” is not defined, that date is not asserted to be the first paid start; it also remains label composition rather than retention.

For an activation sensitivity, usage rows were joined to exactly one subscription by `subscription_id` and retained only when `start_date ≤ usage_date ≤ end_date` (with no upper bound when `end_date` is blank). This leaves 5,568 rows and 469 accounts with at least one row; 19,142 rows precede start and 290 follow a nonblank end. The first interval-valid usage is a proxy relative to account signup: median 77 days; 10/469 within 7 days and 62/469 within 30 days. These dates do not prove onboarding or “time to value”; account signup is not a validated activation event, and 31 accounts have no valid-period usage row.

The interval-valid usage total is 55,724 source `usage_count` units. The top decile of 47 accounts contributes 25.1%; top 10 accounts contribute 6.9%, and top 50 contribute 26.4%. This does not show unusual concentration without a business benchmark, nor does usage count establish customer value. By any-event membership, interval-valid mean usage is 113.3 per account among 352 accounts versus 107.1 among 148 without events; the data are not a verified pre-event comparison and duration/eligibility differs. Higher recorded use among the event group therefore neither proves nor refutes retention protection.

Duplicate sensitivity is distinguished explicitly: 21 duplicated usage IDs, 42 source rows in duplicate-ID groups, and 21 excess rows. There are 14 interval-valid rows belonging to duplicate-ID groups; retaining only the first source occurrence before interval filtering yields 5,562 valid rows, while deduplicating within the valid subset yields 5,565 unique IDs with a valid row. These are two different sensitivities, not contradictory counts.

## Customer experience and support

Satisfaction is missing on 825/2,000 tickets (41.25%). Under any-event account membership, 1,395 ticket rows from 347 accounts have mean satisfaction 3.9804 across 815 scored tickets (580 missing); the no-event group has 605 rows from 145 accounts, mean 3.9833 across 360 scored tickets (245 missing). Account-cluster means are 3.9616 (330 accounts with any score) and 3.9703 (136). Median first response is 89 vs. 87 minutes; median resolution is 35 hours in both. Event-group escalation is 71/1,395 ticket rows (5.1%) vs. 24/605 (4.0%). The ticket table has priority, but no ticket-category field; priority counts are returned by label without inventing categories.

These patterns are small/descriptive, vary with label and weighting grain, and have no verified event-time order. Ticket rows are not independent customers; the report therefore also shows account-level summaries. No causal support explanation is supported. Ticket category and priority are preserved in CSV outputs for further review, but event/ticket timestamps cannot be safely aligned into a pre-cancellation window.

## Perceived value and economics

The 5,000 subscription rows represent 500 accounts, with repeated subscriptions per account. Recorded MRR field values range 0–33,830 (median 931; 778 zero rows); ARR values range 0–405,960 (median 11,172; zero-row count is included in the generated JSON). The row sums, 11,338,747 MRR units and 136,064,964 ARR units, are not customer-level current revenue. The dataset does not establish currency/period semantics for every subscription field, snapshot time, effective dates, upgrades and downgrades as a reconciled bridge, or which subscription an event refers to. The event refund field totals USD 8,652.25 over 142 nonzero rows; refunds are not recurring revenue lost.

Current MRR, ARR, logo churn, subscription churn by period, GRR, NRR, LTV, historical revenue lost, at-risk revenue, preventable exposure and ROI remain **UNKNOWN**. The Decision Room's effect and value fields remain user-entered hypothetical assumptions.

## Specific account investigation candidates

These are identifiable follow-up records, selected by repeat history or label disagreement—not future-risk accounts:

| Account | Observed reason to investigate | What to verify |
|---|---|---|
| `A-0a62f5` / Company_381 | 5 event rows, all non-reactivation; account and subscription flags are false; two ticket rows; one interval-valid use row. | Determine why event history has five rows but both flags remain false; confirm whether rows represent cancellation cycles, errors or duplicate business events. |
| `A-180abf` / Company_122 | 5 event rows, account flag and subscription membership true; 64 seats; 3 tickets. | Confirm dates and whether five rows represent separate subscriptions, reactivation cycles or repeated cancellation events. |
| `A-37f969` / Company_150 | 4 event rows, account and subscription flags false; five tickets, one escalation. | Reconcile the lifecycle timeline and inspect support context; no causal or current-risk status implied. |
| `A-fd7ad3` / Company_100 | 4 event rows (3 non-reactivation), subscription-flag account true but account flag false; eight tickets, one escalation. | Resolve cross-table status and support chronology before any outreach decision. |

The complete candidate table is generated at `solution/analysis/business_drivers/outputs/account-investigation-candidates.csv` and surfaced in the Cost of Inaction chapter. Names are source identifiers; no real-world identity verification is claimed.

## Root-cause hypothesis ranking

| Priority / classification | Candidate mechanism | Evidence and counterevidence | Decision use |
|---|---|---|---|
| P0 · VERIFIED_OBSERVATION | Outcome/lifecycle instrumentation conflict | 401 accounts differ across four indicators; semantics may legitimately differ. | Reconcile definitions and effective-dated states before any rate or targeting. |
| P1 · CONDITIONAL_RESULT | Acquisition/ICP mismatch | UK, partner and DevTools event-label prevalence repeats across two event labels; account flag differs for partner; no CAC, margin, valid cohort or confounder adjustment. | Investigate by verified cohort after outcome definition, not change channel spend now. |
| P1 · UNKNOWN | Weak activation/time-to-value | Only proxy median 77 days among 469 accounts; 19,432 usage rows are outside subscription bounds; signup/onboarding event is not validated. | Instrument activation and first-value events. |
| P1 · CONDITIONAL_RESULT | Low adoption/concentrated use | Valid-period use exists in 469 accounts; top decile contributes 25.1%; account-level use is only a proxy. | Define meaningful use, compare at equal lifecycle ages, and run a pilot. |
| P2 · CONDITIONAL_RESULT | Support friction | Event-group satisfaction is similar under event membership; escalation and means vary by label/grain; 41.25% satisfaction missing. | Review escalated accounts and link ticket chronology to verified status. |
| P2 · UNKNOWN | Price/value mismatch | Budget/pricing reason codes occur; row-level subscription amounts exist. Codes are event descriptions and price/currency/value histories are unreconciled. | Verify through cancellation interviews and invoice/contract reconciliation. |
| P2 · UNKNOWN | Reliability/competitor gap | Usage error counts and feature/competitor codes exist; no incident exposure/release timeline or verified cancellation association. | Join incident telemetry and validate through customer evidence. |

These evidence priorities are qualitative, not probabilities. No candidate is declared a demonstrated causal root cause.

## Answers to the CEO

### 1. What is causing churn?

**Unknown.** The most certain finding is inconsistent measurement: 312 account memberships differ between the account flag and any-event label; 401 differ under at least one of four indicators. The most useful next candidate explanations are acquisition profile, activation/adoption and support friction, but current snapshots do not establish order or cause. Reason codes (“features” 114, “support” 104, “budget” 104 of 600 event rows) describe records, including reactivations and repeated accounts; they are not causal evidence.

### 2. Which segments and specific accounts are most at risk?

**No future-risk ranking is defensible.** Event-derived labels show exploratory prevalence differences for UK, partner referrals and DevTools; the account flag disagrees with some of those comparisons. Specific accounts above are reconciliation/investigation candidates only. There is no valid temporal target or calibration design for a model, and no current account-level risk probability.

### 3. What should RavenStack do?

First reconcile effective-dated account and subscription lifecycle and establish eligible denominators. Second instrument onboarding completion and a meaningful first-value event plus account-month feature/support states. Third, once eligibility is valid, run a randomized Customer Success adoption/support pilot with account-level assignment, 90-day verified retention as primary outcome, and satisfaction, escalation, discounts and service cost as guardrails. Staff effort is a planning assumption and must be estimated by the owner function; no benefit or causal uplift can be quantified from current files.

## Cohort and experiment design

The correct next dataset should store account acquisition cohort, paid-subscription start, trial conversion, monthly eligibility/status, cancellation effective date, reactivation and closing/opening recurring value. Retention should be measured at equal elapsed periods, with right censoring made visible. A test can then randomize eligible active accounts, stratify by verified plan/channel/value, assign a defined adoption or service intervention, analyze intention-to-treat, and report account retention at 90 days. Guardrails: account satisfaction response rate and score, ticket escalations, discounting, complaints and intervention cost. Define sample size and exclusions before assignment; do not treat repeated tickets as independent units.

## Reproduction and classification

Run the standard-library script and tests using commands in `solution/analysis/business_drivers/README.md`. It emits `business-investigation.json` and five CSV outputs. Account-segment Wilson intervals are descriptive binomial intervals; the analysis makes no causal or multiple-comparison-adjusted significance claim. Specific accounts and segment prevalence are explicitly label-conditioned. Synthetic source generation limits external validity.
