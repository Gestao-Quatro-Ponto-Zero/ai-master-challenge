# RavenStack — G4 Customer Churn, Cohorts & Executive Decision

**Challenge:** G4 AI Master Challenge 001 — Diagnóstico de Churn  
**Analysis date:** 2026-10-21  
**Result:** PARTIAL — reproducible conditional date metrics exist; true historical customer churn and validated cohort retention remain not identifiable.

## 1. Executive summary

The best defensible primary **Customer Churn Rate is UNKNOWN**. The classical formula is unique eligible customers lost during a period divided by unique active customers at the start. The source does not identify the lost-customer numerator consistently.

For 2024, applying the supplied subscription-date rule produces **0/191 = 0.0% conditional account-coverage loss**: none of the 191 distinct accounts active on 2024-01-01 loses all recorded subscription coverage during 2024. This is a mathematical result under a date interpretation, not a validated commercial churn KPI. The same opening population includes 103 accounts with a 2024 non-reactivation churn event, while 443 of 472 non-reactivation event rows are dated when a linked subscription is still active. Account/event/subscription semantics conflict.

For 2023 the opening eligible population is **0**, so the classical annual rate is undefined, not 0%. The date-only acquisition cohort starting in 2023 is not a substitute for the opening-base churn rate.

Leadership should first establish a shared customer lifecycle definition and event-to-subscription/account-status audit trail. Then measure onboarding, adoption and customer experience against valid account-month or renewal cohorts. Do not launch a broad retention discount or claim a root cause from current labels.

## 2. Business context and G4 public approach

The challenge's business question spans acquisition fit, value realization, product adoption, customer experience, recurring economics and retention. G4's public cohort material describes time-linked groups and comparison at equal elapsed periods; its ICP article discusses using customer segment/cohort and LTV history to identify customer profiles that generate sustained value; its Customer Experience program discusses fit, the pre-to-post-sale journey, service consistency and retention. Its public LTV material describes value over the customer relationship and links it to acquisition economics.

Sources and attribution are documented in [the G4 methodology addendum](../research/g4-customer-churn-methodology-addendum.md). Direct automated retrieval of G4 pages returned 403 during this run; summaries rely on their public indexed text, accessed 2026-10-21. These are public teachings, not proprietary G4 formulas. The formula and diagnostic decisions below are our implementation choices.

## 3. Dataset and lifecycle audit

The submission includes five source CSVs: 500 account records, 5,000 subscription records, 25,000 usage records, 2,000 support tickets and 600 account-grain churn events. The new customer-churn module uses accounts, subscriptions and churn events because only those tables contain customer identity, candidate eligibility/lifecycle dates and departure markers. Usage and support remain available in the existing analysis; they are not joined into customer churn counts.

All 5,000 subscription IDs are unique and all subscription account IDs have account rows. Thirteen subscription intervals have `end_date <= start_date`. The source README describes blank `end_date` as active and `churn_flag` on a subscription as ended; account `churn_flag` is “churned at any point”; event `churn_date` is described as when the account left. None of those descriptions explains the observed contradictions. The latest source dates are 2024-12-31; 2025-01-01 is only a derived boundary, not a separately extracted snapshot.

Date snapshots under `[start_date, end_date)` with blank end as open-ended:

| Boundary | Distinct accounts with any active subscription | Active subscription rows |
|---|---:|---:|
| 2023-01-01 | 0 | 0 |
| 2024-01-01 | 191 | 655 |
| 2025-01-01 | 500 | 4,514 |

Multiple simultaneous subscription rows are collapsed to one `account_id` for customer calculations.

## 4. Formula and historical customer churn

**Classical formula:** `unique eligible customers lost during period / unique active customers at beginning of period × 100`.

For date-based diagnostics, a customer is considered active at a boundary if at least one linked subscription satisfies `start_date <= boundary` and (`end_date` is blank or `end_date > boundary`). A gross date-derived account loss is an opening account whose union of recorded subscription intervals has any coverage gap during the period. End-of-period loss is an opening account absent from the active set at the following annual boundary. These both rely on interpreting ends as effective coverage terminations and on the completeness of all contracts.

