# G4 Challenge 001 — Delivery audit

**Audit date:** 2026-10-22  
**Scope:** local candidate package only; official requirements checked against the current public repository.  
**Result:** PARTIAL — analytically useful, reproducible submission package; causal customer churn, revenue impact and visual browser proof remain unknown. No Git or remote operation was performed.

## Official challenge interpretation

The challenge requests a diagnostic answering root cause, risky segments/specific accounts, and prioritized actions with estimated impact. It also explicitly values five-table integration, verifiable numeric findings, actionable recommendations, correlation/causality separation and CEO readability. Predictive models, dashboards and automation are presented as optional differentiators. The process log is mandatory. See the [requirements matrix](G4-CHALLENGE-REQUIREMENTS-MATRIX.md) and direct source links there.

## Monthly conclusion added

The daily account × `plan_tier` ledger now supplies the primary 24-month executive series (Jan 2023–Dec 2024). It has 24 observed rows, with a valid positive opening denominator for 23 months; January 2023 has no opening customer or plan base and its rates are undefined. All daily and monthly arithmetic bridges close with zero residual.

- Event rows: **73→527**; opening customer exposure **845→3,909 account-months**; event rows per 100 opening account-months **8.64→13.48**.
- Plan-proxy loss events: **6→56**; exposure **1,406→9,414 relation-months**; loss events per 100 relation-months **0.427→0.595**.
- Complete date-derived account coverage-loss episodes: **2→6**; exposure-normalized episodes **0.237→0.153 per 100 account-months**.
- Source usage total: **124,561→125,964 (+1.13%)**; per observed account-month **24.462→24.747 (+1.17%)**. However, **19,142 of 25,000 usage rows precede the linked subscription start**, making adoption-before-loss inference unreliable.

Therefore, the absolute event count increase is partly consistent with much greater exposure, but simple scale does not explain all record/plan-proxy intensity changes. The full-account coverage-loss episode intensity moves in the opposite direction. This is a mixed conditional picture, not evidence that verified customer churn accelerated. A change in event-recording practice cannot be isolated from true event behavior. Plan-tier mix remained near one-third Basic/Enterprise/Pro at year close (2023: 35.29/32.09/32.62%; 2024: 33.38/33.52/33.10%); industry/acquisition compositional decomposition is not available at a valid lifecycle grain.

## Use and customer experience

Usage comparisons are descriptive: raw use grew only 1.13%, source observed account-months stayed 5,092 vs. 5,090, and matched-in-subscription-interval usage records are only 514 in 2023 and 5,054 in 2024. This is not proof of activation or adoption growth because the observation frame disagrees with subscription dates.

For the retrospective any-event label, satisfaction averages were 3.9804 (815 scored tickets) vs. 3.9833 (360); median first response 89 vs. 87 minutes; median resolution 35 hours in both; escalations 71/1,395 (5.09%) vs. 24/605 (3.97%). Overall 825/2,000 satisfaction values are missing. Event labels have no reliable temporal ordering to tickets. These values do not demonstrate CX as cause or protection.

## Economic scenario

Revenue exposure and recurring MRR churn are UNKNOWN. The existing Decision Lab accepts editable generic assumptions and labels effectiveness as an assumed incremental percentage-point lift, not causal uplift. Its low/base/high cases are sensitivity scenarios, not forecasts or confidence intervals. Example arithmetic in the final-answer brief uses 60 *historically affected* accounts as a reference pool, 100 user-supplied units per invitation, 60% uptake, 5 pp assumed lift, 500 units monthly value and six months; the base net result is -600 generic units. This is not historical/current eligibility, observed currency, estimated company ROI or a recommendation to spend. The evaluator should treat the test plan and measurement steps as actionable; financial impact evidence is conditional.

## Validation performed in this continuation

