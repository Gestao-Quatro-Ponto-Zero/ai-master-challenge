# RavenStack — Beyond the Churn Headline

## A monthly, evidence-driven diagnosis of growth, retention and commercial movement

**Prepared by Thomas Leick**  
G4 AI Master Challenge 001 — Diagnóstico de Churn  
Independent submission · 22 October 2026

> RavenStack's records show more recorded churn events in 2024. They do not establish that its commercially verified customer churn rate increased. The right decision is to reconcile lifecycle and instrument customer-level outcomes before making a broad retention investment.

## Executive verdict

The classic customer churn rate is not identifiable from the source as a verified commercial KPI. The date-reconstructed ledger shows zero losses from the 190-account opening cohort in 2024, but also six complete coverage-loss episodes during the year, all within a system where account event records, account flags and subscription histories disagree. Those facts are not a certified 0% churn rate.

At the account × plan-tier proxy level, 7 of 374 opening relations lost coverage at least once in 2024 (1.87% conditional); 3 (0.80%) remained without that plan-tier coverage at year close. Fifty-four of 62 plan-proxy loss episodes across 2023–2024 occurred while the account retained another plan. Losing a plan is not necessarily losing a customer.

The apparent paradox is not established. Recorded event rows increased from 73 to 527 (+621.9%), but opening customer exposure rose from 845 to 3,909 account-months. Recorded events per 100 opening account-months rose from 8.64 to 13.48, while reconstructed complete-coverage-loss episode intensity fell from 0.237 to 0.153 per 100 account-months. These are different, conditional measures. They do not prove worsening customer retention or a change in event logging.

**Decision:** reconcile account/subscription lifecycle and event linkage first; review the 60 accounts with date-reconstructed plan losses, starting with the 8 complete-coverage-loss episodes that later returned; then run an account-randomized retention experiment only after a valid eligibility rule and primary outcome exist.

### Three answers to the CEO

**Q1 — What is causing churn?** No causal root cause is established. The strongest verified finding is a conflict among outcome indicators and lifecycle records. Feature, support and budget reasons are reported often, but are not causal evidence; usage and satisfaction are not reliably time-aligned to customer loss.

**Q2 — Which segments and accounts need attention?** Under the conditional 2024 plan-proxy opening cohort, Enterprise is 5/120 (4.17%), Basic 2/132 (1.52%), and Pro 0/122 (0.00%). The eight named accounts on page 5 experienced full date-derived coverage loss and later returned. They are reconciliation candidates, not predicted future churn.

**Q3 — What should RavenStack do?** Repair lifecycle identity and timestamps, review those historical cases, reconcile the explicit transition flags, instrument activation, then test CS outreach with account-level randomization and a verified 90-day customer-coverage outcome. Financial impact remains a formula-based scenario because recurring revenue is not reconciled.

## 1. The mathematics of growth

The daily source is a conditional account × plan-tier ledger. For executive reporting, each month's opening population is the denominator. Monthly rates are not sums or averages of daily rates.

| Measure | 2023 | 2024 | Interpretation |
|---|---:|---:|---|
| Opening customer exposure | 845 account-months | 3,909 account-months | 4.63× exposure; not unique customers |
| Recorded churn-event rows | 73 | 527 | Events, not customers lost |
| Event rows per 100 account-months | 8.64 | 13.48 | Recorded-event intensity; not customer churn |
| Plan-proxy loss episodes | 6 | 56 | Date-reconstructed coverage exits |
| Opening relation exposure | 1,406 relation-months | 9,414 relation-months | 6.70× exposure |
| Plan losses per 100 relation-months | 0.427 | 0.595 | Conditional episode intensity |
| Complete coverage-loss episodes | 2 | 6 | Each later regained coverage by the observation end |
| Complete-loss episodes per 100 account-months | 0.237 | 0.153 | Decreased despite higher absolute count |

The observed ledger grows from 190 customers / 374 plan-tier relations at the start of 2024 to 500 / 1,414 at year close. The bridge records 309 new customers, 7 customer reactivations and 6 complete-coverage-loss episodes in 2024; counts and cohort rates answer different questions. A symmetric arithmetic decomposition of the 454 additional event rows assigns about 339 to greater exposure and 115 to higher recorded-event intensity. This is an identity decomposition, not causal attribution. Changes in event-recording practice cannot be identified.

