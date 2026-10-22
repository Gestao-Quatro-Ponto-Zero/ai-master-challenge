CHECKPOINT: 49 — Monthly Business Laboratory
STATUS: PASS
OBJECTIVE: Add an observed-versus-scenario laboratory to the existing Decision Room using actual monthly ledger rows.
WORK COMPLETED:
- Added `POST /api/monthly-lab/scenario`, typed request/response validation, immutable monthly opening bases, flow bridges, cohort loss rates, three sensitivity cases, and scenario-only financial arithmetic.
- Added the React Monthly Business Laboratory to the existing fourth chapter: real-month selector, separate Observed/Scenario modes, editable movement assumptions, tier-level proxy controls, unit-neutral values, reset, API error handling, and local JSON export.
- Added tests for baseline-versus-scenario separation, impossible flows, immutable opening bases, out-of-window month, zero-denominator UNDEFINED, and all 24 source months.
- Scenario transition counts remain annotations and do not add to loss/acquisition totals. All monetary outputs are explicitly user-assumption-only; the observed baseline has no reconciled revenue comparison.
FILES CREATED:
- solution/apps/web/src/features/monthly-lab/MonthlyBusinessLab.tsx
- solution/apps/web/src/features/monthly-lab/MonthlyBusinessLab.test.tsx
FILES MODIFIED:
- solution/apps/api/src/schemas/contracts.py
- solution/apps/api/src/main.py
- solution/apps/api/tests/test_api.py
- solution/apps/web/src/App.tsx
- solution/apps/web/src/contracts.ts
- solution/apps/web/src/lib/api.ts
- solution/apps/web/src/styles.css
COMMANDS EXECUTED:
- `npm test`
- `npm run build`
- `python3.12 -m compileall -q apps/api/src apps/api/tests analysis/transition_audit`
- `docker build -f apps/api/Dockerfile --target test -t ravenstack-api-test:local .`
- `docker run --rm ravenstack-api-test:local`
TESTS EXECUTED: Frontend tests and TypeScript/Vite production build; backend/API tests in the test image.
TEST RESULTS: Frontend 8 tests passed across 3 files; Vite build passed. API/analysis suite: 44 passed, 1 Starlette deprecation warning. Ruff passed on touched backend and audit files. Compose runtime: both project services healthy; HTTP smoke verified 24 monthly rows, transition audit, scenario POST through the frontend proxy, and frontend HTML/bundle availability.
EVIDENCE LEVEL: UNIT/SYNTHETIC + INTEGRATION + LOCAL_RUNTIME
BUSINESS FINDINGS: None added by the scenario; all inputs are hypothetical. Observed monthly baselines come from the existing date-reconstructed ledger.
UNKNOWN:
- Actual recurring revenue, intervention response, causal lift, profit, margin, taxes, or accounting ROI.
BLOCKERS: Browser access remains unavailable from the prior denied visual-QA attempt; no alternate browser boundary was used. Visual browser QA remains UNKNOWN.
RISKS:
- Scenario formulas assume constant monthly user-supplied values over the selected horizon and do not discount or model gross margin.
NEXT STEP: Phase 3 is complete in checkpoint 50; final package status is in checkpoint 51.
