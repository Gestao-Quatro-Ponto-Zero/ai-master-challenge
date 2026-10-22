# Checkpoint 10 — Final responsive visual QA

CHECKPOINT: 10 — Final Visual QA
STATUS: PASS for the tested visual matrix; screenshot-file delivery PARTIAL due browser-tool path restrictions.
OBJECTIVE: Inspect the actual running frontend at the five requested viewport sizes, test all four chapters and interactive controls, correct only reproducible visual defects, then rerun frontend and Docker verification.

## WORK COMPLETED

- Preflighted `/home/thomasleick/the_churn_paradox/` and the candidate package. Both paths are owned by `thomasleick`; the workspace is not a Git repository. Existing isolated Compose project `ravenstack-remediation` had healthy API and web containers. No unrelated project containers were stopped or modified.
- Used Playwright against `http://localhost:15173/` and tested each chapter at 1440×900, 1366×768, 768×1024, 390×844 and 320×568.
- Corrected four reproducible responsive issues in `solution/apps/web/src/styles.css` and `solution/apps/web/src/App.tsx`:
  1. Chapter 03 grid children inherited intrinsic minimum widths from its 650 px account table, expanding the page to 746 px at 390 px and 967 px at 768 px. Responsive grid items now have `min-width: 0`, leaving the wide table inside its own scroll container.
  2. At 320 px, topbar metadata extended the document to 344 px. The metadata is hidden at widths up to 360 px; the document now fits exactly 320 px.
  3. Numeric scenario input for assumed percentage-point lift collapsed to zero width at 320 px because its `percentage points` suffix could not wrap. Form fields now stack under 1050 px and narrow suffixes wrap; the narrowest input measured 134 px at 320 px.
  4. The fixed chart tick interval caused month labels to overlap at 390 px and 320 px. Recharts now uses `preserveStartEnd`, which reduces mobile labels while retaining chart data and avoids overlap.
- Tested keyboard navigation: the second chapter button received the explicit 3 px gold `:focus-visible` outline.
- Tested the segment dropdown at 320 px, selected plan tier, and observed the three plan rows render without page-wide overflow.
- Submitted the Decision Room scenario at 320 px using the UI. The API response rendered 25 selected accounts, 2.5 hypothetical incremental retained accounts, and 3,750 / 2,500 / 1,250 user-supplied units for hypothetical value, cost and net value.

## FILES CREATED

- `process-log/checkpoints/10-final-visual-qa.md`

## FILES MODIFIED

- `process-log/PROGRESS.md`
- `solution/apps/web/src/App.tsx`
- `solution/apps/web/src/styles.css`

Vite also regenerated ignored build output under `solution/apps/web/dist/` and `solution/apps/web/tsconfig.tsbuildinfo` during verification.

## COMMANDS EXECUTED

- Filesystem ownership and package inventory via `stat` and `find` — PASS; candidate project files are owned by `thomasleick`.
- `git -C /home/thomasleick/the_churn_paradox rev-parse --show-toplevel` — returned “not a git repository”; no Git mutation followed.
- `docker compose -p ravenstack-remediation ps` — PASS; API and web healthy before and after the final build.
- `npm test -- --reporter=verbose` from `solution/apps/web` — PASS, 6 tests in 2 files.
- `npm run build` from `solution/apps/web` — PASS; TypeScript and Vite succeeded. Vite still warns about the 648.28 kB minified JS chunk (183.45 kB gzip).
- `API_PORT=18000 WEB_PORT=15173 docker compose -p ravenstack-remediation up --build -d` from `solution/` — PASS; final web image rebuilt and both isolated services started healthy. Docker used its legacy builder because Buildx is not installed.
- Browser viewport matrix — PASS for all specified widths and heights; each of four headings was confirmed at each viewport. `document.documentElement.scrollWidth` did not exceed the viewport. At 390 px and 320 px, chart month-label text bounding boxes did not overlap. Wide tables overflow only within their horizontal-scroll wrappers.
- Browser scenario interaction at 320 px — PASS; UI rendered the actual local API scenario response in user-supplied units.

## TESTS EXECUTED