| Metric | 2023 | 2024 | Classification |
|---|---:|---:|---|
| Unique opening active accounts | 0 | 191 | Reconstructed date population |
| Opening accounts with any date-derived coverage gap | 0 | 0 | Conditional date diagnostic |
| Opening accounts without coverage at year end | 0 | 0 | Conditional date diagnostic |
| Conditional gross customer churn | Undefined (0 denominator) | 0/191 = 0.0% | Not validated as commercial churn |
| Non-reactivation event rows | 67 of 73 total event rows | 472 of 527 total event rows | Event records, not lost customers |
| Opening accounts with a non-reactivation event during year | 0 | 103/191 | Event-label overlap, not a churn rate |
| Opening accounts with `account.churn_flag=True` | 0 | 49/191 | All-time flag prevalence within opening base |
| Opening subscriptions no longer active at next annual boundary | 0 | 66/655 = 10.08% | Conditional subscription churn; not customer churn |

**Decision: C — Customer churn not identifiable.** In 2024, the conditional date rule has a reproducible value of 0/191, but the source also reports account departures for many of those accounts on dates with active subscriptions. Neither source is established as authoritative at commercial relationship grain. The correct primary product KPI is `UNKNOWN`; the date result remains separately disclosed. 2023 is undefined because its opening denominator is zero.

## 5. Cohort retention

G4-style cohorts were built by month of earliest positive-length subscription start. At each equal elapsed-month boundary, the diagnostic counts an account active if any linked subscription spans that date. It yields **24 cohorts and 300 cohort-age points**. Four points fall below 100%: September 2023 cohort 14/15 (93.3%) at 2023-12-01 and 2024-01-01; January 2024 cohort 25/26 (96.2%) at 2024-02-01; June 2024 cohort 26/27 (96.3%) at 2024-10-01. Each cohort is back at 100% at the latest derived boundary because recorded active subscription intervals resume or remain open.

These observations are conditional date-state diagnostics, not validated retention. The apparently non-monotone recovery, event/date conflict, open-ended rows and latest-boundary construction prevent a real retention heatmap. A validated cohort requires immutable cohort acquisition date, paid/eligible status, dated relationship termination, reactivation and observation/censoring timestamps.

Monthly and quarterly opening-base interval checks were also generated. Monthly date gaps occur in 2023-11 (1/149), 2024-03 (1/235), 2024-04 (1/264) and 2024-09 (2/385). Quarterly date gaps occur in 2023-Q4 (1/131), 2024-Q2 (1/264) and 2024-Q3 (1/338); other quarters with nonzero denominators have no gap under the same rule. These period denominators reset to all accounts active at each month/quarter start, including customers acquired during 2024, so they are not the 2024 annual opening cohort's churn count. The 2024 annual opening cohort itself has zero such gaps across the full year by the current interval union calculation. All subannual rates remain conditional on end-date and coverage semantics.

## 6. Movement reconciliation

The 2024 boundary sets reconcile arithmetically as:

`191 opening accounts + 308 first-subscription accounts active at close + 1 previously seen account returning active at close − 0 opening accounts absent at close = 500 closing accounts`.

Residual: **0**. This is a boundary-set identity, not a gross flow ledger: it does not enumerate intra-year temporary gaps, cancellations, returns, account transfers or contract replacements. Therefore, it does not resolve customer churn.

## 7. Acquisition, ICP and segments

Account-level descriptive comparisons are available under the all-time account flag and non-reactivation-event labels. For segments with at least 30 accounts, DevTools has the highest account-flag prevalence in this descriptive table: **35/113 = 31.0%**; it also has 2024 non-reactivation event prevalence of **75/113 = 66.4%**. The event acquisition-source segment has 2024 event prevalence **58/96 = 60.4%** and account-flag prevalence **29/96 = 30.2%**. These are not validated retention differences; event labels are inconsistent with recorded active status, and the account flag is all-time without a period timestamp. They are reasonable samples for acquisition/ICP and lifecycle review, not evidence of ICP mismatch or predictive risk.

No CAC, margin, paid conversion or account-level realized LTV is available, so acquisition quality cannot be ranked economically. Small groups must not be over-interpreted; the interface displays denominators.

## 8. Activation and adoption

