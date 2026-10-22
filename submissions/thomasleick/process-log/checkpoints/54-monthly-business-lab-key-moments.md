CHECKPOINT: 54 — Monthly Business Lab & Key Moments
STATUS: PARTIAL
OBJECTIVE: Consolidate the existing monthly ledger view and scenario laboratory with deterministic, selectable Key Moments; preserve the executive paper and historical analysis.

INITIAL STATE:
- Workspace: `/home/thomasleick/the_churn_paradox/`; write scope: `submissions/thomasleick/`.
- Candidate package has no Git metadata. Directories and reviewed files were owned by `thomasleick`; no uncertain overlapping changes were identified.
- Project Compose services were already running under Compose project `solution`, using API host port 18201 and web host port 15176; both were healthy. They were rebuilt/recreated as this project's own services only.
- Five raw CSV SHA-256 values matched the daily-ledger metadata exactly.
- Paper source/PDF were preserved and not modified.

WORK COMPLETED:
- Reused the daily account × plan-tier proxy ledger, the existing monthly API response, Chapter 02 monthly charts/table and the existing Monthly Business Lab. Added no second churn engine or endpoint.
- Added deterministic `key_moments.py` selectors to the existing API payload. Selectors include rate peak, gross loss-volume peak, acquisition changes, recovery, portfolio contraction/possible downgrade, rate-versus-volume divergence and largest event/date-lifecycle discrepancy. Ties are retained; zero-base rates are excluded; the criteria explicitly do not claim statistical significance.
- Added typed API/UI contracts, monthly selected-period comparison, chart highlighting, linked movement/account and segment detail, and a Key Moment → same-month lab action.
- Preserved OBSERVED as an immutable date-reconstructed baseline and SCENARIO as hypothetical API-calculated inputs. Existing plan transition audit remains separate; possible upgrades/downgrades are not treated as confirmed migrations or added as extra churn.
- Added evaluator instructions to the submission README and a focused report at `docs/findings/MONTHLY-BUSINESS-LAB-KEY-MOMENTS.md`.
- Rebuilt the project's Compose services and executed HTTP checks against the running app and frontend proxy.

REAL DATA FINDINGS VERIFIED:
- 24 monthly periods are served; Jan 2023 rates are null/UNDEFINED due to zero opening population.
- Oct 2024 is `RATE_PEAK`: 9 / 1,073 = 0.83877% (display 0.84%), conditional plan-level proxy.
- Dec 2024 is `LOSS_VOLUME_PEAK`: 11 gross relation-loss events. Separately, opening-cohort losses are 5 / 1,279 = 0.39093% (display 0.39%).
- The API currently emits 18 selectable moments over all 7 supported types. These are deterministic descriptive selectors, not significance results.
- All five current CSV hashes match the metadata recorded in the ledger artifact.

FILES INSPECTED:
- `solution/analysis/daily_portfolio_churn/engine.py`, `outputs/g4-alignment/daily-portfolio-churn.json`, `key_moments.py`
- `solution/apps/api/src/main.py`, schemas, tests, Dockerfile
- `solution/apps/web/src/contracts.ts`, `App.tsx`, `App.test.tsx`, `features/monthly/MonthlyChurnView.tsx`, `features/monthly-lab/MonthlyBusinessLab.tsx`, styles, package scripts
- `solution/compose.yaml`, README, prior checkpoint 53, paper and process log
- All five original CSVs and source hashes

FILES CREATED:
- `docs/findings/MONTHLY-BUSINESS-LAB-KEY-MOMENTS.md`
- `process-log/prompts/012-monthly-business-lab-key-moments.md`
- `process-log/checkpoints/54-monthly-business-lab-key-moments.md`

FILES MODIFIED:
- `README.md`
- `solution/analysis/daily_portfolio_churn/key_moments.py`
- `solution/apps/api/src/main.py`
- `solution/apps/api/src/schemas/contracts.py`
- `solution/apps/api/tests/test_api.py`
- `solution/apps/web/src/contracts.ts`
- `solution/apps/web/src/features/monthly/MonthlyChurnView.tsx`
- `solution/apps/web/src/features/monthly-lab/MonthlyBusinessLab.tsx`
- `solution/apps/web/src/App.tsx`
- `solution/apps/web/src/App.test.tsx`
- `solution/apps/web/src/styles.css`
- `process-log/PROGRESS.md`

FILES PRESERVED: Original five CSVs, existing analytical outputs/reports, official paper/PDF, prior checkpoint sequence, existing transition audit and unrelated projects.

COMMANDS EXECUTED:
- SHA-256 verification of all five CSVs against `daily-portfolio-churn.json` metadata — all matched.
- `docker build -f apps/api/Dockerfile --target test -t ravenstack-api-tests:local .` — succeeded.
- `docker run --rm ravenstack-api-tests:local` — 45 passed; one upstream Starlette deprecation warning.
- `docker run --rm -e RUFF_CACHE_DIR=/tmp/ravenstack-ruff --entrypoint ruff ravenstack-api-tests:local check src/main.py src/schemas/contracts.py tests/test_api.py /app/analysis/daily_portfolio_churn/key_moments.py` — all checks passed. An initial Ruff invocation without writable cache failed; retry with `/tmp` cache passed.
- `npm test -- --reporter=dot` — 3 files, 9 tests passed.
- `npm run build` — TypeScript/Vite passed; output: main JS 324.71 kB, chart chunk 420.59 kB.
- `docker compose config -q` — passed.
- `API_PORT=18201 WEB_PORT=15176 docker compose -p solution up --build -d` — both images built; both project services healthy.
- HTTP smoke checks: API health 200; direct daily endpoint 200; frontend 200; frontend proxy `/api/daily-portfolio-churn` 200 with 24 months and key moments.
- Scenario POST through frontend proxy for Oct 2024 — 200 `SCENARIO_ONLY`; observed acquisition count 23 remained fixed in baseline while scenario count was 24; returned modeled figures under user assumptions. Invalid 999,999 customer-loss input returned 422.
- Browser open attempt through approved in-app browser was rejected by browser security policy because permission was denied. No alternate browser, raw Playwright, CDP or workaround was used.

TEST RESULTS:
- Analytics/API: 45 passed.
- Ruff: passed.
- Frontend: 9 passed.
- TypeScript/Vite: passed.
- Compose config/build/runtime and HTTP proxy/scenario smoke: passed.
- Browser visual exercise and screenshots: UNKNOWN / not performed due explicit browser security denial.

EVIDENCE LEVEL: UNIT / SYNTHETIC; INTEGRATION; LOCAL_RUNTIME. Browser visual evidence is absent.

RISKS:
- Reconstructed relations remain plan-tier proxies conditioned on subscription date semantics.
- Candidate transitions are not confirmed migration events; financial revenue churn remains UNKNOWN.
- The existing scenario model is arithmetic under user assumptions, not causal uplift or observed revenue.
- Browser visual QA remains outstanding; automated frontend tests/build and runtime HTTP do not prove rendered visual behavior.

NEXT STEP: Human may review the local application visually if the browser permission policy permits it; no Git or remote operation was performed.

PAPER_MODIFIED: NO
GIT_EFFECTS: NONE
REMOTE_EFFECTS: NONE
