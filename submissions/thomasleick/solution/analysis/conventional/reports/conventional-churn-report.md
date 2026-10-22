# Conventional churn analysis — RavenStack

## Executive conclusion

The data do not establish a conventional churn rate or a causal root cause. They contain several incompatible churn labels: **110** accounts with the supplied account flag, **352** with any event row, **339** with at least one non-reactivation event, and **312** represented by a flagged subscription. Only **75** accounts are positive under both the account flag and any-event definition. These differences are material and label-dependent.

The event record volume rises from **73** in 2023 to **527** in 2024, but there is no monthly eligible-account denominator; this is event volume, not an increasing churn rate. Usage and support data do not provide a defensible pre-cancellation window, while subscription revenue rows cannot be interpreted as unique current or lost revenue.

## Respostas às três perguntas do CEO

### Pergunta 1 — O que está causando o churn?

**Causa não identificada.** The event table records reason codes: budget=104, competitor=92, features=114, pricing=91, support=104, unknown=95. These are event-row descriptions, include reactivations and repeated accounts, and do not prove causal mechanisms. By any-event account membership, mean recorded ticket satisfaction is 3.980 (815/1395 scored tickets; 580 missing) versus 3.983 (360/605; 245 missing) among other accounts. This cross-sectional difference is negligible descriptively and non-temporal; it does not establish no support effect. Usage comparisons are also cross-sectional and are distorted by lifecycle timestamp inconsistencies.

At account grain, the all-time usage-count mean is 503.4 across 352 event-history accounts and 495.4 across 148 other accounts; the account-level bootstrap 95% interval for the mean difference (event minus no-event) is [-24.2, 42.0]. This descriptive interval cannot establish temporal order or causality. For ticket satisfaction, account-cluster bootstrap difference is -0.009, 95% interval [-0.122, 0.102], with scored-account denominators 330 vs 136; ticket-level score denominators above remain the observed score counts.

To identify causes, RavenStack would need reconciled prospective subscription states, dated exposure windows before cancellation, consistent outcome definitions, and a design that addresses confounding; reason codes should be verified through customer interviews.

### Pergunta 2 — Quais segmentos e contas estão mais em risco?

The accompanying `segment-account-labels.csv` compares account attributes under all four account-level definitions with denominators and Wilson 95% intervals. Examples: DevTools has the highest account-flag prevalence among industries (35/113 = 31.0%); partner-referred accounts have 67/89 = 75.3% with any event; and UK accounts have 43/58 = 74.1% with a non-reactivation event. These are label-conditioned exploratory comparisons and not stable predictive risk. At subscription grain, churn flags are nearly flat by billing frequency: annual 247/2461 = 10.0%, monthly 239/2539 = 9.4%. Segments with fewer than 30 observations are flagged for caution.

`account-event-volume-ranking.csv` lists identifiable accounts and signals, ordered only by observed non-reactivation event count. The top event-volume records include A-0a62f5 (5 events), A-180abf (5 events), A-0baac2 (4 events). These are examples of repeated observed records for reconciliation, not accounts forecast to churn or confirmed currently at risk.

### Pergunta 3 — O que a empresa deveria fazer?

1. **Instrument a canonical subscription lifecycle and monthly eligible-customer snapshot** — account flag (110), any-event label (352), non-reactivation-event label (339), and subscription-flag accounts (312) disagree; 4,514 subscription rows have no end_date while 486 are flagged ended. Success: reconciled account/subscription state and timestamped eligible cohort coverage. Validation: reconcile source-of-truth events and subscription states for a prospective cohort.
2. **Use reason codes and account examples as interview prompts, not root-cause verdicts** — 600 event rows include reason codes features=114, support=104, budget=104, unknown=95, competitor=92, pricing=91; reactivation rows included unless filtered. Success: coded, dated interviews linked to verified lifecycle outcomes. Validation: sample cancellation interviews and compare reason consistency with subsequent lifecycle.
3. **Pilot an adoption/support outreach only after a prospective eligibility rule is defined** — all-time usage per account and ticket satisfaction are descriptive and not temporally aligned; mean satisfaction 3.980 among event accounts (815 scored of 1,395 tickets) vs 3.983 among no-event accounts (360/605). Success: pre-registered 90-day account retention plus guardrails for support satisfaction and cost. Validation: randomize eligible accounts to outreach vs usual care, stratify by plan and baseline usage, analyze intention-to-treat.

