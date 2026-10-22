CHECKPOINT: 28 — Contract forensics preflight
STATUS: PASS
OBJECTIVE: Recheck current workspace, ownership, source data and runtime state before scoped writes.
WORK COMPLETED:
- Confirmed workspace and submission package are owned by `thomasleick`, writable, and the workspace remains outside a Git repository.
- Inspected the five CSVs, dataset README, historical churn module, API, frontend, Docker files, process logs and latest report.
- Recomputed SHA-256 for all five CSVs; hashes matched the previously recorded source hashes. No source CSV was changed.
- Confirmed the existing `ravenstack-historical` API/web services were healthy and left them running and unchanged.
- Identified three source grains: account, subscription, churn event. Event rows contain account_id but no subscription_id.
FILES CREATED: `process-log/prompts/004-contract-churn-forensics.md`; this checkpoint report.
FILES MODIFIED: NONE.
COMMANDS EXECUTED:
- `stat`, `find`, `ls`, `sha256sum`, `git status`/`git rev-parse` read-only probes.
- `docker compose -p ravenstack-historical ps`.
- Python stdlib CSV schema/row inspection.
TESTS EXECUTED: NONE.
TEST RESULTS: Not applicable to preflight.
EVIDENCE LEVEL: STATIC / SOURCE HASH.
BUSINESS FINDINGS: NONE at the preflight gate; prior counts treated as unverified until recalculation.
UNKNOWN: Commercial meaning of `end_date`; whether multiple same-account rows represent independent products, versions, or snapshots.
BLOCKERS: None for local work.
RISKS: Event table cannot explicitly relate event IDs to contracts; source is synthetic.
NEXT STEP: Recalculate the 66 subscription rows and 443 event/date conflicts from the original CSVs.
