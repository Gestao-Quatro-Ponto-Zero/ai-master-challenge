# RavenStack — The Churn Paradox
## G4 AI Master Challenge 001 — consolidated business investigation

**Evidence snapshot:** 2026-10-21. The report uses the five source CSVs in `solution/data/raw/`; current output is reproducible with the independent generator documented in `solution/analysis/business_drivers/README.md`. Dataset SHA-256 hashes and source details are in `process-log/evidence/mission-2026-10-21-data-profile.json`. The supplied dataset describes synthetic data; these records do not establish the real operating performance of a company.

## 1. Executive summary

RavenStack has 600 recorded churn-event rows, including 527 dated in 2024 and 73 in 2023. Those counts do not establish a rising churn rate: the records lack a reconciled eligible-account denominator, reliable lifecycle transitions and consistent account/subscription outcomes. The supplied account churn flag is true for 110/500 accounts, while 352 accounts have any event history; these two memberships disagree for 312 accounts. Across four outcome indicators, 401/500 accounts disagree on at least one pair.

The files contain usable diagnostic signals—customer profile, use, tickets, contract-row fields and reason codes—but they cannot establish a causal churn mechanism, a defensible future-risk probability, recurring revenue lost, or intervention ROI. Usage is often outside the linked subscription interval; satisfaction is missing for 41.25% of ticket rows and is not aligned to cancellation. Revenue-like contract rows repeat across 5,000 subscriptions and lack reliable snapshot semantics.

Leadership should first reconcile lifecycle state and financial snapshots, then instrument activation/adoption on an account timeline, and only then run an account-randomized retention pilot among verified eligible renewals. Do not launch a broad save campaign from the supplied labels.

## 2. Business context

Churn is a customer-outcome measure with a defined population and time window. For a subscription business, it also connects acquisition quality, customer fit, onboarding and time-to-value, sustained adoption, customer experience, contract lifecycle and recurring revenue. Event volume, a static churn flag and ticket sentiment answer different questions. Treating them as interchangeable can misallocate Customer Success effort and make financial exposure appear more certain than it is.

This report uses the public G4 concepts summarized in [the source review](../research/g4-business-framework.md). The business dimensions below are our interpretation of those public concepts, not an official or proprietary G4 framework.

## 3. Public G4 methodology review

The reviewed G4 materials discuss customer cohorts, end-to-end Customer Experience, ICP and customer segmentation, commercial strategy, LTV and relationship marketing. Their practical implication for this investigation is to compare customers with a shared starting event over comparable follow-up time, understand who acquires durable value, inspect the post-sale journey and connect retention to economics. The source review provides canonical URLs, access notes and the translation to available RavenStack fields. Some pages were readable only via official indexed public text and page metadata; no private course content was used.

## 4. Dataset audit

| Source | Rows / entity grain | Main use | Key limit |
|---|---:|---|---|
| `ravenstack_accounts.csv` | 500 accounts | Profile, signup, account flag | Static flag is not a dated outcome. |
| `ravenstack_subscriptions.csv` | 5,000 subscription rows | Plan, dates, billing, recorded amounts and subscription flag | Ten rows per account on average; version/snapshot and eligibility semantics are not established. |
| `ravenstack_feature_usage.csv` | 25,000 usage rows | Dated feature activity, duration, errors, beta indicator | 19,142 rows precede linked subscription start; repeated IDs and ambiguous lifecycle restrict interpretation. |
| `ravenstack_support_tickets.csv` | 2,000 ticket rows | Priority, response/resolution, escalation and score | 825 satisfaction scores missing; no category field; ticket rows cluster within accounts. |
| `ravenstack_churn_events.csv` | 600 event rows | Reason, event date/type, reactivation marker and refunds | Repeated events and no reliable subscription linkage; rows are not unique lost customers. |

The original source files are retained unchanged. Current source hashes/profile and the earlier data audit are in `process-log/evidence/` and checkpoints 02 and 15. The independent business analysis aggregates each child table to its intended grain before comparing account outcomes. No account-level finance amount is obtained by summing subscription versions and calling that current MRR.

## 5. Churn-definition analysis

| Definition | Positive accounts | Interpretation |
|---|---:|---|
| Supplied account `churn_flag` | 110/500 (22.0%) | Operational field prevalence only; not a historical rate. |
| Any event row | 352/500 (70.4%) | Ever had at least one event row, including reactivation. |
| At least one non-reactivation event | 339/500 (67.8%) | Event membership; does not prove final cancellation or current state. |
| At least one flagged subscription | 312/500 (62.4%) | Account membership from 486 flagged subscription rows. |

