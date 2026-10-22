CHECKPOINT: 39 — Daily commercial runtime validation
STATUS: PARTIAL
OBJECTIVE: Validate tests, formatting, Docker build, service health and actual API/frontend proxy behavior.
WORK COMPLETED: Docker test target rebuilt; Ruff passed after one unused assignment was removed and cache was directed to a writable temp path. Rebuilt only the existing RavenStack Compose project `ravenstack-g4-final` on its existing API/web ports. Both containers became healthy. API health, daily analytics endpoint, frontend root and frontend API proxy returned HTTP 200. API and proxy reported the same 62 plan losses and 8 full customer coverage loss events.
FILES CREATED: This checkpoint.
FILES MODIFIED: `solution/analysis/daily_portfolio_churn/engine.py` (removed unused local); API response schema and frontend runtime presentation were updated in Checkpoint 38 to expose boundary snapshots.
COMMANDS EXECUTED: `docker compose config --quiet`; Docker test-target build; `docker run ... ruff check ... && pytest -q ...`; `npm test -- --run`; `npm run build`; `API_PORT=18200 WEB_PORT=15175 docker compose -p ravenstack-g4-final up --build -d`; `docker compose -p ravenstack-g4-final ps`; Python urllib HTTP smoke checks.
TESTS EXECUTED: API + daily-engine pytest; Ruff; frontend Vitest; TypeScript/Vite build; Compose validation; runtime HTTP checks.
TEST RESULTS: Final pytest run: 30 passed with one upstream deprecation warning; Ruff passed; frontend 6/6 passed; TypeScript/Vite build passed; Compose configuration passed; API/web healthy; direct API and frontend proxy passed. Added tests for same-day start boundary snapshots and preserving invalid intervals. Docker warned buildx is absent and legacy builder was used. Initial Ruff call failed due unwritable default cache; rerun with `RUFF_CACHE_DIR=/tmp/ruff-cache` passed. Browser request for local URL was denied by the browser security policy; no workaround was attempted.
EVIDENCE LEVEL: UNIT / SYNTHETIC, INTEGRATION, LOCAL_RUNTIME.
BUSINESS FINDINGS: Runtime API reports 731 daily rows; all hashes/schema are included; 2024-01-01 snapshot is 191 accounts/379 relations versus 190 accounts/374 relations before that date's transitions.
UNKNOWN: Live browser rendering, visual viewport checks, keyboard navigation, commercial meaning of date transitions and any verified revenue measure.
BLOCKERS: Browser security policy explicitly denied navigation to local application.
RISKS: Browser visual behavior is unverified; large Vite bundle warning remains.
NEXT STEP: Publish additive consolidated/CEO reports and update progress.
