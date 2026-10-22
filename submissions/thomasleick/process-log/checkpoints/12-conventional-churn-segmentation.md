CHECKPOINT: 12 — Conventional churn labels and segmentation
STATUS: PASS (descriptive); predictive risk remains UNKNOWN
OBJECTIVE: Define alternate account/subscription outcomes, quantify disagreement and compare segment prevalence with denominators.
WORK COMPLETED:
- Kept separate (1) supplied account flag, (2) any event for an account including reactivation, (3) any explicitly non-reactivation event, and (4) account/subscription-flag comparisons.
- Generated per-segment positive counts, denominators, proportions, Wilson 95% intervals and a small-sample marker; account and subscription grains remain separate.
- Added account event-volume listing with evidence fields. It is not called a risk score.
- Reconciled the historical 312 account disagreement as the symmetric difference between account flag and any-event membership.
FILES CREATED: `outputs/segment-account-labels.csv`; `outputs/segment-subscription-label.csv`; `outputs/account-event-volume-ranking.csv`; label comparison SVG; updated summary/report.
FILES MODIFIED: NONE outside the new `solution/analysis/conventional/` module.
COMMANDS EXECUTED: Full `run.py` over current source CSVs; `python3 -m unittest discover -s solution/analysis/conventional/tests -v`.
TESTS EXECUTED: Label counts and cross-tab sum, alternate-label reconciliation, Wilson interval bounds and account/subscription grain checks.
TEST RESULTS: Account flag 110/500; any event 352/500; any non-reactivation event 339/500; accounts with >=1 subscription-flag row 312/500. Account flag vs any-event symmetric difference =312; account flag vs subscription-flag account membership difference =278; at least one disagreement among four account labels =401/500. Account flag vs any-event table: 75 both, 35 flag only, 277 event only, 113 neither. Subscription flag true rows =486.
EVIDENCE LEVEL: LOCAL_RUNTIME / UNIT — CSV-derived outputs plus automated invariant tests.
BUSINESS FINDINGS: DevTools shows 35/113 (31.0%) under account flag. Partner-referral accounts show 67/89 (75.3%) with any event; UK accounts 43/58 (74.1%) with a non-reactivation event. These segment leaders are label-dependent, exploratory, and not validated forward risk. Subscription churn-flag prevalence varies only 9.4% monthly to 10.0% annual in row-grain comparison.
UNKNOWN: Which outcome definition corresponds to true account loss; no calibrated probabilities, future risk ranking, or causal segment effects.
BLOCKERS: None for prevalence analysis; predictive objective lacks a defensible target/time split.
RISKS: Multiple segment comparisons are exploratory; confidence intervals do not repair synthetic-generation or label problems. Small segments are flagged.
NEXT STEP: Compare all-time and in-subscription usage sensitivity, support, and financial fields without join inflation.
