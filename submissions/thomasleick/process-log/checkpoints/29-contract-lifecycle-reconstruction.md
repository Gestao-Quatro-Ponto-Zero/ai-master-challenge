CHECKPOINT: 29 — Contract and event lifecycle reconstruction
STATUS: PASS for row reconciliation; commercial lifecycle remains UNKNOWN.
OBJECTIVE: Audit each ended opening subscription, conflicting event, reactivation marker, account continuity and monetary record.
WORK COMPLETED:
- Added an isolated standard-library analysis module with CLI, hashes, 66 subscription details, 443 conflicting events, 55 reactivation rows, 191-account indicator matrix and reproducible JSON/CSV outputs.
- Recalculated all 66 opening subscription exits: 57 accounts; another same-account subscription was active at each of the 66 end dates; no full account coverage gap among the 57; all 57 active at the 2025-01-01 date boundary; 55 rows had a successor start on/after the end date, without confirmed migration linkage.
- Recalculated 443/472 event rows with active subscription context, 302 distinct accounts, 395 rows with multiple active subscriptions and 278 accounts ever having multiple active subscriptions at an event date.
- Tested symmetric end-date proximity windows: conflict rows within 0/7/30/60 days = 5/39/104/160. These compare account dates only.
- Analyzed 55 reactivation-marked rows: 51 active on event date, 20 after an account subscription end, 45 before a later subscription start, 33 after an earlier non-reactivation event across source history; 14 accounts belonged to opening cohort.
- Added descriptive segment incidence, reason summaries, named record-reconciliation examples and MRR/ARR/refund guardrails.
FILES CREATED:
- `solution/analysis/contract_churn/{__init__.py,investigate.py,README.md}`
- `solution/analysis/contract_churn/tests/test_investigate.py`
- `solution/analysis/contract_churn/outputs/contract-churn-forensics.json`
- `solution/analysis/contract_churn/outputs/ended-opening-subscriptions-2024.csv`
- `solution/analysis/contract_churn/outputs/conflicting-nonreactivation-events-2024.csv`
- `solution/analysis/contract_churn/outputs/opening-account-reconciliation-2024.csv`
- `solution/analysis/contract_churn/outputs/reactivation-marked-events-2024.csv`
- `docs/findings/CONTRACT-CHURN-FORENSICS.md`, `docs/findings/CONTRACT-CHURN-EXECUTIVE-SUMMARY.md`
FILES MODIFIED: NONE outside new analysis and reports at this phase.
COMMANDS EXECUTED:
- `python analysis/contract_churn/investigate.py --help`
- `python analysis/contract_churn/investigate.py`
- `python -m unittest discover -s analysis/contract_churn/tests -v`
- `python -m unittest discover -s analysis/historical_churn/tests -v`
- Read-only Python probes for reactivation history, account examples, segments and end-date proximity.
TESTS EXECUTED: 5 contract-forensics tests; 5 historical reconstruction tests.
TEST RESULTS: Both suites passed 5/5. The source inventory matched 191 accounts/655 IDs, 66 endings/57 accounts and 443/472 conflict rows.
EVIDENCE LEVEL: SOURCE-DATA REPRODUCTION / UNIT.
BUSINESS FINDINGS:
- All 66 ended contract rows have another date-active contract; none of the 57 associated accounts lose merged date coverage in 2024.
- `mrr_amount` row values sum to 93,159 and `arr_amount` row values sum to 1,117,908, but these are explicitly non-authoritative row sums, not lost/current revenue. Conflict-event refunds: 110 rows, $7,044.82 recorded.
- Recorded reason codes show features 91, budget 82, support 81, unknown 77, pricing 72, competitor 69; reasons are not proven causes.
UNKNOWN: Whether each row is a paid contract, product entitlement, version or administrative snapshot; true lost recurring revenue; whether events describe full account cancellation.
BLOCKERS: None for analysis.
RISKS: An early event inventory initially retained all 472 rows rather than only the 443 conflicts; filtering was corrected and assertions now pin 443. A first reactivation-history probe restricted prior events to 2024; it was corrected to include all earlier source events (33 rows).
NEXT STEP: Expose results through API and existing Chapter 02 while keeping four-chapter structure.