Existing usage analysis finds substantial date-order problems (including usage records before linked subscription start); the existing investigation therefore does not establish a reliable time-to-first-value or pre-churn adoption slope. Usage totals can describe observed activity but cannot be sequenced confidently against a validated customer departure. Instrument signup, onboarding milestones, first successful use, feature adoption snapshots and paid-status intervals with a common account key before using activation as a churn mechanism.

## 9. Customer experience

The existing support analysis reports ticket-level and account-level comparisons with denominators. Satisfaction is missing for 825/2,000 tickets; the remaining means are cross-sectional and not aligned to a trusted customer-loss time. Support differences are diagnostic, not causal. Do not assign save actions from a satisfaction mean without a valid account-period outcome and a comparison design.

## 10. Value, reason codes and economics

Among the 472 2024 non-reactivation event rows, recorded reason counts are: features 91, budget 82, support 81, unknown 77, pricing 72 and competitor 69. The four themes features/budget/support/pricing total **326/472** event rows. These are repeated event rows with self-reported/generated reason labels, not unique lost customers and not demonstrated causes. Reason patterns should guide interviews and instrumentation.

Verified lost MRR, ARR, GRR, NRR, LTV and recoverable revenue remain **UNKNOWN**. Repeated subscription rows do not establish period revenue snapshots. Refunds are observed event fields, not lost recurring revenue. No intervention effectiveness or causal financial benefit has been measured.

## 11. Root-cause hypotheses and evidence

| Candidate mechanism | Evidence observed | Counterevidence / limit | Status |
|---|---|---|---|
| Lifecycle/measurement definition problem | 103/191 opening accounts have a 2024 non-reactivation event; 443/472 non-reactivation event rows occur while at least one linked subscription is date-active | Does not tell whether event or contract status is correct | Strongest supported explanation for the *apparent metric paradox*, not a customer churn cause |
| Product feature/value concern | 91/472 2024 event rows use `features`; budget 82; pricing 72 | No validated customer loss or event-to-subscription FK; repeats per account | Business hypothesis / interview theme |
| Support friction | 81/472 event rows use `support`; existing ticket data include escalations and satisfaction | Reasons not causal; missing scores and temporal ambiguity | Business hypothesis |
| Acquisition/ICP mismatch | DevTools label prevalence is relatively high under both account flag and event labels | Labels are unreliable; no CAC/LTV or retained cohort comparison | Exploratory hypothesis |
| Usage protects retention | Usage data and subscription status are not reliably time-aligned | No valid pre-loss exposure comparison | Unknown |

No causal root cause is established.

## 12. Specific account review candidates

The new API/UI surfaces accounts with repeated 2024 event history inside the 2024 date-derived opening population, explicitly as reconciliation priorities: `A-37f969` (4 non-reactivation event rows all-history; account flag false), `A-ee42db` (4; flag false), `A-1b9609` (3; flag false), `A-1e1b80` (3; flag false), `A-32fb14` (3; flag true), and `A-3b5cd1` (3; flag false). The source dates classify these accounts active in the opening population; their IDs are not predictions. A customer-success/RevOps review should determine whether events represent a contract ending, account departure, administrative reversal or duplicate record.

## 13. Answers to the three G4 challenge questions

### Q1 — Why are customers churning?

No customer churn cause is established because the lost-customer outcome itself is not consistently identified. The strongest confirmed issue is lifecycle measurement conflict: event rows say account departure while account coverage continues by subscription dates. Features (91 rows), budget (82), support (81) and pricing (72) are reported themes for investigation, not proven causes.

### Q2 — Which customers or segments need attention?

Prioritize **DevTools** for descriptive review (35/113 all-time account flags; 75/113 2024 event-labeled accounts) and the acquisition `event` segment (29/96 flags; 58/96 with 2024 events). Review the specific accounts listed above with Customer Success and Revenue Operations. These are label-conditioned segment comparisons and record-reconciliation cases—not verified lost customers or future-risk predictions.

### Q3 — What should RavenStack do?

