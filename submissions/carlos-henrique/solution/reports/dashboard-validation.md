# Dashboard Validation

## Result

**Gate: PASS.** The reworked pt-BR local dashboard is functional, comprehensible, deterministic, privacy-safe within the declared anonymous demo contract, and suitable for documentation, video, and final submission. It is not approved for live operations.

## Build and dependency gates

| Gate | Result |
|---|---|
| `npm ci` / dependency resolution | PASS |
| `npm audit --omit=dev` | PASS - 0 vulnerabilities |
| ESLint | PASS - 0 warnings/errors |
| TypeScript strict typecheck | PASS |
| Vitest | PASS - 18/18 |
| Next.js production build | PASS - 10 static routes |
| Playwright responsive smoke | PASS - 36/36 |
| Desktop screenshot run | PASS - 12/12 |
| Python compileall | PASS |
| Full Python pytest | PASS - 130/130 |
| Deterministic data rebuild | PASS - 15 files, 0 differences across two runs |

The production build statically prerendered `/`, `/quality`, `/journeys`, `/graph`, `/watchlist`, `/experiments`, `/governance`, `/demo`, and `/methodology`, plus the not-found route.

## Data and semantic gates

The builder verified the frozen hashes of 25 authorized Phase 3-8 inputs against source commit `3e96b07e9f113c15ec2a9635324054c3e7b27b00`. It then validated all 15 application JSONs.

| Invariant | Result |
|---|---|
| PII-like fields | 0 |
| Raw operational IDs | 0 |
| Account name, email, feedback text | 0 |
| Non-finite JSON values | 0 |
| Prohibited product language | 0 |
| Scores or probabilities | 0 |
| Revenue-at-risk/saved attribution | 0 |
| Automatic actions | 0 |
| Executed experiments or synthetic outcomes | 0 |
| UNSTABLE graph patterns | 0 |
| HIGH same-day-dependency graph evidence | 0 |
| Quarantined event used as behavior | 0 |
| Causal claims | 0 |
| Graph views above 35 nodes/80 edges | 0 |
| Invalid watchlist priorities or queue mixing | 0 |

Anonymous `acct_*` keys appear only in bounded local data records used to select real evidence. The rendered product substitutes controlled profile labels in Portuguese; `acct_*` and pattern keys are never rendered. Unit, smoke, and source-contract tests prevent operational identifiers and PII from entering the interface.

## Metric reconciliation

- 500 anonymous accounts.
- 35,586 processed events.
- 13,927 usable MAIN events.
- 21,659 excluded/quarantined records kept only as quality backlog.
- 4,221 governed journeys.
- 435 promoted ROBUST/SENSITIVE patterns.
- 43 promoted transitions.
- Seven review queues.
- Eight experiment designs, all `UNTESTED`.

These values reconcile to prior governed artifacts. Phase 9 did not modify analytical inputs or recalculate their business logic.

## Route and browser validation

All nine product routes loaded in desktop, tablet, and mobile Chromium profiles. Tests asserted a visible main landmark and demo badge, zero browser console errors, and zero failed local `/data/` requests. Interaction tests covered guided-demo advancement, watchlist evidence, experiment detail, and bounded Cytoscape rendering.

## Visual review

Seven full-page screenshots were regenerated from the localized production app. Human visual review covered homepage, quality, journeys, graph, watchlist, experiments, governance, pt-BR language and accents, typography, labels, tooltips/disclosures, headline number formatting, MRR language, limitations, anonymity, causal wording, overflow, and performance. A contact sheet and detailed overview/graph previews were inspected. The graph density found during review was corrected and the screenshots were recaptured.

Loading, not-found, error, and reusable empty states are present. Empty/error components have unit coverage. Loading behavior was checked through the route structure; network failures are not simulated in the final production screenshot set.

## Scope review

All new or changed repository files are under `submissions/carlos-henrique/`. No raw CSV was added. `node_modules`, `.next`, test results, caches, logs, temporary previews, and TypeScript build metadata are excluded. No push or Pull Request was performed.

## Operational limitations

Authentication, authorization, live backend, live data freshness, production telemetry, external LLM explanations, automated interventions, live experiment execution, and outbound integrations are not implemented. These omissions are explicit product boundaries rather than build defects.
