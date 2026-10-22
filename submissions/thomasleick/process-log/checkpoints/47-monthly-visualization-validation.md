CHECKPOINT: 47 — Monthly churn visualization and API reconciliation
STATUS: PARTIAL
OBJECTIVE: Make the Jan 2023–Dec 2024 monthly view the immediately visible Chapter 02 primary visualization and validate it against the real monthly endpoint.
WORK COMPLETED:
- Confirmed the 24-month MONTHLY endpoint series and Jan 2023 zero-base null rates.
- Verified the React component renders gross and month-close persistent rates separately for customer coverage and account × plan-tier proxy, plus monthly movement counts and the 24-row evidence table.
- Compared 24 endpoint records and 19 monthly fields against the reproducible monthly CSV; all values matched.
- Found the preexisting local web container was serving a stale bundle without the component; rebuilt only the submission Compose services with isolated ports API 18201 and web 15176, then verified the served bundle includes the monthly chart/table.
- Updated the executive README summary and appended the full 24-month numeric table to the monthly analysis report.
FILES CREATED: solution/apps/web/src/features/monthly/MonthlyChurnView.tsx; process-log/checkpoints/47-monthly-visualization-validation.md
FILES MODIFIED: solution/apps/web/src/App.tsx; solution/apps/web/src/App.test.tsx; solution/apps/web/src/styles.css; README.md; docs/findings/G4-MONTHLY-CHURN-ANALYSIS.md; process-log/PROGRESS.md
COMMANDS EXECUTED: `npm test -- --run`; `npm run build`; `API_PORT=18201 WEB_PORT=15176 docker compose up --build -d`; HTTP GET `/api/health`, `/api/daily-portfolio-churn`, web `/`, and web proxy `/api/daily-portfolio-churn`; Python comparison of endpoint JSON to monthly CSV; Docker Compose status inspection.
TESTS EXECUTED: Frontend Vitest; TypeScript/Vite production build; monthly API/CSV field parity; runtime API/web/proxy smoke checks.
TEST RESULTS: PASS — 2 test files, 6 tests; build PASS; after rebuild, 24/24 monthly rows and 19 fields matched; API health and data endpoint 200; web root and proxy 200; API and web containers healthy; served bundle contains monthly view strings. First Compose attempt with default ports failed because port 8000 was occupied; no unrelated container was stopped or changed. Retried with isolated ports successfully. One post-rebuild parity invocation used the wrong working directory for a relative CSV path and failed before comparison; rerunning with the package path passed.
EVIDENCE LEVEL: UNIT / SYNTHETIC (React tests); INTEGRATION (API-to-CSV parity and web proxy); LOCAL_RUNTIME (Compose health and served bundle).
BUSINESS FINDINGS: Conditional plan-proxy monthly opening-cohort gross loss rate is highest at 9/1,073 = 0.84% in Oct 2024; largest plan-proxy absolute monthly gross loss count is 11 in Dec 2024. Customer full-coverage opening-cohort gross loss rate peaks at 1/149 = 0.67% in Nov 2023 and is 2/385 = 0.52% in Sep 2024 at its 2024 maximum. These are conditional descriptive outputs, not certified churn or statistical trend claims.
UNKNOWN: Desktop/mobile rendered layout, keyboard/focus interaction in the live browser, browser tooltip display behavior, and visual legibility; browser access to localhost was explicitly denied, no screenshot captured.
BLOCKERS: Browser security permission denial prevents visual desktop/mobile QA.
RISKS: Dashboard combines many counts, so screen-reader/browser review remains important. Existing monthly data are conditional date reconstructions with plan tier as proxy.
NEXT STEP: If browser access is later permitted, inspect the five requested viewport sizes; no other code/runtime work remains for this monthly view.
