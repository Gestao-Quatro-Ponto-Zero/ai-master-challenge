CHECKPOINT: 07 — Docker integration and runtime validation
STATUS: PASS (local application); remote fork remains blocked independently
OBJECTIVE: Build both images, start services with the exact root command, and verify runtime, API, frontend proxy, scenario safety, browser rendering and restart determinism.
WORK COMPLETED:
- Added a workspace-root Compose include that resolves the portable candidate package configuration and its build contexts.
- Built a locked Python 3.12 API runtime image and a React/Vite build served by non-root Nginx on port 5173.
- API is exposed on 8000; frontend proxies /api and OpenAPI to the API service. Health dependency is active.
- Visited the actual running app in Chrome. Verified all four chapter navigation targets, current support comparison, account/revenue exposure view, 30/60/90-day plan and Decision Room calculation.
- Verified a 390×844 responsive viewport: document width 375 px, with no horizontal overflow.
- Restarted the final containers and compared SHA-256 of /api/analysis before/after; outputs were identical.
FILES CREATED: solution/.dockerignore, solution/apps/web/.dockerignore, solution/apps/web/nginx-main.conf, root compose.yaml invocation wrapper, and current API runtime evidence in process-log/evidence/.
FILES MODIFIED: solution/compose.yaml, API/web Dockerfiles and sources; all submission files remain under submissions/thomasleick/.
COMMANDS EXECUTED:
- docker compose config --quiet — passed from workspace root.
- docker compose up --build — passed from /home/thomasleick/the_churn_paradox; both images built and services started.
- docker compose ps — both services reported healthy after health checks.
- HTTP GET /api/health, /, /api/analysis via frontend proxy, /openapi.json — all returned 200.
- POST /api/scenarios/retention — valid assumptions returned 200/HYPOTHETICAL; effectiveness 1.5 returned 422.
- docker compose restart followed by the same API GET — response SHA-256 unchanged: 47b61db47aa47687246dfe1f627358b1d57660244314e304f2e640196c80ec88.
- Browser runtime navigation, scenario recalculation, console check and 390×844 responsive check.
TESTS EXECUTED: API pytest 7/7; Ruff all checks passed; frontend Vitest 2/2; npm audit 0 vulnerabilities; manual HTTP/browser integration.
TEST RESULTS: Both final containers started. API, web and scenario paths returned expected status/results. No browser console errors. App remained usable through restart. Image build emitted a Vite large-chunk advisory (645.85 kB JS / 182.85 kB gzip); no build failure. Docker warned Buildx is absent and used its supported fallback builder.
EVIDENCE LEVEL: LOCAL_RUNTIME.
BUSINESS FINDINGS: NONE.
UNKNOWN: Full assistive-technology evaluation was not run. The visual browser screenshot was inspected during this execution but not saved as a submission artifact. No deployment was performed.
BLOCKERS: None for local runtime. GitHub fork remains BLOCKED_AUTHENTICATION from checkpoint 01; it does not affect this local validation.
RISKS: Keep the backend UNKNOWN metrics and hypothetical scenario labels visible. The Vite bundle-size advisory remains.
NEXT STEP: Complete final submission package scope and G4 readiness review; leave Git operations pending separate authorization.