For account flag versus any-event history: 75 are positive under both, 35 flag-only, 277 event-only and 113 neither (symmetric difference 312). Pairwise differences are 301 for account flag vs. non-reactivation, 278 for account flag vs. flagged-subscription membership, and 13 between the two event-derived memberships. Across all four indicators, 401 accounts differ on at least one comparison. Because the fields may encode different lifecycle semantics, disagreement is a reconciliation finding, not proof that all disagreeing rows are erroneous.

There are 539 event rows marked non-reactivation and 61 marked reactivation. Annual counts are 73 in 2023 and 527 in 2024. Without eligible account/subscription exposure and reliable outcome dates, neither event-based nor account-based churn rate is identifiable. Logo churn, subscription churn rate, GRR and NRR remain **UNKNOWN**.

## 6. Acquisition and ICP

The independent output provides account-grain label prevalence with Wilson 95% intervals by referral source, industry, country, plan, trial status and account characteristics. Examples with adequate descriptive counts include:

| Segment | Any event | Non-reactivation event | Account flag |
|---|---:|---:|---:|
| UK (n=58) | 45 (77.6%) | 43 (74.1%) | 19 (32.8%) |
| Partner referral (n=89) | 67 (75.3%) | 64 (71.9%) | 13 (14.6%) |
| DevTools (n=113) | 83 (73.5%) | 81 (71.7%) | 35 (31.0%) |
| Ads (n=98) | 59 (60.2%) | 56 (57.1%) | 23 (23.5%) |

UK and DevTools directions are similar under the two event labels, but remain descriptive. Partner differs sharply under the account flag, demonstrating label dependence. Revenue, margin, acquisition cost, comparable cohort age and adjusted customer mix are absent. An acquisition-quality or ICP mismatch has not been established. Subscription-row flag prevalence is 247/2,461 annual (10.0%, Wilson 95% 8.9–11.3%) and 239/2,539 monthly (9.4%, 8.3–10.6%); this is not a billing-period churn rate.

## 7. Activation and adoption

Linking usage to exactly one subscription and retaining only dates on/after subscription start and on/before nonblank end leaves 5,568 usage rows across 469 accounts. There are 19,142 rows before linked subscription start and 290 after a nonblank end; 31 accounts have no interval-valid usage. The first interval-valid use occurs a median 77 days after account signup; 10/469 are within seven days and 62/469 within 30 days. Signup is not a validated onboarding or first-value event, so this is a timing proxy, not time-to-value.

Among interval-valid usage counts, the top decile (47 accounts) represents 25.1%; the top ten represent 6.9%, and top 50 represent 26.4%. Without a benchmark, this does not establish unusual concentration. Any-event accounts average 113.3 interval-valid usage units per account versus 107.1 among accounts without events; this is retrospective, not a verified pre-cancellation comparison. Usage count is not realized value. No reliable feature adoption trend before cancellation can be reconstructed.

Duplicate usage IDs are reported as three distinct measures: **21 duplicated ID groups; 42 rows belonging to those groups; 21 excess rows** beyond one retained occurrence per ID. Within the interval-valid sensitivity, 14 rows belong to duplicated ID groups. Deduplication order changes valid-row totals slightly; outputs preserve the distinct policies rather than silently removing records.

## 8. Customer Experience

Satisfaction is missing on 825/2,000 tickets (41.25%). By any-event account membership, event accounts contribute 1,395 tickets from 347 accounts, with mean score 3.9804 among 815 scored rows and 580 missing. The no-event group contributes 605 tickets from 145 accounts, mean 3.9833 among 360 scored rows and 245 missing. Account-cluster means are 3.9616 across 330 scored accounts versus 3.9703 across 136.

Median first response is 89 vs. 87 minutes, median resolution is 35 hours in both groups, and escalations are 71/1,395 (5.1%) vs. 24/605 (4.0%). These are all-time descriptive comparisons under one alternative label; ticket selection and account clustering matter, and temporal order to cancellation is not established. Similar averages do not prove that CX is favorable for at-risk customers. The source has priority but no ticket-category column; categories are not invented.

## 9. Cohort analysis

Account signup quarter yields eight diagnostic cohorts of 53–80 accounts. A quarter of earliest listed subscription start can also be shown, but multiple subscription rows and no validated first eligible paid subscription make that anchor ambiguous. These cohorts can compare retrospective label composition only. Unequal follow-up, censoring, conflicting labels and missing eligible-state history prevent retention-by-elapsed-month calculations. No retention heatmap is published. To make one valid, RavenStack needs a defined start/eligibility event, monthly active/paid status, cancellation and reactivation dates, consistent account/subscription mapping, and follow-up censoring rules.

