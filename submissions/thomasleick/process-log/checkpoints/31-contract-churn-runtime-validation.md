CHECKPOINT: 31 — Contract churn runtime validation
STATUS: PARTIAL
OBJECTIVE: Verify the standalone package in an isolated Compose project and exercise real frontend-to-API routing.
WORK COMPLETED:
- Built API and web images using the submission `solution/` directory.
- Started isolated project `ravenstack-contract` on API port 18100 and web port 15174. Existing `ravenstack-historical` services were left running and unchanged.
- Both new service health checks reported healthy.
- API `/api/health`, `/openapi.json`, `/api/contract-churn`, frontend `/`, and web proxy `/api/contract-churn` returned HTTP 200. OpenAPI listed the route; direct API and proxy returned the same 629,567-byte payload and counts (66, 443, 55).
- Attempted browser verification at `http://127.0.0.1:15174/`; the browser security surface denied permission. No alternate surface, raw browser protocol or workaround was used.
FILES CREATED: This checkpoint report and refreshed output artifacts from the reproduction run.
FILES MODIFIED: `process-log/PROGRESS.md` updated after recording all checkpoints.
COMMANDS EXECUTED:
- `API_PORT=18100 WEB_PORT=15174 docker compose -p ravenstack-contract up --build -d`
- `docker compose -p ravenstack-contract ps`
- Python HTTP smoke checks for API, OpenAPI, frontend and proxy.
- Browser navigation attempt; denied by the browser security surface.
TESTS EXECUTED: Runtime health checks and HTTP integration smoke; API/frontend/analytics suites recorded in checkpoint 30/29.
TEST RESULTS: Containers and HTTP/proxy passed. Actual browser rendering and in-browser selection interaction remain UNKNOWN. Docker warned buildx is absent; builds succeeded. No screenshots captured.
EVIDENCE LEVEL: LOCAL_RUNTIME / INTEGRATION; no BROWSER evidence.
BUSINESS FINDINGS: 66 ended subscription rows across 57 continuous accounts; 443 of 472 non-reactivation events coincide with active subscription context; commercial meaning remains unresolved.
UNKNOWN: Rendered visual behavior, actual clicking/filtering in browser, true paid continuity, actual lost revenue and cause.
BLOCKERS: Browser permission denied local application access.
RISKS: Frontend visual integration is supported by Vitest rendering and build plus proxy checks, but the live visual surface was not reviewed. Large API payload and bundle warning remain.
NEXT STEP: A reviewer may open `http://localhost:15174/` to visually inspect the new Chapter 02 panel; reconcile lifecycle semantics with billing/entitlement data before declaring churn KPI.