## 2. What the data actually says

All five source tables were inspected and used at their correct grains before comparison. Their joins are one-to-many; account-level outcomes are deduplicated before comparison.

- **Accounts:** 500 records; 110 account churn flags. Compared with any event history, 312 accounts differ: 75 have both, 35 are flag-only, 277 event-only, and 113 neither. These indicators may have different intended meanings.
- **Subscriptions:** 5,000 unique subscription IDs and three tiers. The fields `upgrade_flag` and `downgrade_flag` are present (529 and 218 true rows; 23 rows have both). They are row flags without a linked from/to tier or transition event. Recorded MRR/ARR fields are populated, but a reconciled revenue transition ledger is not present; sums across contract rows are not treated as verified loss or expansion.
- **Usage:** 25,000 rows. Recorded usage count increased from 124,561 to 125,964 (+1.13%) and from 24.462 to 24.747 per observed account-month (+1.17%). However, 19,142 rows predate the linked subscription start and 290 follow its end. The total is source-recorded activity, not validated adoption among active customers.
- **Support:** 2,000 tickets; satisfaction is missing on 825 (41.25%). For accounts with any event versus no event, mean scored ticket satisfaction was 3.9804 (815 scored, 580 missing) vs. 3.9833 (360 scored, 245 missing). Escalations were 71/1,395 (5.09%) vs. 24/605 (3.97%). Ticket rows cluster within accounts and are not temporally aligned to cancellation; no causal support effect is established.
- **Churn events:** 600 rows, including 73 in 2023 and 527 in 2024, across 352 accounts; 339 rows are marked non-reactivation. Reason rows: features 114, support 104, budget 104, unknown 95, competitor 92, pricing 91. Reason codes are recorded explanations, not verified root causes.

Of 62 date-derived plan-proxy losses, 54 occurred while another plan remained active; 8 coincided with complete account coverage loss and all 8 later regained date-derived coverage by the observation horizon. No event has a subscription ID link, so event-to-contract attribution is ambiguous.

## 3. Who needs attention?

The following 2024 segment results are opening-cohort plan-proxy losses, not future risk scores:

| Plan-tier proxy | Opening relations | Lost at any time | Rate | Still lost at year close |
|---|---:|---:|---:|---:|
| Enterprise | 120 | 5 | 4.17% | 2 |
| Basic | 132 | 2 | 1.52% | 1 |
| Pro | 122 | 0 | 0.00% | 0 |

The counts are small, labels are conditional on interval dates, and the tiers are not validated product identities. Industry exposure diagnostics also vary (e.g., 10 plan-loss rows over 2,215 relation-months in DevTools vs. 8 over 2,146 in FinTech). These do not establish industry causality.

Eight specific account IDs had at least one complete-coverage-loss episode followed by a return within the observed period. They are lifecycle-reconciliation cases, not calibrated future-risk candidates:

| Account | Segment | Plan at candidate record | Observed date-derived movement |
|---|---|---|---|
| A-180abf | DevTools · US · event | Pro | 2 plan-loss events; 1 complete-coverage-loss episode; later returned |
| A-0a282f | DevTools · US · organic | Basic | 1 plan loss and 1 complete-coverage-loss episode; later returned |
| A-0baac2 | FinTech · DE · organic | Enterprise | 1 plan loss and 1 complete-coverage-loss episode; later returned |
| A-40a557 | Cybersecurity · AU · partner | Pro | 1 plan loss and 1 complete-coverage-loss episode; later returned |
| A-410e86 | FinTech · US · organic | Basic | 1 plan loss and 1 complete-coverage-loss episode; later returned |
| A-432483 | Cybersecurity · US · ads | Pro | 1 plan loss and 1 complete-coverage-loss episode; later returned |
| A-8adedc | EdTech · US · event | Basic | 1 plan loss and 1 complete-coverage-loss episode; later returned |
| A-c9bb3e | EdTech · US · ads | Pro | 1 plan loss and 1 complete-coverage-loss episode; later returned |

## 4. Decision and impact

