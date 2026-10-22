# RavenStack — G4 Submission Readiness

**Audit date:** 2026-10-22 · **Mode:** local scoped implementation and verification

## Decision

**Status: PARTIAL — locally reviewable package; not yet submitted.** The package has the expected candidate folder structure, source data, runnable Compose project, API/UI, executive reports and written process log. Current tests and local runtime checks pass. Submission is not marked complete because the current visual browser review is UNKNOWN, the commercial customer-churn KPI is not identifiable from the data, and the required fork/branch/commit/push/PR workflow has not been executed (those remote/Git actions were explicitly prohibited in this phase).

## Official challenge compliance matrix

| Official requirement | Candidate artifact / evidence | Status | Remaining issue |
|---|---|---|---|
| Investigate the root cause by crossing all five datasets | API analyses and findings under `solution/analysis/`; G4 consolidated report; four-chapter app | PARTIAL | Five tables are used, but no causal root cause is identifiable. This is stated directly. |
| Identify segments and specific accounts | Daily plan-tier summary, 60 account movement candidates, 8 full-coverage gap-return timelines, segment tables | PARTIAL | These are descriptive, date-conditional records, not validated future-risk candidates. |
| Give concrete prioritized actions with impact estimate | Decision Room, scenario engine, 30/60/90 plan, conditional generic-unit simulator | PARTIAL | Actual revenue impact and causal intervention uplift are UNKNOWN. Scenario estimates are editable assumptions, not a measured impact. |
| Show verifiable numbers and methodology | Deterministic modules, tests, JSON/CSV outputs, current runtime evidence | PASS for stated calculations | Business semantics of source dates remain conditional. |
| Distinguish correlation and causation | App, README and analytical reports state no causal driver is established | PASS | None; maintain this wording if future metrics are added. |
| Executive can read and act | Four guided chapters; direct Q1/Q2/Q3 answer cards; CEO brief | PARTIAL | Test/browser surface did not provide current visual proof; business KPI remains unknown. |
| Process log included | `process-log/PROGRESS.md`, checkpoints 01–44, prompt references, evidence JSON and iterations narrative | PASS (written narrative route) | No screenshots, screen recording or chat export are included; the official guide accepts a written narrative. |
| Candidate-only submission scope | All created/modified artifacts from this execution are under `submissions/thomasleick/` | PASS for this execution | No Git diff is available because the standalone workspace has no Git repository. |
| README follows official template | Candidate README has identity fields without invented values, executive summary, solution, approach, findings, recommendations, limits, AI process log and evidence | PASS with known omissions | Display name/LinkedIn were not supplied; no submission date or PR link exists. |
| Reproducible application setup | `solution/compose.yaml`, pinned dependency files, Dockerfiles, CSVs and `solution/README.md` | PASS from package root with available ports | Default 8000/5173 ports were occupied in this environment; a verified override used 18201/15176. |

## Package and provenance

- Workspace: `/home/thomasleick/the_churn_paradox/`.
- Candidate package: `/home/thomasleick/the_churn_paradox/submissions/thomasleick/`.
- CSV files: all five are present in `solution/data/raw/`.
- SHA-256 hashes rechecked in this run and copied into `process-log/evidence/final-consolidation-runtime.json`.
- Docker contexts resolve inside `solution/`; the API image copies the five source CSVs and required processed analytical artifacts. Runtime does not depend on `/tmp`, a parent-workspace data directory, external database, secret or paid API.
- Root wrapper compose file is outside the submission package and is not required. Run Compose from `submissions/thomasleick/solution/`.
- Existing prior reports, historical checkpoints and CSVs were preserved. No cleanup of ignored build output, `node_modules` or Python caches was performed.
- No Git repository exists at the workspace root; no branch or HEAD is available. Git initialization was not run.

## Test and runtime matrix

