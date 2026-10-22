CHECKPOINT: 13 — Usage, support and revenue
STATUS: PASS (descriptive); temporal and economic exposure remain UNKNOWN
OBJECTIVE: Compare available behavioral, support, and financial fields by explicit labels while preserving natural grain and exposing limitations.
WORK COMPLETED:
- Aggregated usage per account before comparison; kept all-date totals separate from the subscription-interval sensitivity and exposed feature coverage, beta, error, and session measures.
- Compared ticket-level means, denominators, missing satisfaction, response/resolution times, and escalation rates by each label. Account-level bootstrap intervals avoid resampling each ticket as if it were an independent account.
- Summarized MRR/ARR fields at source subscription-row grain, with explicit raw row sum labels, zero counts and distributions; did not translate those sums into revenue exposure.
- Counted event refunds as a separate observed field.
FILES CREATED: `outputs/usage-by-label.csv`; `outputs/feature-adoption.csv`; `outputs/support-by-label.csv`; `outputs/support-by-segment.csv`; financial output in `analysis-summary.json` and written report.
FILES MODIFIED: NONE outside the new module.
COMMANDS EXECUTED: Full analysis generation and `python3 -m unittest discover -s solution/analysis/conventional/tests -v`.
TESTS EXECUTED: Usage lifecycle and duplicate counts; support missingness; financial sums compared with source rows; deterministic bootstrap; no churn-rate placeholder.
TEST RESULTS: Usage rows: 19,142 before linked subscription start; 290 after non-null end; 5,568 within inclusive observed intervals; 5,562 valid-interval rows after first-per-duplicate-ID sensitivity. Any-event accounts average 503.4 all-time usage_count vs 495.4 for others (difference 8.1; account-bootstrap 95% CI -24.2 to 42.0). Event-history ticket satisfaction 3.980 (815 scored/1,395 tickets; 580 missing) vs 3.983 (360/605; 245 missing); account-cluster mean difference -0.009 (95% CI -0.122 to 0.102). First-response and resolution differences also have 95% intervals spanning zero. Subscription MRR rows median 931, range 0–33,830; ARR median 11,172, range 0–405,960; 778 rows are zero. Raw row sums are explicitly not unique/current revenue. Event refund fields total $8,652.25 across 600 rows (142 nonzero), not recurring revenue loss.
EVIDENCE LEVEL: LOCAL_RUNTIME / UNIT.
BUSINESS FINDINGS: Current comparisons do not show a clear all-time usage or ticket-satisfaction separator for accounts with any event; intervals are descriptive and cross-sectional, not evidence of no effect. The CEO's favorable usage/satisfaction narrative is not validated as temporal account-level improvement.
UNKNOWN: Valid pre-event usage/support signals, MRR/ARR movement, gross/net retention, lost or recoverable recurring revenue, causal economic impact.
BLOCKERS: No reliable lifecycle snapshots, currency/time eligibility ledger, or prospective cohort.
RISKS: Records often predate subscription starts; excluding date-invalid observations changes the analysis population and does not repair their chronology.
NEXT STEP: Publish integrated CEO answers and compare the conventional output with the preserved investigation; do not integrate into app without safe API/UI and runtime validation.