No financial benefit or ROI is claimed. Staff effort and intervention cost were not supplied; exposure and recoverable recurring revenue remain **UNKNOWN**.

## Conventional Analysis vs. The Churn Paradox

- **Confirmed from current CSVs:** 500 accounts, 5,000 subscriptions, 25,000 usage rows, 2,000 tickets, 600 event rows; hashes are recorded in `outputs/analysis-summary.json`.
- **Label sensitivity:** account flag 110; any-event account 352; at least one non-reactivation event 339; and 312 distinct accounts with at least one flagged subscription (486 subscription rows are flagged). These are distinct account/subscription grains.
- **Reconciliation of the previously reported 312 discrepancy:** the current CSVs produce 312 accounts with different values between the account flag and any-event membership (symmetric difference), while account flag vs subscription-flag membership differs for 278 accounts. Thus 312 is specifically the account-flag/any-event disagreement count; it is not the number with account-vs-subscription disagreement. Across all four account-level indicators, 401 of 500 accounts differ on at least one label.
- **Robust limitation:** annual event rows are not rates and financial row sums are not recurring revenue lost. The label conflict and chronology issues are confirmed, while their meanings depend on which fields are compared.
- **Conclusions changed by label:** segments and account comparisons vary with outcome definition; inspect the complete output CSVs before prioritizing a segment.
- **Not confirmed:** increasing churn rate, satisfaction/usage causality, root cause, recurring revenue loss, preventable exposure, model performance, intervention uplift.

## Data and method

Source tables: accounts: 500 rows, subscriptions: 5,000 rows, feature_usage: 25,000 rows, support_tickets: 2,000 rows, churn_events: 600 rows. Current SHA-256 values are in the output summary. Joins use account IDs or subscription IDs and retain the natural grain. Account metrics are aggregated per account before comparison; tickets/events/subscriptions are not joined into one fan-out table. Duplicate usage IDs are retained in raw totals and separately quantified: **21 IDs, 42 rows in duplicate-ID groups, 21 excess rows**. Valid-interval usage is a sensitivity only; the interval convention is start_date ≤ usage_date ≤ end_date, or no end bound where end_date is blank. It does not repair the source chronology.

The account-level label is the dataset's supplied `accounts.churn_flag`. Event labels are (1) any account with an event including reactivation and (2) any account with at least one event where `is_reactivation` is false. The second does not mean final churn. Subscription-level results use the source subscription churn flag. Wilson intervals describe binomial proportions under each observed label; they do not correct selection, synthetic generation, or label error.

Subscription financial columns are analyzed at source-row grain. Across 5,000 rows, recorded MRR values range $0–$33,830 (median $931); ARR values range $0–$405,960 (median $11,172). There are 778 zero-valued rows. The table has repeated contract rows per account and mixed lifecycle states; even the raw row sums ($11,338,747 MRR field, $136,064,964 ARR field) are not unique/current/at-risk revenue. The observed event refund field sum is $8,652.25, across 600 event rows, and is not lost recurring revenue.

## Outputs

- `outputs/data-profile.json`: schema, nulls, duplicate keys, hashes and table sizes.
- `outputs/analysis-summary.json`: definitions, counts, comparisons and limitations.
- `outputs/segment-account-labels.csv`, `outputs/segment-subscription-label.csv`.
- `outputs/usage-by-label.csv`, `outputs/feature-adoption.csv`.
- `outputs/support-by-label.csv`, `outputs/support-by-segment.csv`.
- `outputs/account-event-volume-ranking.csv`.
- `outputs/label-definition-comparison.svg`, `outputs/event-rows-by-year.svg`.

## Reproduction and limitations

From the standalone `solution/` directory: `python analysis/conventional/run.py --data-dir data/raw --output-dir analysis/conventional/outputs`. Run tests with `python -m unittest discover -s analysis/conventional/tests -v`. The implementation uses Python standard library only. No calibrated prediction or causal inference was attempted; there is no suitable event-time cohort or temporal holdout.