| Check | Current result | Evidence |
|---|---|---|
| Five-table/business-driver generator | PASS | Current isolated JSON output: 500 accounts, 5,000 subscriptions, 25,000 usage rows, 2,000 tickets, 600 events |
| Daily/monthly ledger regeneration | PASS | 731 daily rows, 24 months, 62 plan-proxy loss events, zero daily plan/customer bridge failures |
| Business-driver tests | PASS | `python -m unittest discover -s analysis/business_drivers/tests -v` — 6 passed |
| API and daily ledger tests | PASS | Python 3.12 Docker test target: 34 passed, one upstream Starlette/AnyIO deprecation warning |
| Frontend tests | PASS | `npm test` — 6 passed |
| TypeScript/Vite production build | PASS | `npm run build`; chunks: app 282.35 kB, charts 420.58 kB, icons 16.29 kB; aggregate JS 719.22 kB uncompressed / 198.79 kB gzip. No safe size reduction was demonstrated in this pass. |
| Ruff | PASS | Corrected container-relative invocation; all checks passed |
| Compose configuration | PASS | `docker compose config --quiet` |
| Compose build/runtime | PASS | Isolated project `ravenstack-g4-align`; API 18202 and web 15177 healthy after explicitly setting ports. The default API port 8000 was occupied by an unrelated service and was left untouched. |
| API and frontend-to-API proxy | PASS | Health, daily API and web root returned HTTP 200; proxy returned the exact 24-month ledger JSON. Industry, country and referral monthly segment sums reconcile to each monthly customer and plan opening/closing base. |
| Scenario validation | PASS | Valid assumptions returned expected base net `-600` generic units; uptake 150% rejected with HTTP 422 |
| Browser/viewport visual review | UNKNOWN | Browser safety denial is recorded historically; not bypassed and not retried here; no screenshot claimed |

The first frontend test run revealed missing fields in local mocked response fixtures, which were completed. One API test expected superseded sensitivity arithmetic and was corrected to current scenario semantics. One first-run `unittest discover` invocation found zero pytest-style tests and is not counted; the Docker pytest target ran the tests. A current host pytest attempt could not run because pytest is not installed in the host Python; the pinned Python 3.12 test image ran 34 tests. Ruff initially could not create its cache as the non-root container user; rerunning with `--no-cache` passed. The default-port Compose start initially hit occupied port 8000; this project's services were restarted on 18202/15177 without changing the occupying service. These are recorded as corrections, not hidden.

## Submission package status

- Candidate directory is self-contained at `submissions/thomasleick/`; source files, source CSVs, analytical outputs, README, reports and process log are inside it.
- `solution/README.md` documents reproducing both analyses into the isolated `g4-alignment/` output folders, keeping earlier output artifacts untouched.
- `node_modules` (176 MB), generated `dist` (752 KB), Python caches and bytecode exist locally but are excluded by `.gitignore` and Docker ignore rules. No secret-looking env/token files were found by the scoped filename scan.
- Source dataset hashes remain included in analytical evidence. Raw CSVs are licensed MIT according to the official challenge and the dataset provenance file records attribution; packaging suitability should still be checked by the candidate at PR time.
- Candidate README follows the template structure and leaves unprovided personal details blank rather than inventing them.
- The package has no Git repository or branch. The current mission explicitly disallowed Git effects; the upstream requires a PR, so remote submission and final PR scope review remain unperformed.
- Written process narrative is accepted by the current submission guide; it documents prompt iterations, observed correction and human steering without claiming unverified human activity.

## Remaining gaps

1. Commercially verified customer churn and its causal root cause are not identified.
2. Future-risk scoring is absent by design; historical labels and plan-date cases are not calibrated risk.
3. Recurring revenue, LTV, actual financial impact and intervention effectiveness are unknown.
4. Browser/viewport rendering and screenshots are unknown.
5. Personal candidate details and eventual PR/branch compliance require candidate action once remote Git effects are authorized.

## Artifacts created or updated

- `docs/findings/G4-CHALLENGE-REQUIREMENTS-MATRIX.md`
- `docs/findings/G4-CHALLENGE-FINAL-ANSWERS.md`
- `docs/findings/G4-MONTHLY-CHURN-ANALYSIS.md`
- `docs/findings/G4-CHALLENGE-DELIVERY-AUDIT.md`
- `process-log/checkpoints/45-monthly-growth-churn-analysis.md`
- `process-log/checkpoints/46-g4-alignment-delivery-audit.md`
- `process-log/prompts/008-monthly-churn-addendum.md`
- `process-log/evidence/g4-alignment-runtime.json`

Prior reports and original CSVs were preserved. See checkpoint 46 for final state and commands.
