# G4 Challenge 001 — Final executive answers

## Executive conclusion

The record count of churn events increased sharply, but that does not itself demonstrate worsening retention. From 2023 to 2024, recorded event rows increased **73→527** while reconstructed opening account-month exposure grew **845→3,909**. Event rows per 100 reconstructed opening account-months rose **8.64→13.48**. Date-derived plan-proxy loss episodes rose **6→56** and their intensity rose **0.427→0.595 per 100 opening relation-months**; in contrast, full account-coverage loss episodes rose **2→6** while their intensity fell **0.237→0.153 per 100 account-months**. These are conditional date diagnostics and event-record measures, not a validated commercial customer churn rate. The CEO's apparent contradiction is therefore not resolved as a true retention deterioration: source usage was nearly flat, while lifecycle and outcome records conflict.

## Q1 — What is causing churn?

**No causal root cause is established.** There are 600 recorded event rows (73 in 2023; 527 in 2024), 352 accounts with any event, 339 with a non-reactivation event and 110 with `account.churn_flag=True`; **401/500 accounts disagree across at least one of the four supplied outcome indicators**. Recorded event rows lack a subscription/plan key and frequently coincide with date-active subscription coverage. Reasons are declared classifications, not causal proof.

Platform usage did not materially grow on the raw source scale: 124,561→125,964 recorded usage count (+1.13%), 24.462→24.747 per observed account-month (+1.17%). Yet 19,142/25,000 source usage rows precede linked subscription start; temporal pre-loss adoption is not identifiable.

The any-event group and no-event group have nearly equal satisfaction (3.9804/815 scored ticket rows vs 3.9833/360); first response medians 89 vs 87 minutes, resolution medians 35 vs 35 hours, and escalation rates 5.09% vs 3.97%. 825/2,000 satisfaction observations are missing (41.25%). Tickets are repeated within accounts and not temporally aligned to loss; these comparisons do not support a causal support explanation.

**Decision:** treat acquisition fit, activation, adoption, CX friction, price/value and lifecycle/instrumentation as hypotheses for prospective measurement. Fix lifecycle definitions before calling any one a root cause.

## Q2 — Which segments and accounts need attention?

The available segment evidence is retrospective prevalence of a disputed event label. Sample sizes and Wilson intervals are shown; overlaps mean the small differences should not be ranked as meaningful risk.

- **industry / DevTools:** 81/113 (71.7%; Wilson 95% interval 62.8–79.2%), using the all-time account-level non-reactivation-event label. This is label prevalence, not risk.
- **industry / EdTech:** 56/79 (70.9%; Wilson 95% interval 60.1–79.8%), using the all-time account-level non-reactivation-event label. This is label prevalence, not risk.
- **plan_tier / Pro:** 126/178 (70.8%; Wilson 95% interval 63.7–77.0%), using the all-time account-level non-reactivation-event label. This is label prevalence, not risk.

Each interval overlaps with adjacent groups; do not treat the label differences as significant or predictive. Under reconstructed dates, 60 accounts have at least one plan-proxy loss; 54 loss episodes occurred while another plan proxy remained active, and 8 accounts had a complete coverage gap followed by a return within the observed window. Those eight are retrospective lifecycle-reconciliation cases.

| Account | Segment | Observed evidence | Recommended handling |
|---|---|---|---|
| `A-180abf` | DevTools · US · event · Pro | 5 event rows (5 non-reactivation), 3 tickets/0 escalations, 10 interval-valid usage rows | Review event/account status agreement; no predictive score |
| `A-37f969` | HealthTech · IN · partner · Enterprise | 4 event rows (4 non-reactivation), 5 tickets/1 escalations, 8 interval-valid usage rows | Review event/account status agreement; no predictive score |
| `A-fd7ad3` | Cybersecurity · US · event · Enterprise | 4 event rows (3 non-reactivation), 8 tickets/1 escalations, 1 interval-valid usage rows | Review event/account status agreement; no predictive score |
| `A-0a62f5` | FinTech · UK · partner · Pro | 5 event rows (5 non-reactivation), 2 tickets/0 escalations, 1 interval-valid usage rows | Review event/account status agreement; no predictive score |