## 10. Subscription economics

Subscription `mrr_amount` row values range 0–33,830 (median 931) and ARR row values 0–405,960 (median 11,172); each has 778 zero rows. Summing all rows (11,338,747 MRR-field units and 136,064,964 ARR-field units) would double-count repeated contract records and is not reported as current or lost revenue. Event-row refunds sum to USD 8,652.25 across 142 nonzero records; refunds do not measure recurring revenue lost. Current MRR/ARR, expansion/contraction, revenue churn, GRR, NRR, LTV, exposed recurring revenue and preventable loss remain **UNKNOWN**. Finance needs currency, invoice/contract lineage, dated opening/closing snapshots and explicit movement semantics.

## 11. Root-cause hypotheses

Evidence priority below ranks investigation usefulness, not causal probability:

| Priority / mechanism | Evidence | Counterevidence / limit | Status and next test |
|---|---|---|---|
| P0 — Outcome/lifecycle instrumentation conflict | 401/500 accounts differ across at least one of four account indicators; 312 differ between account flag and any event. | Indicators may encode different semantics. | `VERIFIED_OBSERVATION` of disagreement; reconcile source contracts and sample records. |
| P1 — Acquisition/ICP mismatch | Event-label prevalence varies by channel, geography and industry. | Rankings change with label; no CAC, value, adjustment or valid outcome cohort. | `CONDITIONAL_RESULT`; analyze comparable prospective acquisition cohorts. |
| P1 — Weak activation/time-to-value | 5,568 interval-valid usage rows; first-use proxy is delayed for many accounts. | Signup is not activation; most usage rows are outside subscription intervals. | `UNKNOWN`; instrument onboarding and first-value events. |
| P1 — Low/concentrated adoption | Top decile accounts produce 25.1% of interval-valid usage counts. | Count is not value; no validated pre-cancellation window. | `CONDITIONAL_RESULT`; define meaningful use and follow prospectively. |
| P2 — Support friction | Ticket and account-cluster summaries are available by labels. | 41.25% score missing, ticket selection, no event-time alignment. | `CONDITIONAL_RESULT`; link tickets to reconciled renewal/cancel dates. |
| P2 — Price/value mismatch | Price/budget reason codes and repeated contract-row monetary fields exist. | Reason codes are not causal proof; financial semantics unresolved. | `UNKNOWN`; validate with customer interviews and finance lineage. |
| P2 — Reliability/competitive gap | Usage error counts and reason codes exist. | No incident/release exposure or reliable cancellation timeline. | `UNKNOWN`; link telemetry to incident exposure and verify with customers. |

No root cause has been established. Reasons are customer/event-recorded categories and should be treated as reports to investigate, not causal explanations.

## 12. Answers to the G4 Challenge

### Question 1 — What is causing churn?

**Answer:** Unknown. The strongest verified finding is outcome/lifecycle disagreement, not a demonstrated customer mechanism. Usage, support, acquisition and event reasons provide candidate follow-up signals, but their temporal alignment and outcome definitions are insufficient for causal attribution. Confirm cause through reconciled lifecycle records, prospective pre-outcome instrumentation and controlled tests.

### Question 2 — Which segments and accounts are most at risk?

**Answer:** No segment or account has a defensible calibrated future-risk estimate. UK, partner referral and DevTools have higher event-label prevalence in some comparisons, but rankings depend on outcome label and are unadjusted. The interface names specific accounts as **reconciliation candidates** based on repeated event rows and/or conflicting flags; they are not predictions or “most likely to churn” accounts. A valid risk ranking requires a stable future outcome, features measured before prediction, and time-based validation.

### Question 3 — What should RavenStack do?

**Answer:** First (RevOps + Data/Product Analytics), reconcile account/subscription state, event semantics, eligibility, reactivation and dated financial snapshots. Next (Product Analytics + Customer Success), instrument onboarding completion, first value and adoption within a shared timeline. Then (Customer Success + Analytics), pilot a defined intervention among verified active accounts with upcoming renewal using account-level random assignment and holdout. Measure 90-day verified account retention; guardrail satisfaction, escalation, discounting and treatment cost. Costs and benefits must be estimated from RavenStack operations; no uplift is known from this dataset.

## 13. Account and segment priorities

Four displayed examples illustrate reconciliation, not risk:

| Account | Observed reason to inspect | Interpretation |
|---|---|---|
| A-0a62f5 / Company_381 | 5 non-reactivation event rows while account and subscription flags are false; 2 tickets, no escalation, 1 valid-use row. | Event/flag conflict; not a risk score. |
| A-180abf / Company_122 | 5 event rows, flags align true; 64 seats and 3 tickets. | Reconcile current lifecycle and subscription linkage. |
| A-37f969 / Company_150 | 4 event rows while flags are false; 5 tickets and 1 escalation. | Inspect support and event lineage; no causal inference. |
| A-fd7ad3 / Company_100 | 4 event rows (3 non-reactivation); subscription flag true and account flag false; 8 tickets, 1 escalation. | Conflicting outcome membership. |

These rows are examples surfaced for investigation. They are not selected by predicted churn probability, preventable revenue or a validated risk ranking.

## 14. Decision Room and financial scenarios

The API computes selected outreach as the minimum of eligible accounts, capacity and budget divided by per-contact cost. Hypothetical incremental retained accounts equal selected outreach times user-supplied incremental percentage-point lift. Hypothetical gross value multiplies those accounts by user-entered monthly value and horizon; hypothetical net value subtracts contact cost. The UI labels all inputs and outputs as user-supplied assumptions, not observed lift or forecast. When monthly value is unset, value and net benefit are `UNKNOWN`. Currency units are generic, not USD. Scenario arithmetic does not imply revenue is recoverable.

## 15. Recommended 30/60/90-day action plan

| Timing | Suggested function | Work / dependency | Success measure |
|---|---|---|---|
| Days 1–30 | RevOps + Data/Product Analytics | Define account and subscription states, cancellation/reactivation semantics, event linkage, eligible denominator and finance snapshot contract; validate sample records against source contracts. | Audited state coverage and stable eligible account-month denominator. |
| Days 31–60 | Product Analytics + Customer Success + Finance | Instrument onboarding completion, first value, dated adoption/support signals; create reconciled renewal cohort and baseline. Estimate pilot sample size and costs locally. | Coverage and data quality for first value, 7/30-day adoption and upcoming renewals; approved analysis plan. |
| Days 61–90 | Customer Success + Analytics | If eligibility and power are adequate, launch an account-randomized intervention with holdout; monitor guardrails. Complete 90-day outcome readout 90 days after treatment begins. | Intention-to-treat 90-day account retention; verified MRR reported separately; satisfaction, escalation, discount and cost guardrails. |

Effort labels in the app (medium / low-to-medium) are planning estimates only, not measured budget or staffing commitments. Functions are suggested, not assigned employees.

## 16. Experiment design

Eligibility: verified active paid accounts with a renewal within 60 days and a prespecified observable adoption or unresolved-support criterion. Exclude accounts with unresolved identity/lifecycle state. Randomize by account, stratified by plan and verified recurring value; keep all subscriptions and contacts for an account in one arm to prevent contamination. Compare a documented Customer Success/adoption treatment with business-as-usual holdout. Primary outcome: verified account retention at 90 days. Report renewal and verified MRR separately. Guardrails: satisfaction, escalations, discounting, complaints and treatment cost. Use intention-to-treat; predefine exclusions, censoring, sample size/power, analysis date and stopping rules. No experiment has been run.

## 17. Engineering architecture

The standalone `solution/` package contains a FastAPI service, React/TypeScript/Vite single-page application served by Nginx, deterministic Python analysis scripts and the five original CSVs. The API loads verified outputs at startup, exposes REST/JSON and OpenAPI, and serves `/api/business-investigation`; Nginx proxies `/api` to the API. Docker Compose runs only the API and web services. No persistent database, cloud service or runtime AI provider is required. Typed API response contracts are mirrored in TypeScript.

## 18. Implementation changes in this execution

- Added the public G4 business concept review and an independent business-driver analysis module with generated CSV/JSON artifacts.
- Added the business investigation API contract and integrated the findings into the existing four chapters without replacing the conventional evidence.
- Added business-driven findings and recommendation/hypothesis content; historical reports and all five source CSVs remain preserved.
- During final responsive QA, corrected the confirmed 390 px Chapter 02 panel-header overflow and the confirmed 320 px Chapter 03 account-candidate badge overflow using mobile-only CSS. No analytical calculations changed.
- Removed unused local variables/imports and expanded compressed one-line statements in the conventional analysis script and business-driver tests after Ruff identified them. The edits were style/dead-code only; both real-data analysis test suites passed again, so no findings or outputs were intentionally changed.

## 19. Validation evidence

Current-turn evidence:

- `docker compose -p ravenstack-remediation -f compose.yaml ps` from `solution/`: API and web both healthy; API `/api/health` and Nginx-proxied `/api/health` returned `status=ok`, `analysis=loaded`, `data=source-csv`.
- Browser viewport 390×844: all four chapters rendered; document width 375 CSS layout pixels and no content overflow beyond viewport.
- Browser viewport 320×568 after correction: all four chapters rendered; `documentElement.scrollWidth` equals `innerWidth` (320) in each chapter.
- Chapter 04 scenario submission through the real UI returned 50 accounts selected, 5 hypothetical incremental retained, 5,000 user-supplied cost units and `UNKNOWN` value/net because monthly value is unset.
- Keyboard Tab produced a 3 px gold focus outline. Emulated reduced motion set chapter animation to 0.01 ms and document scrolling to `auto`.
- `npm test -- --run`: 2 files, 6 tests passed. `npm run build`: TypeScript and Vite succeeded; 2,200 modules, JavaScript 662.02 kB minified / 186.41 kB gzip, above Vite's 500 kB warning threshold.
- Ruff 0.11.8 (from the pinned API test image) passed across API, scripts, conventional analysis and business-driver analysis after the style cleanup.
- Docker web image rebuild succeeded; Compose health became healthy. The build emitted a non-blocking warning that Compose Bake is enabled but buildx is not installed.
- API tests passed 13/13 in the final validation checkpoint 22. Conventional analysis passed 8/8 and business-driver analysis 4/4 after the later style-only cleanup (checkpoint 23). Earlier analysis runs remain separately recorded in checkpoints 09–19.

Screenshots were not persisted: the browser screenshot tool rejected writes into the candidate package because its allowed roots point to the LeickOS workspace. No screenshot was written outside the submission scope. Rendered DOM, viewport metrics and scenario interaction were observed directly in the browser.

## 20. Conventional analysis versus business-driven analysis

The conventional analysis established the row counts, outcome-label disagreement, label-conditioned segment comparisons, interval-valid usage sensitivity, support denominators, contract-row limitations and absence of a valid model. The business-driven layer reorganizes these same verified outputs around acquisition/ICP, activation, adoption, Customer Experience, economics and cohort decisions, then converts them into a sequence of evidence-readiness actions and an experiment. It confirms that cohort retention and root cause are not identifiable, adds explicit first-use and concentration diagnostics, makes label dependence visible in the interface and highlights the operational value of lifecycle instrumentation. It does not overturn the prior analytical conclusion that churn rate, future risk, lost recurring revenue and causal impact are unknown.

## 21. Known unknowns

- Whether churn rate increased and the denominator of eligible customers/subscriptions by period.
- Final account/subscription status, cancellation date, reactivation lifecycle and event-to-subscription mapping.
- Reliable time-to-value, pre-cancellation adoption and support sequence.
- A valid retention curve, cohort survival or time-to-event estimate.
- Causal root cause, predictive probabilities, model performance or calibrated account risk.
- Current recurring revenue, MRR/ARR movement, GRR/NRR, LTV, revenue exposed/lost or preventable value.
- Intervention cost, incremental effect, ROI or experiment outcome.
- Whether the synthetic source's segment relationships generalize to a real business.

## 22. Experimental extensions

No separate experiment module or predictive model was added. The business-driver analysis is an independently generated, additive analytical module, and its limitations are explicit. The simulator remains a conditional arithmetic exercise, not an experiment result. No extension is presented as validated causal evidence.

## 23. Final recommendations

1. Reconcile account/subscription lifecycle, event definitions and eligible denominators before publishing a churn rate or targeting accounts.
2. Establish dated, account-linked activation/adoption, support and finance snapshots so customer cohorts share comparable follow-up.
3. Use current segment and account evidence for investigation only; do not label it future risk.
4. Run an adequately powered account-level holdout pilot only after eligibility and outcome measures are verified.
5. Report measured 90-day retention and verified revenue separately from scenario assumptions; expand only if the randomized evidence and guardrails support it.

## Reproduction

From `submissions/thomasleick/solution/`:

```bash
python analysis/business_drivers/run.py --data-dir data/raw --output-dir analysis/business_drivers/outputs
python -m unittest discover -s analysis/business_drivers/tests -v
docker compose up --build
```

The portable runtime root is the submitted `solution/` directory. See [the package README](../../README.md), [solution instructions](../../solution/README.md), [business-driver report](business-driven-investigation.md), [analysis methodology](../methodology/analysis.md), [G4 source review](../research/g4-business-framework.md), and [process checkpoints](../../process-log/checkpoints/).