| Check | Command / evidence | Result |
|---|---|---|
| Daily ledger reproduction | `PYTHONPATH=analysis python -m daily_portfolio_churn --data-dir data/raw --output-dir /tmp/ravenstack-final-verify` | PASS; 731 rows, 62 plan losses, 60 accounts, 0 daily plan bridge failures, 0 customer bridge failures |
| API + analytical unit tests | Built API test target, then ran all API and analysis test directories in an isolated container with read-only mounts | PASS; 57 tests; 1 upstream Starlette/AnyIO deprecation warning |
| Frontend tests | `npm test` from `solution/apps/web/` | PASS; 6/6 |
| TypeScript and production build | `npm run build` from `solution/apps/web/` | PASS; Vite chunks app 269.63 kB, charts 420.58 kB, icons 16.29 kB |
| Ruff | `ruff check src tests` in API test image and daily engine | PASS; cache redirected to `/tmp/ruff-cache` because runtime image user cannot write under `/app` |
| Compose syntax | `docker compose --env-file .env.example config --quiet` | PASS |
| Images | `docker compose --env-file .env.example up --build -d` with port overrides | PASS; API and web images built. Docker warns Buildx is not installed and uses legacy builder. |
| Compose health | `docker compose ps` | PASS; API and web healthy |
| API / frontend proxy | HTTP health, daily endpoint and web `/api/daily-portfolio-churn` | PASS; 200 and direct/proxy plan-loss counts match |
| Scenario | Valid POST and invalid effectiveness >1 | PASS; valid hypothetical response 200, invalid request 422 |
| Browser / viewport review | Not performed in current run; local browser safety surface previously denied access and was not retried | UNKNOWN; no screenshot claimed |
| Default ports | First Compose attempt on 8000/5173 | BLOCKED by ports already allocated to other existing RavenStack containers; those containers were preserved. Verified current run uses 18201/15176. |

## Visual and process evidence

Visual styles include responsive breakpoints, chart text alternatives, visible keyboard focus, table captions and reduced-motion CSS under static source inspection. The React tests navigate across all four chapters; this is not a rendered-browser visual review. Do not claim current viewport PASS or attach synthetic screenshots.

The official process-log guide permits written narrative as an evidence format. The package includes a chronological narrative, prompt references, mistakes/corrections and test checkpoints. The independent candidate should review these statements before external submission. Browser screenshots and chat exports are absent.

## Outstanding items before the official submission

1. Review the CEO brief and README for candidate-authored accuracy.
2. If available, have a human reviewer verify the browser presentation on desktop and mobile; retain the current UNKNOWN status until then.
3. Keep customer churn, validated retention, recurring-revenue exposure and causal intervention impact marked UNKNOWN until supported by operational data.
4. Once separately authorized, execute the official fork/branch/commit/push/PR process. The official contribution process requires one candidate folder, the README template, a process log, code setup instructions and no changes outside that folder.

## Official references checked

- [Challenge 001 — Diagnóstico de Churn](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/blob/main/challenges/data-001-churn/README.md)
- [Contributing / submission rules](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/blob/main/CONTRIBUTING.md)
- [Submission guide](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/blob/main/submission-guide.md)
- [Submission README template](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/blob/main/templates/submission-template.md)


## Addendum — G4 alignment and monthly analysis (2026-10-22)

The current official challenge README, contribution rules, submission guide and template were checked. The new [requirements matrix](G4-CHALLENGE-REQUIREMENTS-MATRIX.md) marks required root cause, segment/account risk and estimated impact as PARTIAL where source evidence is insufficient; optional prediction is not a gate. Written process narrative is accepted by the submission guide. The monthly analysis is reproducible in `solution/analysis/daily_portfolio_churn/outputs/g4-alignment/`; business-driver outputs are isolated alongside. Current tests and isolated Compose API/web integration passed, but browser review remains UNKNOWN. The standalone package is locally ready for candidate review; remote PR and final Git diff cannot be checked until Git operations are separately authorized. Detailed status: [G4-CHALLENGE-DELIVERY-AUDIT.md](G4-CHALLENGE-DELIVERY-AUDIT.md).
