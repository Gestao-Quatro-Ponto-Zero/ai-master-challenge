CHECKPOINT: 41 — Final consolidation preflight and current baseline
STATUS: PASS
OBJECTIVE: Revalidate the authorized package, source hashes, prior ledger and project runtime before editorial changes.
WORK COMPLETED: Confirmed workspace and submission ownership; confirmed there is no Git repository at the workspace root; found checkpoints through 40; rechecked all five CSV hashes; reran daily portfolio ledger into `/tmp/ravenstack-final-verify` so historical package outputs remained unchanged; inspected app contracts, source/docs, compose targets and running containers. Existing RavenStack containers on 8000/5173 and 15175/18200 were identified and preserved.
FILES CREATED: None in this checkpoint.
FILES MODIFIED: None in this checkpoint.
COMMANDS EXECUTED: `sha256sum solution/data/raw/*.csv`; `PYTHONPATH=analysis python -m daily_portfolio_churn --data-dir data/raw --output-dir /tmp/ravenstack-final-verify`; `docker ps`; `docker compose ps`; `docker compose --env-file .env.example config --quiet`; read-only source/report inspections.
TESTS EXECUTED: Baseline generation only; formal tests are in checkpoint 43.
TEST RESULTS: Current rerun: 731 daily rows; 1,476 merged intervals; 1,433 first relations; 43 reactivations; 62 plan-proxy loss events affecting 60 accounts; 8 complete-coverage loss events; zero plan/customer bridge failure days. 2024 opening cohort: 190 accounts / 374 account-plan relations, 7 relations with any loss (1.8717%), 3 inactive at close (0.8021%), 0/190 full account coverage losses.
EVIDENCE LEVEL: INTEGRATION for deterministic source-to-ledger reproduction; STATIC for filesystem and source inspection.
BUSINESS FINDINGS: Customer churn remains UNKNOWN as a commercially verified KPI. Date-derived plan-proxy measures are reproducible but conditional on `[start_date, end_date)` semantics.
UNKNOWN: Whether subscription `end_date` is commercial cancellation or administrative/contract end; stable product identity; recurring-revenue ledger; causal drivers; current rendered browser behavior.
BLOCKERS: Browser visual validation not attempted because local browser access was previously denied; do not bypass the boundary. Default ports are occupied by existing project containers.
RISKS: Historical README numbers and earlier process records are retained; only the new evidence artifact represents this current run.
NEXT STEP: Consolidate the app's top-level metrics, daily boundary explanation, account timelines, direct executive answers and readiness reports.
