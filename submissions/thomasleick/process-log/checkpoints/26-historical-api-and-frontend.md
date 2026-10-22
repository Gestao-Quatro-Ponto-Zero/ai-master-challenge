CHECKPOINT: 26 — Historical API and frontend integration
STATUS: PASS
OBJECTIVE: Expose the reproducible historical calculation through the existing API and executive product without changing the original four-chapter structure.
WORK COMPLETED:
- Added `GET /api/historical-churn`; the backend reconstructs from the original CSVs at startup and validates the typed top-level response schema.
- Added the independent module to the API image build context.
- Added typed frontend response definitions and API integration.
- Added a Chapter 02 panel for annual classic logo churn, subscription churn, account/event/flag comparison, monthly date gaps, conditional cohort dips, formula and caveats.
- Updated Chapter 01 to show the 2024 conditional date result alongside its warning; the older event/flag analysis remains intact.
- Updated the standalone solution README with reproduction commands and interpretation guidance.
FILES CREATED:
- None at this checkpoint.
FILES MODIFIED:
- `solution/apps/api/src/main.py`
- `solution/apps/api/src/schemas/contracts.py`
- `solution/apps/api/Dockerfile`
- `solution/apps/api/tests/test_api.py`
- `solution/apps/web/src/App.tsx`
- `solution/apps/web/src/App.test.tsx`
- `solution/apps/web/src/contracts.ts`
- `solution/apps/web/src/lib/api.ts`
- `solution/apps/web/src/styles.css`
- `solution/README.md`
COMMANDS EXECUTED:
- `npm test -- --run` from `solution/apps/web/`.
- `npm run build` from `solution/apps/web/`.
- `docker compose config --quiet` from `solution/`.
TESTS EXECUTED: Frontend Vitest suite and TypeScript/Vite production build.
TEST RESULTS: 6/6 frontend tests passed; TypeScript and Vite build passed. Vite reported the existing bundle-size warning (672.09 kB minified JS; 188.89 kB gzip). Compose config validation passed.
EVIDENCE LEVEL: UNIT / STATIC
BUSINESS FINDINGS: NONE beyond source-data findings in checkpoint 25.
UNKNOWN: Source lifecycle semantics and true churn remain unresolved.
BLOCKERS: None.
RISKS: The UI intentionally displays conditional values; users must not interpret the date model as the validated company KPI.
NEXT STEP: Rebuild and run both Docker services, exercise API/proxy and rendered chapters.
