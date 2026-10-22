# Checkpoint 09 — Scoped remediation and validation

CHECKPOINT: 09 — Remediation & Validation
STATUS: PARTIAL
OBJECTIVE: Correct the independently audited scenario-unit semantics, CLI portability, duplicate-count terminology, visible satisfaction evidence, frontend tests and confirmed accessibility gaps; validate the standalone Docker package and live UI.

## WORK COMPLETED

- Rechecked the workspace and candidate package before writing. The candidate files and parent directories were owned by `thomasleick`; the project workspace was not a Git repository. Existing source CSVs, staging files, initial reports and historical process evidence were preserved.
- Changed scenario output and the frontend to use `user-supplied units`; the API contract defines effectiveness as hypothetical incremental retention lift, not observed causal uplift.
- Made both analytical scripts support `--help`, package-relative CSV defaults, explicit `--data-dir`, and explicit `--output` (stdout when omitted). Reproduced analysis directly from all five packaged CSVs.
- Replaced ambiguous duplicate usage-row reporting with three verified counts: 21 duplicated IDs, 42 rows in duplicate-ID groups, and 21 excess rows.
- Exposed support satisfaction group means, scored-ticket denominators, missing-score counts and the non-temporal, non-causal interpretation in the evidence chapter.
- Added UI/API tests, a production-used scenario helper test, explicit keyboard focus styling, chart data alternatives, status/error semantics, and more legible supporting text. Reduced-motion styling already existed and was retained.
- Built and ran the submission's Docker Compose project in an isolated Compose namespace on ports 15173/18000. The live browser rendered every chapter and submitted a scenario through the frontend proxy. The running API and web containers reported healthy.

## FILES CREATED

- `process-log/checkpoints/09-remediation-validation.md`
- `solution/apps/api/tests/test_analysis_scripts.py`
- `solution/apps/web/src/features/scenario.ts`
- `solution/apps/web/src/scenario.test.ts`
- `solution/apps/web/src/App.test.tsx`

## FILES MODIFIED

- `README.md`
- `docs/findings/executive-report.md`
- `docs/methodology/analysis.md`
- `process-log/PROGRESS.md`
- `solution/README.md`
- `solution/apps/api/Dockerfile`
- `solution/apps/api/src/analytics/engine.py`
- `solution/apps/api/src/main.py`
- `solution/apps/api/src/schemas/contracts.py`
- `solution/apps/api/tests/test_api.py`
- `solution/apps/web/package.json`
- `solution/apps/web/package-lock.json`
- `solution/apps/web/src/App.tsx`
- `solution/apps/web/src/contracts.ts`
- `solution/apps/web/src/styles.css`
- `solution/apps/web/vite.config.ts`
- `solution/scripts/analyze.py`
- `solution/scripts/audit_data.py`

## COMMANDS EXECUTED

- `python3 scripts/audit_data.py --help` — PASS; CLI help lists both data and output options.
- `python3 scripts/analyze.py --help` — PASS; CLI help lists both data and output options.
- `python3 scripts/audit_data.py` and `python3 scripts/analyze.py` from `solution/`, piping JSON to stdout — PASS; current packaged source data reproduced. Analysis reports 500 accounts, 5,000 subscription rows, 25,000 usage rows, 2,000 tickets, 600 event rows, and duplicate counts 21/42/21. Event rows by year remain 73 in 2023 and 527 in 2024.
- `npm test -- --reporter=verbose` from `solution/apps/web` — PASS, 6 tests in 2 files.
- `npm run build` from `solution/apps/web` — PASS (TypeScript and Vite); emits Vite's unresolved >500 kB chunk warning: JS 648.26 kB minified, 183.45 kB gzip.
- `docker build --target test -t ravenstack-api-test -f apps/api/Dockerfile .` from `solution/` — PASS (performed for this remediation image).
- `docker run --rm ravenstack-api-test` — PASS, 12 tests; one third-party Starlette deprecation warning.
- `docker run --rm ravenstack-api-test ruff check --no-cache src tests /app/scripts` — PASS.
- `API_PORT=18000 WEB_PORT=15173 docker compose -p ravenstack-remediation config --quiet` — PASS.
- `API_PORT=18000 WEB_PORT=15173 docker compose -p ravenstack-remediation up --build -d` — PASS; both isolated service images built and services started. Buildx was unavailable and Docker used the legacy builder.
- `docker compose -p ravenstack-remediation ps` — PASS; API and web report healthy on ports 18000 and 15173.
- Browser on `http://localhost:15173/` — PASS for live frontend render, chapter navigation 01–04, visible satisfaction group values and a successful scenario recalculation through the frontend. With 100 eligible, capacity 50, budget 2,500 units, contact cost 100, assumed lift 10 percentage points, value 500 units/month and horizon 3 months, the UI returned 25 selected, 2.5 hypothetical incremental retained accounts, 3,750 units hypothetical value, 2,500 units cost and 1,250 units hypothetical net value. These are scenario arithmetic only.
- Attempted a browser viewport resize using the exposed browser client — NOT COMPLETED; that client did not provide the invoked resize method. No mobile rendering claim is made.