### Prioritized actions

1. **Lifecycle instrumentation — Data/Product Analytics, days 0–30.** Link every cancellation, reactivation and plan change to account and subscription IDs with effective timestamps. Success: proportion of lifecycle events linked to an eligible contract and reconciled against source records.
2. **Account reconciliation — Customer Success + RevOps, days 0–30.** Review the 60 accounts with date-derived plan losses; begin with the 8 complete-coverage-loss/return cases. Success: sampled cases classified with customer-confirmed outcome and documented reason.
3. **Transition audit — RevOps/Product, days 30–60.** Investigate the 529 upgrade and 218 downgrade subscription-row flags, including the 23 rows with both; do not infer a migration from a flag alone. Success: transitions have dated source/destination plan and comparable contract value.
4. **Activation and adoption instrumentation — Product Analytics, days 30–60.** Record a canonical activation event and meaningful feature adoption by eligible account cohort. Success: complete 7/30-day activation and adoption coverage for new cohorts.
5. **Controlled retention test — CS + Analytics, days 60–90.** Once eligibility and lifecycle are reliable, randomize eligible accounts (not tickets or subscription rows) to outreach vs. holdout. Primary outcome: verified customer coverage at 90 days; guardrails: plan downgrade, support burden and customer experience.

### Conditional impact model

There is no verified recurring-revenue baseline, so the paper does not state recovered revenue or ROI. For a sensitivity model only, the historical 60 accounts with any plan loss are a reference population, not an asserted current intervention list. If all 60 were eligible and contacted, assumed uptake/lift combinations of 50%/5 pp, 70%/10 pp, and 90%/15 pp imply 1.5, 4.2, and 8.1 incremental retained-account equivalents. With unit monthly contribution `V`, horizon `H` months, and contact cost `C`, modeled gross benefit is respectively `1.5VH`, `4.2VH`, and `8.1VH`; modeled net contribution is each amount minus `60C`. Break-even `V` is `60C/(retained equivalents × H)`. These are editable assumptions, not measured causal effects or company revenue.

## 5. Method, limits and laboratory

### Definitions

- **Customer churn rate:** unique eligible customers lost in the period ÷ unique active customers at the period opening. The commercial KPI is **not identifiable** because account flags, event records and interval coverage conflict.
- **Monthly plan-proxy opening-cohort gross loss:** distinct opening account × plan-tier relations that lose date-derived coverage at least once ÷ opening relations. In 2024: 7/374 = 1.87%.
- **Monthly plan-proxy closing loss:** opening-cohort relations still inactive at month close ÷ opening relations. In 2024: 3/374 = 0.80%.
- **Event intensity:** recorded event rows per reconstructed opening account-month. It is not a churn rate.

The daily ledger is the computational source; monthly is the executive frequency. Interval reconstruction uses `[start_date, end_date)` and treats a null end as open to the observed horizon. This is a reproducible conditional rule, not proof of effective commercial end. There is no `product_id`; `plan_tier` is only a plan-level proxy. Revenue changes, causal drivers and calibrated future risk remain unknown.

### Laboratory

Run the local application from `solution/` using `docker compose up --build`. The guided executive chapters and monthly business laboratory are complementary to this paper. Reproduction commands and data provenance are in `solution/README.md`; chronological prompts, corrections and test records are in `process-log/`. Local browser visual QA has not been demonstrated where browser access is denied.

### Sources

- G4 AI Master Challenge 001 — Diagnóstico de Churn: https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/blob/main/challenges/data-001-churn/README.md
- Submission guide: https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/blob/main/submission-guide.md
- Dataset: https://www.kaggle.com/datasets/rivalytics/saas-subscription-and-churn-analytics-dataset (synthetic; credit River @ Rivalytics; MIT per challenge/source metadata)
- Analytical source: `solution/analysis/daily_portfolio_churn/outputs/g4-alignment/daily-portfolio-churn.json`
- Five-table analysis: `solution/analysis/business_drivers/outputs/g4-alignment/business-investigation.json`

---

**Authorial mark:** Café · Cubo · Disciplina · Código  
Prepared by Thomas Leick. No personal credential or LinkedIn URL is asserted.