- Frontend Vitest: 6 passed.
- TypeScript and production Vite build: passed, with bundle warning.
- Docker Compose image build and runtime health: passed.
- Playwright: all four chapters at five viewports; segment selection at 320 px; scenario submission at 320 px; keyboard focus indicator at 390 px.

## TEST RESULTS

| Viewport | All 4 chapters | Page horizontal overflow | Chart | Tables | Decision controls |
|---|---|---|---|---|---|
| 1440×900 | PASS | None | Rendered; labels did not overlap | Fit | Inputs visible |
| 1366×768 | PASS | None | Rendered; labels did not overlap | Wide evidence table scrolls inside wrapper | Inputs visible |
| 768×1024 | PASS | None | Rendered; labels did not overlap | Wide tables scroll inside wrappers | Minimum input width 161 px |
| 390×844 | PASS | None | 271 px chart; six labels; no overlap | Scroll inside wrappers | Minimum input width 153 px |
| 320×568 | PASS | None | 216 px chart; four labels; no overlap | Scroll inside wrappers | Minimum input width 134 px; scenario submitted |

- Mobile navigation, controls, chapter content and data tables remain within the viewport; the page scrolls vertically as expected.
- The segment select updated to `plan_tier` and displayed Basic/Pro/Enterprise data at 320 px.
- No analytical code, scenario arithmetic, source data or business conclusions were changed.

## TEST FAILURES AND CORRECTIONS

- A rapid browser-action loop checked for the previous chapter's already-visible heading before React had committed navigation, so it returned stale chapter state. That run was stopped and replaced with sequential chapter changes that waited briefly and asserted each resulting heading before recording metrics.
- One accessibility-role click timed out while Playwright waited for the chapter button to become stable. A later click on the same visible navigation button succeeded; DOM state was checked after each transition.
- The first segment-select locator attempt happened while Chapter 01 was still rendered and therefore correctly matched no element. After explicitly switching to Chapter 02 and verifying its heading, Playwright selected `plan_tier` and confirmed the output rows.
- Saving a screenshot to the candidate evidence path was rejected by the browser tool's allowed-root check. The path was not redirected to an unauthorized location; screenshots remain tool output only.

## SCREENSHOTS

- One actual 320×568 diagnostic screenshot was captured before the fixes and displayed the original clipping/overflow defect.
- One actual desktop screenshot (1920×903 browser viewport) was captured after the final build and showed the live application with API data.
- Final-size screenshots could not be persisted in the candidate evidence folder. The Playwright screenshot tool denied writes outside its configured roots (`/home/thomasleick/LeickOS` and its `.playwright-mcp` output directory). Mobile post-fix evidence is therefore the actual viewport DOM/geometry and interaction results above, not a screenshot file.

## EVIDENCE LEVEL

LOCAL_RUNTIME: Dockerized API/frontend, Playwright viewport testing, live chapter navigation, table/segment interaction and mobile scenario submission. UNIT / SYNTHETIC: frontend Vitest fixtures.

## BUSINESS FINDINGS

BUSINESS FINDINGS: NONE. This visual QA did not change or extend the analytical conclusions.

## UNKNOWN

- Assistive technology behavior was not tested.
- Final mobile screenshot files are absent because the browser tool cannot write into the candidate path; narrow viewport behavior was nevertheless inspected in the actual rendered browser.
- The production JS bundle still exceeds Vite's advisory 500 kB chunk threshold.
- Analytical limitations recorded in prior checkpoints remain unchanged.

## BLOCKERS

- No blocker to visual fixes or local validation. The browser screenshot writer's allowed-root restriction prevented saving evidence images inside the submission. No workaround was attempted outside the authorized boundary.

## RISKS

- Browser automation generated its managed snapshots and diagnostic screenshot in its configured `.playwright-mcp` tool-output area under the active LeickOS browser workspace. No project source outside the candidate package was intentionally edited; tool-managed outputs were not deleted.
- Mobile tests verify one Chromium/Playwright rendering environment; they do not establish behavior in every browser or with assistive technology.
- Vite bundle-size warning remains.

## NEXT STEP

Review the visual corrections and the remaining bundle warning. No Git initialization, branch, commit, push, PR, deployment or change to unrelated containers occurred.