## TESTS EXECUTED

- API tests: 12 passed.
- Ruff: passed.
- Frontend Vitest: 6 passed.
- TypeScript production build: passed.
- Compose configuration/build/runtime: passed; both health checks passed.
- Live frontend-to-API scenario interaction: passed; invalid scenario input returned HTTP 422 in the local integration check performed during this validation run.
- Browser responsive resize: not executed successfully.

## TEST RESULTS

- Scenario monetary formatting does not imply USD; response contract carries a neutral unit label.
- Satisfaction means and scored/missing counts render from the API; the application identifies the all-time grouping as non-temporal and non-causal.
- Duplicate metrics now distinguish duplicate IDs, rows in duplicated groups and excess rows, with source-data values reproduced.
- All four chapters rendered from the live backend-connected application. Screenshot evidence was captured from the running Chapter 02 application in the active browser session; no fabricated or synthetic screenshot was created.
- No original CSV, upstream challenge file, historical process record, Git state or unrelated container was modified.

## PROCESS NOTES

- AI tool: Codex in the current project workspace; browser checks used the connected in-app browser against the local Compose frontend.
- Prompt reference: the user's “RavenStack Remediation & Validation” scoped-write instructions in this conversation.
- Human decision: the user explicitly authorized this write phase. No other human intervention or approval is claimed.
- Agent decisions: retain the independent project root; use a named Compose project and unused local ports so existing application containers remain untouched; preserve historical evidence; label generic scenario units rather than implying a currency; do not create predictive or causal claims unsupported by the CSVs.
- Mistakes and corrections: an initial CLI-output summarizer expected a different JSON shape and printed null values; the output was inspected and parsed again using its actual nested keys, yielding verified counts. The browser's accessible-role click timed out despite finding the visible submit button; retrying through the visible submit selector completed the live scenario. A browser viewport resize method was unavailable, so no mobile-rendering result is claimed. A browser wait call without its required state parameter failed; the chapter was read directly after navigation instead. An early TypeScript build reported a stale `ScenarioForm` type reference; it was corrected before the passing production build. No historical process entries were rewritten.
- Remaining limitations: see `UNKNOWN`, `BLOCKERS` and `RISKS` below.

## EVIDENCE LEVEL

UNIT / SYNTHETIC for UI fixture tests; INTEGRATION for API contract and proxy scenario; LOCAL_RUNTIME for Compose health, browser-rendered chapters and scenario calculation; STATIC for narrow-screen CSS review only.

## BUSINESS FINDINGS

- Current source CSV reproduction confirms 600 event rows (73 in 2023, 527 in 2024), 352 unique event accounts, and 110 `churn_flag=True` rows/accounts in the account table; the flag/event mismatch affects 312 of 500 accounts (277 event-history accounts with false flag; 35 flagged accounts without events).
- Support tickets with recorded satisfaction average 3.980/5 across 815 scored tickets in event-history accounts and 3.983/5 across 360 scored tickets in accounts without an event row. There are 580 and 245 missing scores respectively. The grouping is all-time, not aligned to a pre-event window, and does not establish causality.
- These source tables do not establish logo churn rates, subscription churn rates, recurring revenue loss/exposure, calibrated account risk or causal intervention uplift. Those remain UNKNOWN.

## UNKNOWN

- Narrow-screen rendered behavior was not independently verified in this browser session.
- No risk prediction, defensible revenue-at-risk estimate or causal intervention impact is established.
- No automated browser E2E suite or assistive-technology audit was performed.

## BLOCKERS

- No blocker to the local remediation or runtime validation. GitHub fork identity/availability and remote publication are outside this authorized phase and were not attempted.

## RISKS

- Frontend production JS remains above Vite's 500 kB chunk warning threshold.
- One third-party deprecation warning remains in API test output.
- The dataset is synthetic and has severe lifecycle/time inconsistencies; recommendations prioritize data reconciliation and a future controlled test, not a broad save campaign.
- The browser resize limitation means responsive behavior was not runtime-demonstrated here.

## NEXT STEP

Review the recorded scoped diff and, if desired, authorize separate work to reduce the bundle and perform an actual narrow-screen/browser-accessibility review. No Git, publication, PR or deployment effect was performed.
