CHECKPOINT: 24 — Historical preflight and method
STATUS: PASS
OBJECTIVE: Revalidate current workspace/data, inspect lifecycle semantics and identify a cohort method before computing historical conclusions.
WORK COMPLETED:
- Confirmed the authorized workspace and submission package are owned by `thomasleick`, writable, and independent of LeickOS. The workspace has no Git repository; no Git operation was performed.
- Rechecked the five source CSVs, schemas and original hashes. All five hashes match the prior verified values; no CSV was changed.
- Inspected the subscription schema and dataset README. The README defines blank `end_date` as active and subscription `churn_flag` as ended; event `churn_date` is described as when the account left. These are source descriptions, not independently verified business semantics.
- Confirmed the source’s latest start, nonblank end and event dates are 2024-12-31. The 2025-01-01 boundary is not an observed 2025 extract.
- Consulted G4’s public cohort article at https://g4educacao.com/blog/analise-de-coorte. It describes time-linked acquisition cohorts and retention comparison at equal elapsed periods. The page was not directly retrievable in the browser, but official indexed content was available; no proprietary G4 framework is claimed.
- Inspected the existing API, frontend, Dockerfiles, prior reports and prior checkpoints. Historical artifacts were not overwritten. The existing isolated RavenStack services were healthy; their containers were left untouched while a separate validation Compose project was later used.
FILES CREATED:
- `process-log/prompts/003-historical-churn-reconstruction.md`
FILES MODIFIED: NONE
COMMANDS EXECUTED:
- Read-only filesystem and source inspection (`ls`, `find`, `sed`, `rg`, `sha256sum`).
- `docker compose -p ravenstack-remediation -f solution/compose.yaml ps --format json`.
- Public G4 source search for the named cohort article.
TESTS EXECUTED: NONE
TEST RESULTS: Not applicable to preflight.
EVIDENCE LEVEL: STATIC
BUSINESS FINDINGS: NONE
UNKNOWN:
- Whether `end_date` is effective cancellation, planned end, or administrative status.
- Whether blank end dates mean active at the historical extraction time.
- Whether subscription rows represent distinct products, concurrent contracts or versions.
BLOCKERS: None for local analysis.
RISKS: Source semantic conflicts could make a date-derived rate conditional rather than a validated company KPI.
NEXT STEP: Independently calculate date-boundary populations and compare them with event and flag definitions.
