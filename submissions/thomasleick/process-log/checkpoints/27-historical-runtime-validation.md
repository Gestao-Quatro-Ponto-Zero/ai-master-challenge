CHECKPOINT: 27 — Historical runtime validation
STATUS: PASS
OBJECTIVE: Verify the date reconstruction, API contracts, frontend rendering and Docker runtime using the current submission package.
WORK COMPLETED:
- Built the API test image and ran the backend/API test suite against real bundled source CSVs.
- Ran Ruff on changed API and historical analysis code.
- Built the frontend and rebuilt/reran the standalone submission Compose services under isolated project `ravenstack-historical` on ports 18000/15173, preserving the previously running `ravenstack-remediation` containers.
- Verified both new containers healthy, API health/OpenAPI/historical endpoint, frontend HTTP 200, and the frontend `/api/historical-churn` proxy payload.
- Browser checked the rendered 2023/2024 summary, monthly gaps, reactivation caveat, cohort dips, Chapter 03 and Chapter 04. Submitted the default scenario through the UI and observed 50 selected accounts, 5 hypothetical retained accounts, 5,000 user-supplied units of cost and UNKNOWN value/net because value input is unset. No browser console errors or document-wide horizontal overflow at 1920 px viewport.
- Recomputed critical snapshots and 2024 logo/subscription exits independently with a separate standard-library snippet; compared all five CSV hashes against preflight.
FILES CREATED:
- `process-log/prompts/003-historical-churn-reconstruction.md`
- `process-log/checkpoints/24-historical-preflight-and-method.md`
- `process-log/checkpoints/25-historical-date-and-cohort-calculations.md`
- `process-log/checkpoints/26-historical-api-and-frontend.md`
- `process-log/checkpoints/27-historical-runtime-validation.md`
FILES MODIFIED:
- `process-log/PROGRESS.md`
COMMANDS EXECUTED:
- `docker compose config --quiet`.
- `docker build --target test -t ravenstack-historical-api-test -f apps/api/Dockerfile .`.
- `docker run --rm --name ravenstack-historical-api-test-run ravenstack-historical-api-test`.
- `docker run --rm --entrypoint ruff ravenstack-historical-api-test check --no-cache /app/apps/api/src/main.py /app/apps/api/src/schemas/contracts.py /app/analysis/historical_churn`.
- `API_PORT=18000 WEB_PORT=15173 docker compose -p ravenstack-historical up --build -d`.
- HTTP checks for `/api/health`, `/openapi.json`, `/api/historical-churn`, frontend `/`, and frontend API proxy.
- Five-file `sha256sum` and independent account/subscription-set verification.
- Browser navigation across all four chapters and a live scenario POST.
TESTS EXECUTED: 5 historical unit tests; 14 API/backend tests; 6 frontend tests; Ruff; TypeScript/Vite build; Docker Compose config/build/runtime; browser smoke test.
TEST RESULTS: 5/5 analytical tests, 14/14 API tests and 6/6 frontend tests passed. Ruff passed. Compose config and both image builds passed; both isolated services became healthy. API and proxy returned identical historical counts. Browser showed the conditional date metrics and scenario output. API tests emitted one Starlette deprecation warning. Docker warned buildx is unavailable; legacy Docker build succeeded.
EVIDENCE LEVEL: LOCAL_RUNTIME / INTEGRATION
BUSINESS FINDINGS:
- Independent date reconstruction: 2023 opening 0; 2024 opening 191 logos and 655 subscriptions; 2025-01-01 date boundary 500 logos and 4,514 subscription rows.
- 2023 classical rate undefined (0/0); 2024 conditional classic logo churn 0/191 = 0%; subscription exits 66/655 = 10.08%.
- 2024 event/flag conflict remains material: 103 opening accounts with non-reactivation events, 49 with account flag true, and 443/472 non-reactivation rows while a subscription is date-active.
UNKNOWN:
- Whether the 0% date-derived 2024 figure is the true company KPI; 2025 actual status; valid retention rate; causal root cause; verified revenue churn.
BLOCKERS: None for local implementation.
RISKS:
- A date-only KPI may understate churn if blank end dates or simultaneous subscription rows do not indicate commercial activity.
- JS bundle-size and Docker buildx warnings remain.
- Browser screenshot was visually inspected in-session but not persisted in the package.
NEXT STEP: Review the consolidated historical report and use the conditional calculation only after business owners reconcile the lifecycle contract.
