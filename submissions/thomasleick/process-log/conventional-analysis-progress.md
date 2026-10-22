# Conventional analysis progress

**Current checkpoint:** 14 — standalone analysis complete; product integration not demonstrated.  
**Workspace:** `/home/thomasleick/the_churn_paradox/`  
**Submission package:** `submissions/thomasleick/`  
**Git effects:** none; workspace remains outside Git.

## Completed in this scoped phase

- Preserved all five source CSVs and existing product/history.
- Created an isolated, standard-library Python analysis under `solution/analysis/conventional/`.
- Reconciled account flag, any event, non-reactivation event, and subscription-flag definitions; the 312 mismatch count is specifically account flag vs any-event membership.
- Generated profiles, per-label segment tables and intervals, account event-volume records, usage/support/revenue comparisons, SVG visualizations, and standalone executive report.
- Added eight tests over source row counts/hashes, labels, cardinality, duplication, dates, support missingness, financial sums, Wilson intervals, deterministic bootstrap and rejection of unsupported rates/probabilities.
- Verified final test run: 8 passed.

## Verified findings

- 500 accounts; 5,000 subscriptions; 25,000 usage rows; 2,000 tickets; 600 event rows.
- Four account-level definitions yield 110 / 352 / 339 / 312 positive accounts. Account flag vs any-event membership has 312 disagreements; account flag vs subscription-flag account membership differs for 278.
- Usage: 19,142 rows before subscription start, 290 after non-null end. Twenty-one duplicate IDs span 42 records (21 excess).
- Satisfaction missing for 825/2,000 tickets. Event-history and no-event scored-ticket means are 3.980 and 3.983; account-cluster bootstrap interval for the scored-account mean difference includes zero.
- Recorded subscription MRR/ARR fields are available, but financial rows repeat account contracts and lack a trusted current snapshot; recurring revenue exposure and causal benefit remain UNKNOWN.

## Not completed / not demonstrated

- New analysis is not shown as a fifth UI section; the existing four chapters, API and app files were preserved.
- Docker daemon access was denied in this environment; no build, container, API/browser integration was run for this phase.
- No causal model, calibrated churn probability, financial ROI, or historical churn rate was produced.

## Authentic process record

- Tool: OpenAI Codex terminal/apply-patch tooling in this conversation.
- Prompt: user request “RavenStack Conventional Churn Analysis”; scope was an independent conventional analysis, preserve existing product/data/history, and avoid Git/remote effects.
- Agent decisions: use Python standard library because pandas/scipy/pytest are absent in the local interpreter and no added dependency is required; keep outputs independently runnable; decline UI integration while API/browser validation cannot be demonstrated and the existing frontend is concentrated in one component.
- Candidate human choices explicitly supplied: the conventional analysis scope and constraints in the user prompt. No additional business intervention, pricing, cost, or causal assumptions were supplied.
- Corrections: clarified that 312 is the symmetric difference between account flag and any-event membership (the separate account-vs-subscription mismatch is 278); output now names both.
- Mistakes: no erroneous conclusion was retained in the final report. No fabricated evidence or synthetic rows were introduced.
