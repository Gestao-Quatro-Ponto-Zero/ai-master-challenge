CHECKPOINT: 30 — Account vs. Subscription Churn product integration
STATUS: PASS
OBJECTIVE: Serve reconciled evidence through a typed API and render a useful executive investigation in Follow the Evidence.
WORK COMPLETED:
- Added `GET /api/contract-churn` and a Pydantic response contract. Startup computes from original CSVs; event-to-subscription foreign keys are not invented.
- Updated Docker API image copy context for the independent analysis module.
- Added the “Account vs. Subscription Churn” panel in Chapter 02 with logo/contract grain counts, coverage, event timing, reason table, detailed 66-row contract table, reason-filtered event sample, reactivation caveat and explicit limitations.
- Updated UI contract types, API client, rendering tests, responsive grid rules, solution reproduction README and forensic reports.
- Preserved existing four chapters and prior analysis views.
FILES CREATED: None in this checkpoint.
FILES MODIFIED:
- `solution/apps/api/src/main.py`
- `solution/apps/api/src/schemas/contracts.py`
- `solution/apps/api/tests/test_api.py`
- `solution/apps/api/Dockerfile`
- `solution/apps/web/src/App.tsx`
- `solution/apps/web/src/App.test.tsx`
- `solution/apps/web/src/contracts.ts`
- `solution/apps/web/src/lib/api.ts`
- `solution/apps/web/src/styles.css`
- `solution/README.md`
COMMANDS EXECUTED:
- `npm test -- --run`
- `npm run build`
- `docker build --target test -t ravenstack-contract-api-test -f apps/api/Dockerfile .`
- `docker run --rm --name ravenstack-contract-api-test-final ravenstack-contract-api-test`
- Ruff through the API test image; `docker compose config --quiet`.
TESTS EXECUTED: Frontend 6 tests, API 16 tests, TypeScript/Vite build, Ruff.
TEST RESULTS: Frontend 6/6; API 16/16; Ruff passed; build/config passed. One Starlette/AnyIO deprecation warning remains. Vite warns on 681.34 kB minified bundle (190.91 kB gzip); no bundle restructuring was attempted.
EVIDENCE LEVEL: UNIT / BUILD / STATIC API CONTRACT.
BUSINESS FINDINGS: Same as checkpoint 29; the UI preserves conditional/unknown labels.
UNKNOWN: Actual rendered browser interaction because the browser safety surface denied access to the local URL.
BLOCKERS: No code blocker. Browser surface refused the local application request; no workaround or alternate browser was attempted.
RISKS: API returns a 629,567-byte forensic payload; acceptable for this local dataset but would need paging for larger production sources.
NEXT STEP: Run isolated Docker Compose and verify health, API/OpenAPI, frontend HTTP and proxy responses; record browser limitation.
