CHECKPOINT: 25 — Historical date and cohort calculations
STATUS: PARTIAL
OBJECTIVE: Reconstruct 2023/2024 account and subscription churn directly from source dates and compare alternative labels.
WORK COMPLETED:
- Added an isolated, standard-library analytical module with explicit CLI paths, source hashes, annual/monthly outputs, interval-gap logic, event conflicts and first-subscription cohort diagnostics.
- Collapsed concurrent subscription rows to distinct accounts for logo calculations; preserved subscription-level denominators separately.
- Added tests for end-date exclusivity, multi-subscription logos, account churn/reactivation, a final subscription termination, zero denominators and real-source outputs.
- Generated JSON plus annual, monthly and conditional cohort CSV outputs from the original CSVs.
- Wrote the methodological report without overwriting any earlier findings.
FILES CREATED:
- `solution/analysis/historical_churn/__init__.py`
- `solution/analysis/historical_churn/reconstruct.py`
- `solution/analysis/historical_churn/README.md`
- `solution/analysis/historical_churn/tests/test_reconstruct.py`
- `solution/analysis/historical_churn/outputs/historical-churn.json`
- `solution/analysis/historical_churn/outputs/annual-reconciliation.csv`
- `solution/analysis/historical_churn/outputs/monthly-reconstruction.csv`
- `solution/analysis/historical_churn/outputs/cohort-retention-conditional.csv`
- `docs/findings/HISTORICAL-CHURN-RECONSTRUCTION.md`
FILES MODIFIED: NONE outside the new module/report at this checkpoint.
COMMANDS EXECUTED:
- `python analysis/historical_churn/reconstruct.py --help`
- `python analysis/historical_churn/reconstruct.py`
- `python -m unittest discover -s analysis/historical_churn/tests -v`
- Independent standard-library recomputation of the three snapshots, 2024 set loss, subscription set loss, 2024 event incidence and stored source hashes.
TESTS EXECUTED: Historical reconstruction unit tests, 5 tests.
TEST RESULTS: 5/5 passed. Independent check reproduced 0 accounts at 2023 start; 191 accounts/655 subscriptions at 2024 start; 500 accounts at 2025 boundary; 0/191 date-derived 2024 logo loss; 66/655 opening subscriptions no longer active.
EVIDENCE LEVEL: UNIT / SOURCE-DATA REPRODUCTION
BUSINESS FINDINGS:
- 2023 classic logo churn is undefined because opening base is 0.
- Conditional 2024 date-derived classic logo churn is 0/191 = 0.0%; conditional opening-subscription exit rate is 66/655 = 10.08%.
- 2024 has 103/191 opening accounts with non-reactivation events; 443/472 non-reactivation event rows occur while at least one linked subscription is date-active.
- Monthly date-rule account gaps appear in 2023-11, 2024-03, 2024-04 and 2024-09; monthly denominators differ from the annual opening cohort.
- 24 first-start cohorts produce 300 month-age points and four intermediate dips; each cohort is back to 100% at its latest boundary. These remain conditional, not validated retention.
UNKNOWN:
- True account loss and whether event dates mean full logo cancellation.
- Whether reactivation markers encode relationship transitions.
- True post-2024 status, recurring revenue churn and causal drivers.
BLOCKERS: None to produce conditional date calculations.
RISKS: Treating a date-derived 0% as a validated churn rate would contradict the 2024 event and flag evidence.
NEXT STEP: Serve these outputs through the API and add an explicitly conditional view in Chapter 02.