1. **Define and instrument customer lifecycle** (Data/Engineering + RevOps; first 30 days). Link account, subscription and event IDs; distinguish effective end, scheduled end, cancellation, reactivation and migration. Success: auditable account-month state and reconciled event-to-contract outcome.
2. **Review event cases and reason taxonomy** (Customer Success + RevOps; days 1–30). Sample repeated event accounts and validate reason against contract/billing status. Success: share of events adjudicated and reason completeness; no discount campaign until eligibility is reliable.
3. **Build ICP cohorts with valid retention and unit economics** (Marketing/Sales + Finance/Analytics; days 31–60). Compare equal-age retained account cohorts by acquisition source, industry, geography and plan after lifecycle repair. Success: denominators, mature follow-up, CAC and verified gross margin/value fields.
4. **Instrument activation and adoption journey** (Product + Customer Success; days 31–60). Record onboarding completion and first-value event; monitor account-level active use at consistent intervals. Success: valid activation and adoption milestones linked to paid status.
5. **Run a controlled retention pilot only after eligibility is stable** (Customer Success + Analytics; prepare by day 60, launch by day 90 if sample/power allow). Randomize by account; primary outcome: verified 90-day logo retention; guardrails: discount, support, complaints and verified MRR. Cost and effect remain unknown until priced and tested.

No monetary impact estimate is defensible today. The plan prioritizes measurement readiness before intervention spend.

## 14. Decision Room and scenario assumptions

The existing scenario simulator remains hypothetical. Users supply eligible population, capacity, cost, incremental retention lift, value per retained account and horizon. Currency is unit-neutral. No supplied assumption is a measured uplift, baseline customer-loss rate, or verified MRR. Scenario output is conditional arithmetic only.

## 15. Engineering and implementation

Added isolated `solution/analysis/g4_customer_churn/` with standard-library computation, source SHA-256 hashes, JSON and CSV outputs, CLI help, methodology and tests. The API computes and serves `/api/g4-customer-churn`. The frontend now shows a single primary Customer Churn KPI as UNKNOWN, the separate 0/191 conditional date result, date/event conflict, conditional cohort diagnostic, segment/account review examples, and Q2 evidence. Existing four chapters and historical modules were retained.

G4 methodology addendum and this report are new files. Historical reports/checkpoints and source CSVs were not edited.

## 16. Validation and evidence

Current execution evidence:

- Preflight and post-run SHA-256 checks revalidated all five source CSVs; the recorded hashes match.
- New G4 analysis tests: 5/5 passed. Historical tests: 5/5; contract forensic tests: 5/5; conventional tests: 8/8; business-driver tests: 4/4.
- `python solution/analysis/g4_customer_churn/analyze.py --help`: CLI help works; JSON plus monthly, quarterly and cohort CSV outputs were regenerated.
- Frontend Vitest: 6/6 passed. TypeScript/Vite production build passed; bundle warning remains (687.34 kB minified, 192.07 kB gzip).
- API Docker test image: Ruff passed; pytest 17/17 passed (one upstream Starlette/AnyIO deprecation warning); G4 module unittest in Python 3.12: 5/5 passed.
- `docker compose config --quiet` passed. Separate production Compose project `ravenstack-g4-final` built and ran both services healthy (API 18200, frontend 15175). Health, OpenAPI, G4 endpoint, frontend root and frontend proxy returned HTTP 200. Proxy JSON matched the direct API payload (94,214 bytes). Valid scenario returned 200/HYPOTHETICAL; invalid input returned 422.
- Docker reports the buildx component is absent and uses its legacy builder; both builds completed successfully.
- Browser viewport verification is not claimed in this run. The prior local browser navigation was blocked by its security surface; no alternate browser boundary was used. No screenshot was created or treated as current evidence.

## 17. Remaining unknowns

- Commercial customer churn by period and true lost-customer numerator.
- Whether end date is effective departure, scheduled contract end, or administrative row end.
- Whether events refer to a contract, account, duplicate/reversed event or non-final intention.
- Valid retention by cohort and right-censoring window.
- Causal effects of feature use, support, acquisition channel or intervention.
- Current/lost recurring revenue, gross/net retention and LTV.
- Calibrated future-risk probabilities.

Required source additions: immutable event ID plus `subscription_id`, effective cancellation date, reason adjudication, status history with extraction timestamps, paid eligibility, reactivation linkage, monthly MRR/discount/refund ledger, CAC and margin, onboarding/first-value markers, and cohort observation end dates.
