CHECKPOINT: 50 — Upgrade/Downgrade Audit and Integrated Validation
STATUS: PASS
OBJECTIVE: Reconcile explicit subscription-row transition flags with candidate date-derived plan transitions, keep their accounting separate, and validate the application changes.
WORK COMPLETED:
- Re-read the subscriptions schema and dataset dictionary. `upgrade_flag` and `downgrade_flag` exist and are described as mid-cycle plan changes.
- Reproduced 529 upgrade-flag rows, 218 downgrade-flag rows, 23 rows with both flags, 307 accounts with an upgrade flag, and 177 with a downgrade flag.
- Reproduced 483 upgrade-flag and 193 downgrade-flag rows with null end dates. Candidate interval pairs within 30 days remain 52 possible upgrade-direction and 51 possible downgrade-direction pairs under an unverified plan-name order.
- Added independent row-flag audit artifacts and a documented classification: 0 confirmed, 0 inferred, 103 possible candidate pairs. Flags lack the dated from/to subscription linkage needed to validate any specific pair; tier order remains unverified.
- Added `GET /api/transition-audit` and an in-product evidence panel. The monthly lab keeps possible transition counts as separate annotations and never adds them again to acquisition or loss flows.
- Financial expansion/contraction remain UNKNOWN. Recorded `mrr_amount` distributions do not establish effective-dated before/after values.
- Revalidated the PDF artifact from Phase 1 and retained the paper's existing treatment of row flags as signals rather than confirmed migrations.
FILES CREATED:
- solution/analysis/transition_audit/audit.py
- solution/analysis/transition_audit/README.md
- solution/analysis/transition_audit/tests/test_audit.py
- solution/analysis/transition_audit/outputs/transition-audit.json
- solution/analysis/transition_audit/outputs/transition-candidates.csv
- docs/findings/UPGRADE-DOWNGRADE-AUDIT.md
- process-log/checkpoints/50-transition-audit-and-integrated-validation.md
- process-log/prompts/009-g4-final-delivery.md
- solution/apps/web/src/features/monthly-lab/TransitionAuditSummary.tsx
FILES MODIFIED:
- solution/apps/api/Dockerfile
- solution/apps/api/src/main.py
- solution/apps/api/src/schemas/contracts.py
- solution/apps/api/tests/test_api.py
- solution/apps/ web source (App, API client, contracts, styles, monthly lab)
- README.md
- process-log/checkpoints/49-monthly-business-laboratory.md
COMMANDS EXECUTED:
- `python3.12 analysis/transition_audit/audit.py --data-dir data/raw --ledger analysis/daily_portfolio_churn/outputs/g4-alignment/daily-portfolio-churn.json --output-dir analysis/transition_audit/outputs`
- `docker build -f apps/api/Dockerfile --target test -t ravenstack-api-test:local .`
- `docker run --rm ravenstack-api-test:local`
- `docker run --rm -e RUFF_CACHE_DIR=/tmp/ruff-cache ravenstack-api-test:local ruff check ...`
- `npm test`
- `npm run build`
- `python3.12 -m compileall -q apps/api/src apps/api/tests analysis/transition_audit`
- `docker compose ps -a` (read-only pre-runtime inventory)
TESTS EXECUTED:
- API/analysis test image: 44 tests.
- Ruff on touched backend and audit files.
- Frontend unit tests and TypeScript/Vite build.
TEST RESULTS: 44 passed, 1 Starlette deprecation warning; Ruff “All checks passed”; Vitest 8/8 passed across 3 files; TypeScript/Vite production build and Compose config validation passed. Both project containers reached healthy. HTTP smoke verified all 24 monthly rows, transition audit counts, 2024-01 scenario POST through the frontend proxy, and the web root.
EVIDENCE LEVEL: UNIT/SYNTHETIC + INTEGRATION + LOCAL_RUNTIME
BUSINESS FINDINGS:
- Subscription-row flags are present and numerous, but do not map to a dated from/to pair. No confirmed migration is established.
- The possible transition counts are conditional on an unverified tier hierarchy; they are not new churn events.
UNKNOWN:
- Which flagged row is the prior/next contract, plan ordering, effective price change, and recurring revenue contraction/expansion.
BLOCKERS: Browser visual QA remains unavailable due the previously denied local browser access; no alternate browser or CDP boundary was used. Browser/viewports remain UNKNOWN.
RISKS:
- Transition candidates use the existing daily engine's name-based assumed hierarchy; source flags may describe mid-cycle events that are not independently joinable.
NEXT STEP: Final package status is recorded in checkpoint 51; leave the project services running on the verified local ports for review.
