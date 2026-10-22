CHECKPOINT: 43 — Final tests, build and local runtime
STATUS: PASS
OBJECTIVE: Verify updated analytical outputs, frontend contracts, Docker services and at least one complete frontend-to-backend HTTP path.
WORK COMPLETED: Built the API test target; executed all API and analysis test folders; ran Ruff; rebuilt the frontend; validated Compose; built both services and started only this submission's project under Compose project `solution` on free ports 18201/15176; verified API and web health, frontend root and static assets, daily-ledger endpoint through direct API and Nginx proxy, and valid/invalid scenario requests. Captured compact runtime evidence in `process-log/evidence/final-consolidation-runtime.json`.
FILES CREATED: `process-log/evidence/final-consolidation-runtime.json`.
FILES MODIFIED: Generated `solution/apps/web/dist/` production assets only; source data and analytical outputs were preserved.
COMMANDS EXECUTED: `docker build --target test -f apps/api/Dockerfile -t ravenstack-final-api-tests .`; `docker run --rm ... pytest -q` against API and six analysis test directories; `ruff check src tests` and daily engine in test image; `npm test`; `npm run build`; `docker compose --env-file .env.example config --quiet`; `API_PORT=18201 WEB_PORT=15176 docker compose --env-file .env.example up --build -d`; `docker compose ps`; HTTP checks to `127.0.0.1:18201` and `:15176`.
TESTS EXECUTED: API and all mounted analysis suites; frontend Vitest; Ruff; Vite/TypeScript build; Compose config/build; HTTP integration checks.
TEST RESULTS: 57 tests passed; one upstream Starlette/AnyIO deprecation warning. Frontend: 6/6 passed. Ruff: passed. Build passed. API/web containers healthy. Health, daily API and proxy HTTP 200; daily proxy count matched direct API at 62. Valid scenario returned 200/HYPOTHETICAL; effectiveness 1.5 returned 422.
EVIDENCE LEVEL: LOCAL_RUNTIME, INTEGRATION, UNIT / SYNTHETIC.
BUSINESS FINDINGS: Runtime API reproduced 62 losses; 2024 cohort 7/374 any-time loss (1.8717%), 3/374 close loss (0.8021%), 0/190 account complete-coverage loss; daily bridge checks 0 failures.
UNKNOWN: Actual visual/browser rendering and viewport behavior.
BLOCKERS: The first default-port Compose attempt failed because 8000 was already allocated. Existing RavenStack services were preserved; successful rerun used 18201/15176. Host Python environment lacks pytest/Ruff; tests ran in project test image. First all-test container invocation needed `/app` on PYTHONPATH for business-driver tests; corrected invocation passed.
RISKS: Docker reports Buildx unavailable and used the legacy builder; no build failure. Browser review remains unverified.
NEXT STEP: Complete submission checklist, preserve current evidence and report local-review readiness without claiming a full PASS.
