CHECKPOINT: 35 — Final customer churn validation  
STATUS: PARTIAL  
OBJECTIVE: Validate analytics, API, frontend build/tests and isolated Docker runtime.  
WORK COMPLETED: Re-ran source hashes; all analysis modules passed; Ruff passed in API test image; built current standalone package using isolated ports and project name `ravenstack-g4-final`; queried services and scenarios.  
FILES CREATED: Final reports `docs/findings/G4-CUSTOMER-CHURN-FINAL.md`, `docs/findings/G4-CEO-FINAL-BRIEF.md`; generated new analysis JSON/CSV artifacts.  
FILES MODIFIED: Existing API, Dockerfile and frontend integration files listed in checkpoint 34; final report/progress records.  
COMMANDS EXECUTED: Five analysis `unittest discover` commands; `docker build --target test -f apps/api/Dockerfile ...`; `docker run ... ruff check ... && pytest -q && python -m unittest ...`; `npm test -- --run`; `npm run build`; `docker compose config --quiet`; `API_PORT=18200 WEB_PORT=15175 docker compose -p ravenstack-g4-final up --build -d`; Python urllib requests to API/web/proxy/scenario; `docker compose ps`; `sha256sum`.  
TESTS EXECUTED: G4 analysis 5; historical 5; contract 5; conventional 8; business drivers 4; API pytest 17; frontend 6.  
TEST RESULTS: All passed after corrections. Ruff passed. One Starlette/AnyIO deprecation warning; Docker notes missing buildx but legacy builds succeeded. `npm run build` passed with Vite bundle warning (687.34 kB minified / 192.07 kB gzip). An initial broad unittest invocation placed `business_drivers` outside its required `solution/` import root and failed with `ModuleNotFoundError`; rerunning that test from `solution/` passed 4/4. An initial Ruff call used the non-writable default cache as UID 10001 and failed; rerunning with `RUFF_CACHE_DIR=/tmp/ruff-cache` passed. These were command-environment issues, not hidden test failures.
EVIDENCE LEVEL: UNIT / SYNTHETIC, INTEGRATION, LOCAL_RUNTIME.  
BUSINESS FINDINGS: API `/api/g4-customer-churn` returns C — NOT IDENTIFIABLE; 2024 diagnostic 0/191; 103 opening accounts with 2024 non-reactivation labels; 443/472 rows with active subscription by date. Proxy returns identical 94,214-byte JSON. Valid scenario HTTP 200/HYPOTHETICAL; invalid input HTTP 422. Both services healthy.  
UNKNOWN: Live browser visual state, responsive viewport rendering and screenshots; historical customer churn truth, validated cohort retention, causal drivers and financial churn.  
BLOCKERS: Browser visual review not claimed; no safe available browser evidence in this run.  
RISKS: Bundle size warning; conditional business outputs remain easy to misread despite explicit labels.  
NEXT STEP: Review final CEO brief; continue lifecycle source remediation before any operational churn-targeted campaign.