These IDs are selected from repeated event history and/or label conflict. They are **investigation examples**, not a risk ranking. Usage is shown only when rows fall within recorded subscription-date bounds; that timing filter does not establish prediction.

## Q3 — What should RavenStack do?

1. **Define the lifecycle contract (Data / RevOps, days 0–30).** Link events to subscription and plan, record effective cancellation and reactivation dates, and version monthly eligible-customer snapshots. KPI: ≥98% of events linked to a contract and zero unresolved status conflicts in audited samples. Baseline: 401/500 accounts disagree across outcome indicators. Impact is measurement quality, not automatic recovered revenue.
2. **Reconcile historical account cases (Customer Success + RevOps, days 0–30).** Review the 60 accounts with date-derived plan losses, prioritizing the 8 complete-coverage-gap-and-return timelines and the specific cases above. KPI: disposition (commercial loss, contract-only event, correction, unknown) documented for every case. Historical cases are not current eligibility.
3. **Instrument activation and adoption cohorts (Product Analytics, days 0–60).** Capture first successful value event, active customer eligibility, and account-level monthly usage tied to a valid contract. KPI: ≥95% of eligible accounts have an interpretable first-use time and monthly active status. Today, 19,142 usage rows precede linked subscription starts.
4. **Audit satisfaction and service friction (Customer Experience + Analytics, days 0–60).** Report satisfaction response coverage and account-level support rates with event time. KPI: missing satisfaction below 20% and account-clustered cohort comparisons; current missingness is 41.25% overall. Do not target an intervention based on the tiny retrospective mean difference.
5. **Run a randomized retention pilot after eligibility/revenue validation (CS + Finance/Analytics, days 60–90).** Randomize eligible renewing accounts by account, analyze intent-to-treat at a 90-day outcome with guardrails for support burden and discounting. KPI: incremental renewal/coverage retention and verified MRR retained. Do not use hypothetical Decision Lab lift as expected impact.

### Conditional financial sensitivity—not an impact claim

The Decision Lab uses generic units, not a currency or observed MRR. One illustrative arithmetic setting uses 60 historically affected accounts as a *reference pool only*, intervention cost 100 units per invited account (60 invitations → 6,000 units), monthly value 500 units per retained account, and six benefit months. With uptake/lift assumptions at 30%/2.5 pp, 60%/5 pp, 90%/7.5 pp, expected incremental retained accounts are 0.45 / 1.80 / 4.05; gross assumed benefit 1,350 / 5,400 / 12,150 units; net after 6,000 cost = −4,650 / −600 / +6,150 units. Break-even monthly value is 2,222 / 556 / 247 units. These cases are not forecasts, confidence intervals, observed revenue, or causal ROI; the pool is retrospective and must be replaced with a current eligible population and verified unit economics.

## Monthly interpretation

The 24-month ledger, including denominators and flows, plus monthly industry/country/referral comparisons are in [G4-MONTHLY-CHURN-ANALYSIS.md](G4-MONTHLY-CHURN-ANALYSIS.md). January 2023 opens at zero, so customer and plan rates are undefined for that month. All other monthly rate values are conditional date reconstruction. 2024-10 has the highest plan opening-cohort loss share (9/1,073 = 0.84%); 2024-12 has the largest absolute monthly plan-loss count (11). The same months need not lead on both measures.

## What remains unknown

- Commercially verified customer churn rate and causal root cause.
- Whether event frequency changed due to logging practice or customer behavior.
- Valid pre-churn activity and ticket timelines.
- Current MRR, revenue churn, LTV and actual dollars at risk.
- Calibrated future-risk accounts or proven intervention effect.

The challenge asks for a diagnostic, specific accounts, and prioritized actions with estimated impact. The solution provides the strongest defensible investigation and explicitly conditional scenario math; the economic effect remains partial until eligibility, revenue and intervention lift are observed.
