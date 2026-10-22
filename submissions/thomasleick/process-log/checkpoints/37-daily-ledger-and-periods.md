CHECKPOINT: 37 — Daily ledger and period aggregations
STATUS: PASS
OBJECTIVE: Build deterministic daily account × plan-proxy transitions and aggregations from the daily source of truth.
WORK COMPLETED: Added interval consolidation, daily plan/customer state, acquisition/loss/reactivation and portfolio expansion/contraction movements; added period summaries, candidate tier transition sensitivity, event reconciliation, source hashes/schemas, segment and account outputs. Preserved invalid intervals in results. Re-generated JSON and CSVs from raw source files. Calendar boundary snapshots now expose date snapshot versus transition opening explicitly.
FILES CREATED: `solution/analysis/daily_portfolio_churn/` engine, CLI, README, tests and `outputs/` JSON/CSV artifacts.
FILES MODIFIED: `solution/analysis/daily_portfolio_churn/engine.py` (the module was newly added in this mission).
COMMANDS EXECUTED: `PYTHONPATH=analysis python3.12 -m daily_portfolio_churn --data-dir data/raw --output-dir analysis/daily_portfolio_churn/outputs` from `solution/`.
TESTS EXECUTED: Engine tests included in the Docker test stage.
TEST RESULTS: Daily run produced 731 rows; 62 plan-proxy loss events, 1,433 first relations, 43 plan returns, 8 complete-coverage loss events, 500 first-observed customers, 8 customer returns, 0 daily bridge failures. 13 invalid nonpositive rows are retained as an explicit invalid inventory.
EVIDENCE LEVEL: UNIT / SYNTHETIC and STATIC for algorithm tests; source-data computations are conditional reconstruction.
BUSINESS FINDINGS: 54/62 plan losses occur while another plan remains; all 8 complete coverage gaps later return by horizon close. 2024 opening cohort: 7/374 plan relations lost coverage at any point (1.87%), 3/374 remain inactive at close (0.80%); customer opening cohort has 0/190 complete coverage losses. These are date/plan-proxy outcomes only.
UNKNOWN: Actual products, confirmed migration, commercial cancellation, and revenue changes.
BLOCKERS: None for local data analysis.
RISKS: Date-only interval convention and date snapshot/transition opening boundary are not interchangeable; the report makes both visible.
NEXT STEP: Expose outputs in API and four-chapter frontend.
