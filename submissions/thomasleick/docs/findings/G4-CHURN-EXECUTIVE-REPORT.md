# RavenStack — CEO decision brief

**G4 AI Master Challenge 001 · Evidence snapshot: 2026-10-21**

## Decision

Do not launch a broad save campaign from these files. First reconcile the account/subscription lifecycle and define who was eligible to churn. Then instrument customer activation and run a controlled retention pilot only on a verified renewal population.

## What the records establish

- There are 600 event rows: 73 in 2023 and 527 in 2024. The data lack an eligible-customer denominator, so the apparent event increase does **not** establish an increase in churn rate.
- 110 of 500 accounts have the supplied churn flag; 352 have any event history. The two memberships differ for 312 accounts. Four account-level indicators disagree pairwise for at least one definition on 401 accounts.
- Use is measurable, but 19,142 of 25,000 usage rows predate the linked subscription start and 290 follow a nonblank end date. Remaining interval-valid use is descriptive, not proven pre-cancellation adoption.
- Satisfaction is missing on 825/2,000 tickets. In an all-time event/no-event split, ticket means are 3.980 (815 scores) and 3.983 (360 scores); these similar averages are not evidence of satisfaction before churn.
- Subscription amount rows repeat and their snapshot semantics are unverified. USD 8,652.25 in recorded refunds is not recurring revenue lost. Current MRR, GRR/NRR, LTV, exposure and preventable loss remain **UNKNOWN**.

## Business interpretation

The strongest verified finding is a measurement and lifecycle disagreement. UK, partner-referral and DevTools segments show higher prevalence under one or both event-derived labels, but the supplied account flag changes the picture, and the analysis is not adjusted for customer mix or cohort age. Treat these groups as diagnostic cuts, not proven bad-fit customers. The data do not demonstrate acquisition mismatch, weak activation, support-caused churn or a price/value cause.

No account is assigned a future churn probability. The application lists example accounts whose event and status records merit reconciliation; it does not call them the accounts most likely to churn.

## Recommended sequence

1. **Days 1–30 — RevOps + Data/Product Analytics:** define eligible paid account/subscription state, event and reactivation meanings, effective dates and monthly denominators; reconcile a sample against contract/source records.
2. **Days 31–60 — Product Analytics + Customer Success + Finance:** instrument onboarding completion, first value, valid adoption, support outcomes and dated recurring-value snapshots. Set the pilot sample size and operating cost from internal data.
3. **Days 61–90 — Customer Success + Analytics:** if eligibility and statistical power are adequate, randomize accounts to a defined adoption/support treatment or holdout. Measure verified account retention at 90 days; track recurring revenue separately and guard against satisfaction decline, escalation, discounting and excess cost.

Do not forecast benefits before a pilot. The Decision Room's editable lift and value fields are user-supplied assumptions; unset monthly value correctly leaves hypothetical value and net benefit `UNKNOWN`.

## Evidence needed next

Build an account-month ledger with eligible paying population, renewal/cancellation/reactivation, plan movement, opening and closing MRR, acquisition cohort, first-value event, pre-renewal adoption and support history. Use that ledger to publish comparable retention cohorts and to prespecify a randomized test. Expand an intervention only if intention-to-treat results support it and guardrails remain acceptable.

See the [consolidated report](G4-CHURN-CONSOLIDATED-REPORT.md) for methods, segment tables, account examples, economics limits, experiment design and reproducible commands. The underlying dataset is synthetic, so findings describe the challenge files rather than a real company's verified performance.
