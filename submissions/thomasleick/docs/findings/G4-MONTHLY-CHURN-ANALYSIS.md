# Monthly churn, customer base growth and retention dynamics

**Scope:** Challenge 001 addendum; analysis generated from the five submitted CSVs. **Evidence:** conditional date reconstruction for commercial lifecycle; observed source rows for usage/events/support. **Grain:** account × `plan_tier` × civil day (plan-level proxy), projected to months from one daily ledger. The month is the executive reporting frequency; daily, quarterly, semiannual and annual views remain derived secondary views.

## Interpretation in one minute

Absolute recorded churn events rose from **73 in 2023 to 527 in 2024** (7.22×), while the reconstructed opening-customer exposure grew from **845 to 3,909 account-months** (4.63×). Events per 100 reconstructed opening account-months also rose from **8.64 to 13.48** (+56.1%). This is event-recording intensity, not customer churn. Date-reconstructed plan loss events rose **6→56** while opening plan-relation exposure grew **1,406→9,414 relation-months**; conditional plan-loss intensity increased **0.427→0.595 per 100 relation-months** (+39.4%). Complete account-coverage loss episodes rose **2→6**, but their reconstructed exposure rate fell **0.237→0.153 per 100 account-months** (-35.1%). These conflicting movements mean absolute volume is not a single retention story.

Source feature-usage counts were nearly flat: **124,561→125,964** (+1.13%), and **24.462→24.747 per observed account-month** (+1.17%). 500 distinct accounts were present in each annual source summary, but date-linked usage has serious lifecycle mismatch (19,142 rows before linked subscription start and 290 after non-null end under this analysis's documented inclusive range test). The data therefore do **not** establish a broad increase in valid adoption or a causal contradiction with retention.

**Conclusion:** the proposition “higher absolute churn-event volume necessarily means worsening retention” is contradicted as a rule. In RavenStack, counts rose partly alongside much greater reconstructed exposure; some exposure-normalized event and plan-proxy measures also rose, while the account-level complete-coverage episode rate fell. Because event semantics, active eligibility, and dates are unresolved, the data **cannot establish whether verified commercial customer churn worsened**. Changes in event-recording frequency are not separately identifiable from changes in underlying events.

## Methods and definitions

- **Opening base:** unique accounts or account–plan proxy relationships active immediately before the first day's movements of a month, under `[start_date, end_date)` and merged overlapping/contiguous same-account, same-plan intervals.
- **Monthly gross opening-cohort plan loss:** opening cohort relationships with at least one coverage loss during month ÷ opening relationships. This is a conditional plan-proxy cohort loss rate; daily rates are never summed or averaged into it.
- **Monthly closing plan loss:** opening cohort relationships still inactive at month end ÷ opening relationships. A lost-then-reactivated relationship is counted in gross cohort loss, not closing loss.
- **Customer measure:** analogous account-level complete loss of all plan proxies. `gross_customer_churn_events` counts within-month full-coverage-loss episodes (including accounts acquired during the month); `opening_customers_lost_any_time` isolates only the opening account cohort.
- **Events:** source event rows and distinct event accounts; normalized event rows per opening customer are recording intensity, not churn. January 2023 has zero opening population, so rates are `UNDEFINED`, not zero.
- **Flow bridge:** each monthly row is an aggregation of daily movements. The sum of daily residuals is zero; the monthly opening + new + reactivated − gross loss = closing identity holds for both account–plan relations and customer coverage in all 24 months. This validates arithmetic only, not business semantics.
- **Composition:** monthly `plan_segments` are available from the ledger output, with opening population, first acquisitions, returns, losses and closing population by recorded plan tier. Tier order is not assumed for possible upgrades/downgrades.

### Data hashes

- `ravenstack_accounts.csv`: `348d8ba906b7776894b5236b2e7aa91a503d41670dbc9aad30c37b503c9abef5`
- `ravenstack_subscriptions.csv`: `dcf1d93ca9a35e0dcba0ab686d255f0e9ec26512970bbf0944cf19cbef2d751a`
- `ravenstack_feature_usage.csv`: `c081da2be8caf987d07f0f79ceb0619aba523d819529230ed6df77984fa21d4e`
- `ravenstack_support_tickets.csv`: `ba0006951479771ee9f93c98789c96bc5fec892cf11f867afb28194f0b76d220`
- `ravenstack_churn_events.csv`: `6391c41d8291b7b4845ec9a84d3837c2ed230a33a32a854ec33d4e66dc150940`

## 24-month ledger summary

Rates are percentages. “Opening-cohort customer losses” and “opening-cohort plan losses” count unique opening units with any loss within the month; closing loss is a separate net state. “Gross loss episodes” are event counts, including in-period entrants. Recorded event rows are not linked to a plan. The `*` event intensity column is undefined at a zero opening customer base.

| Month | Open customers | New | Reactivated | Gross customer-loss episodes | Opening-cohort customer losses / rate | Close customers | Open plan proxies | New plan relations | Plan reactivations | Gross plan-loss events | Opening-cohort plan losses / rate | Opening cohort still lost at close / rate | Close plan proxies | Event rows / accounts | Event rows per 100 open customers* | Possible upgrades | Possible downgrades | Portfolio expansion days | Portfolio contraction days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023-01 | 0 | 2 | 0 | 0 | 0/0 · UNDEFINED | 2 | 0 | 3 | 0 | 0 | 0/0 · UNDEFINED | 0/0 · UNDEFINED | 3 | 1/1 | UNDEFINED | 0 | 0 | 1 | 0 |
| 2023-02 | 2 | 8 | 0 | 0 | 0/2 · 0.00% | 10 | 3 | 10 | 0 | 0 | 0/3 · 0.00% | 0/3 · 0.00% | 13 | 0/0 | 0.00% | 0 | 0 | 2 | 0 |
| 2023-03 | 10 | 11 | 0 | 0 | 0/10 · 0.00% | 21 | 13 | 15 | 0 | 0 | 0/13 · 0.00% | 0/13 · 0.00% | 28 | 5/5 | 50.00% | 0 | 0 | 4 | 0 |
| 2023-04 | 21 | 15 | 1 | 1 | 0/21 · 0.00% | 36 | 28 | 23 | 0 | 1 | 0/28 · 0.00% | 0/28 · 0.00% | 50 | 3/3 | 14.29% | 0 | 1 | 7 | 0 |
| 2023-05 | 36 | 14 | 0 | 0 | 0/36 · 0.00% | 50 | 50 | 21 | 0 | 0 | 0/50 · 0.00% | 0/50 · 0.00% | 71 | 3/3 | 8.33% | 0 | 0 | 7 | 0 |
| 2023-06 | 50 | 21 | 0 | 0 | 0/50 · 0.00% | 71 | 71 | 34 | 0 | 0 | 0/71 · 0.00% | 0/71 · 0.00% | 105 | 5/5 | 10.00% | 0 | 0 | 12 | 0 |
| 2023-07 | 71 | 18 | 0 | 0 | 0/71 · 0.00% | 89 | 105 | 36 | 0 | 0 | 0/105 · 0.00% | 0/105 · 0.00% | 141 | 6/6 | 8.45% | 0 | 0 | 18 | 0 |
| 2023-08 | 89 | 27 | 0 | 0 | 0/89 · 0.00% | 116 | 141 | 49 | 0 | 0 | 0/141 · 0.00% | 0/141 · 0.00% | 190 | 7/6 | 7.87% | 0 | 0 | 22 | 0 |
| 2023-09 | 116 | 15 | 0 | 0 | 0/116 · 0.00% | 131 | 190 | 33 | 0 | 0 | 0/190 · 0.00% | 0/190 · 0.00% | 223 | 6/6 | 5.17% | 0 | 0 | 18 | 0 |
| 2023-10 | 131 | 18 | 0 | 0 | 0/131 · 0.00% | 149 | 223 | 40 | 0 | 1 | 1/223 · 0.45% | 1/223 · 0.45% | 262 | 10/10 | 7.63% | 2 | 0 | 22 | 1 |
| 2023-11 | 149 | 22 | 0 | 1 | 1/149 · 0.67% | 170 | 262 | 60 | 0 | 2 | 2/262 · 0.76% | 2/262 · 0.76% | 320 | 11/11 | 7.38% | 1 | 1 | 38 | 1 |
| 2023-12 | 170 | 20 | 0 | 0 | 0/170 · 0.00% | 190 | 320 | 54 | 2 | 2 | 2/320 · 0.62% | 2/320 · 0.62% | 374 | 16/16 | 9.41% | 0 | 4 | 36 | 2 |
| 2024-01 | 190 | 26 | 1 | 1 | 0/190 · 0.00% | 216 | 374 | 59 | 0 | 3 | 2/374 · 0.53% | 2/374 · 0.53% | 430 | 20/18 | 10.53% | 0 | 3 | 32 | 2 |
| 2024-02 | 216 | 18 | 1 | 0 | 0/216 · 0.00% | 235 | 430 | 61 | 1 | 3 | 3/430 · 0.70% | 3/430 · 0.70% | 489 | 10/10 | 4.63% | 0 | 3 | 43 | 3 |
| 2024-03 | 235 | 25 | 1 | 1 | 1/235 · 0.43% | 260 | 489 | 77 | 2 | 1 | 1/489 · 0.20% | 0/489 · 0.00% | 567 | 24/24 | 10.21% | 0 | 2 | 53 | 0 |
| 2024-04 | 260 | 22 | 1 | 1 | 0/260 · 0.00% | 282 | 567 | 76 | 4 | 4 | 3/567 · 0.53% | 3/567 · 0.53% | 643 | 25/23 | 9.62% | 5 | 0 | 57 | 3 |
| 2024-05 | 282 | 28 | 0 | 0 | 0/282 · 0.00% | 310 | 643 | 78 | 3 | 2 | 2/643 · 0.31% | 1/643 · 0.16% | 722 | 27/25 | 9.57% | 1 | 2 | 53 | 2 |
| 2024-06 | 310 | 27 | 0 | 0 | 0/310 · 0.00% | 337 | 722 | 83 | 2 | 0 | 0/722 · 0.00% | 0/722 · 0.00% | 807 | 40/38 | 12.90% | 0 | 0 | 58 | 0 |
| 2024-07 | 337 | 28 | 0 | 0 | 0/337 · 0.00% | 365 | 807 | 87 | 2 | 5 | 5/807 · 0.62% | 4/807 · 0.50% | 891 | 35/33 | 10.39% | 8 | 0 | 61 | 5 |
| 2024-08 | 365 | 20 | 0 | 0 | 0/365 · 0.00% | 385 | 891 | 85 | 2 | 5 | 4/891 · 0.45% | 3/891 · 0.34% | 973 | 42/40 | 11.51% | 5 | 4 | 65 | 5 |
| 2024-09 | 385 | 31 | 1 | 2 | 2/385 · 0.52% | 415 | 973 | 104 | 1 | 5 | 3/973 · 0.31% | 2/973 · 0.21% | 1,073 | 53/48 | 13.77% | 4 | 4 | 70 | 2 |
| 2024-10 | 415 | 23 | 1 | 0 | 0/415 · 0.00% | 439 | 1,073 | 96 | 6 | 9 | 9/1073 · 0.84% | 7/1073 · 0.65% | 1,166 | 66/60 | 15.90% | 9 | 7 | 76 | 9 |
| 2024-11 | 439 | 36 | 1 | 1 | 0/439 · 0.00% | 475 | 1,166 | 113 | 8 | 8 | 5/1166 · 0.43% | 3/1166 · 0.26% | 1,279 | 68/60 | 15.49% | 8 | 8 | 80 | 7 |
| 2024-12 | 475 | 25 | 0 | 0 | 0/475 · 0.00% | 500 | 1,279 | 136 | 10 | 11 | 5/1279 · 0.39% | 2/1279 · 0.16% | 1,414 | 117/96 | 24.63% | 9 | 12 | 114 | 11 |

## Growth versus normalized measures

| Unit / measure | 2023 | 2024 | Change | Interpretation |
|---|---:|---:|---:|---|
| Recorded churn-event rows | 73 | 527 | +454 (621.9%) | Event rows, not unique lost customers |
| Reconstructed opening account-months | 845 | 3,909 | +4.63× | Exposure denominator; conditional dates |
| Event rows / 100 opening account-months | 8.64 | 13.48 | +56.1% | Recording/event intensity; not customer churn |
| Plan-proxy loss episodes | 6 | 56 | +50 | Conditional reconstructed coverage loss |
| Opening plan-relation-months | 1,406 | 9,414 | +6.70× | Exposure denominator |
| Plan-loss episodes / 100 relation-months | 0.427 | 0.595 | +39.4% | Conditional plan-level proxy intensity |
| Complete customer coverage-loss episodes | 2 | 6 | +4 | Full plan-proxy coverage reached zero; conditional |
| Customer-loss episodes / 100 account-months | 0.237 | 0.153 | -35.1% | Episode intensity fell despite absolute count rising |
| Recorded usage count | 124,561 | 125,964 | +1.13% | Source volume, not valid active-customer adoption |
| Usage count / observed account-month | 24.462 | 24.747 | +1.17% | Descriptive; source observation mismatch |

A symmetric rate/exposure decomposition of the 454 additional event rows is arithmetic, not causal: using each year's event intensity and opening account-month exposure, roughly **339 rows** of the difference are attributable to the larger exposure term and **115 rows** to the higher recorded-event intensity term. For the 50 additional plan loss episodes, the analogous decomposition is about **40.9** exposure-associated and **9.1** rate-associated episodes. These fractional contributions explain the identity `count = exposure × rate`; they do not prove why either input changed. A valid event-logging baseline is absent, so the event-recording effect is **NOT IDENTIFIABLE**.

Customer-base composition also changed: daily-ledger opening/closing customer coverage moved from 0 to 190 during 2023 and from 190 to 500 during 2024; plan proxies from 0 to 374 and 374 to 1,414. Monthly opening exposures are therefore substantially different. The synthetic usage source, however, shows 500 accounts and about 5,090 observed account-months in each year, not an aligned population of active subscription customers. A causal composition adjustment is **NOT IDENTIFIABLE** from these mismatched observation frames.

## Segment and support context

End-of-year plan-proxy composition stayed close to one-third per recorded tier even as the relation base expanded. This does not rule out composition effects within industry, country or acquisition cohorts, but it shows that the top-line growth was not a simple shift to one plan tier.

| Close date | Basic | Enterprise | Pro | Total relations |
|---|---:|---:|---:|---:|
| 2023-12-31 | 132 (35.29%) | 120 (32.09%) | 122 (32.62%) | 374 |
| 2024-12-31 | 472 (33.38%) | 474 (33.52%) | 468 (33.10%) | 1,414 |

Within monthly plan-tier outputs, 2024-12 had the most absolute plan-proxy loss episodes (**11**), while 2024-10 had the highest opening-cohort plan-loss proportion (**9/1,073 = 0.84%**). 2023-11 was the highest 2023 month (**2/262 = 0.76%**). These are low counts under a fast-growing relation base; no trend significance is claimed. Monthly plan-level breakdown is in `outputs/g4-alignment/monthly-plan-segment-summary.csv`; the new `outputs/g4-alignment/monthly-account-segment-summary.csv` reports customer and plan flows by industry, country and referral source for each month. The frontend exposes the same monthly segment table with separate opening customer and opening account-plan denominators, and flags segment-months with fewer than 30 opening customers. Rates are displayed month by month, not summed into annual churn.

The all-time `any_event` label groups are retrospective and non-temporal. Accounts with any event had 1,395 ticket rows across 352 accounts; no-event accounts had 605 rows across 148 accounts. Ticket satisfaction means were **3.9804 (815 scored; 580 missing)** and **3.9833 (360 scored; 245 missing)**. Median first response was 89 vs. 87 minutes; median resolution 35 hours in both groups; ticket escalations were 71/1,395 (5.09%) vs. 24/605 (3.97%). Overall 825/2,000 (41.25%) satisfaction scores were missing. Ticket rows are clustered within accounts, labels lack reliable event time, and missingness is material; these small descriptive differences do not establish support as a cause or protection factor.

### 2024 industry exposure diagnostic

The table below aggregates monthly opening-cohort loss counts over opening account-month exposures. It is a descriptive exposure diagnostic, not an annual churn rate: a customer may contribute observations in more than one month if the reconstructed state changes. Small numerators and conditional date semantics prevent ranking these groups as future risk.

| Industry | Opening account-months | Monthly opening-cohort customer loss rows | Customer loss rows / 100 account-months | Opening relation-months | Monthly opening-cohort plan loss rows | Plan loss rows / 100 relation-months |
|---|---:|---:|---:|---:|---:|---:|
| Cybersecurity | 743 | 0 | 0.000 | 1,716 | 9 | 0.524 |
| DevTools | 894 | 1 | 0.112 | 2,215 | 10 | 0.451 |
| EdTech | 601 | 1 | 0.166 | 1,400 | 6 | 0.429 |
| FinTech | 892 | 1 | 0.112 | 2,146 | 8 | 0.373 |
| HealthTech | 779 | 0 | 0.000 | 1,937 | 9 | 0.465 |

Each individual monthly row remains available for industry, country and referral source; rates are unstable where monthly opening denominators are small. These results do not identify an acquisition-fit or industry cause.

## Evidence conclusions

- **Verified observations:** counts from source rows; reproducible interval-derived populations and monthly arithmetic; event and usage records as recorded.
- **Conditional results:** active customer/plan coverage, losses, reactivations, normalized coverage measures under the date rule; all rates above involving lifecycle reconstruction.
- **Not established:** certified historical customer churn rate, causal retention trend, event logging change, valid pre-loss usage/satisfaction effect, revenue churn, or an explanation for event volume growth.
- **Does growth explain absolute losses?** Larger exposure explains an important portion of count growth as an arithmetic decomposition, but conditional plan loss and event-record intensity also rise. Complete coverage-loss episode intensity falls. The mixed indicators are evidence against treating event counts as a customer-retention KPI.

## Reproduction

From `solution/`:

```bash
PYTHONPATH=analysis python -m daily_portfolio_churn --data-dir data/raw --output-dir analysis/daily_portfolio_churn/outputs/g4-alignment
python analysis/business_drivers/run.py --data-dir data/raw --output-dir analysis/business_drivers/outputs/g4-alignment
PYTHONPATH=analysis python -m unittest discover -s analysis/daily_portfolio_churn/tests -v
python -m unittest discover -s analysis/business_drivers/tests -v
```

## Executive dashboard presentation

The Chapter 02 default is a visible 24-month view, not an annual-only comparison. It has a rate line chart with four separate series: gross opening-cohort plan-proxy loss, plan-proxy relations still lost at month close, gross opening-cohort complete customer coverage loss, and customers still without coverage at close. The movement chart separates plan loss events, persistent opening-cohort plan losses, complete customer loss events, new plan relations, new customers, and both kinds of reactivation. Its 24-row table reports both gross event counts and opening-cohort loss numerators/rates, plus acquisitions, reactivations and closing bases.

Each rate uses its unit-specific opening base. Chart tooltips show numerator, denominator, formula and conditional evidence classification; the table repeats the formula/denominator in each rate cell. January 2023 remains `UNDEFINED` for zero opening populations. Annual events-per-100-account-month and events-per-100-relation-month diagnostics stay in this report and are not rendered as monthly churn rates. The component is `solution/apps/web/src/features/monthly/MonthlyChurnView.tsx`.

**Validation:** Vitest verifies 24 plotted monthly records and table rows, correct account versus plan denominators and the zero-base `UNDEFINED` state. Current API JSON contains 24 rows and was compared field-by-field with `outputs/g4-alignment/monthly-portfolio-summary.csv`. The built frontend bundle contains the new monthly view. A browser navigation to the running local app was explicitly denied by browser security policy, so desktop/mobile visual rendering is not claimed as verified.

## Revalidated monthly results — 24 months

The table below is read from the running `GET /api/daily-portfolio-churn` endpoint after rebuilding the submission Compose package. “Customer” counts complete account coverage loss; “plan proxy” counts unique account × plan-tier relations. Each group is ordered as: opening base; gross loss events (all relationships); opening-cohort relations/customers lost at any time / rate; opening-cohort still lost at close / rate; new customers/relations; reactivations; closing base. Rates are conditional date reconstructions. January 2023 has a zero opening denominator, so the rates are UNDEFINED.

| Month | Customer coverage (opening; loss events; cohort gross lost/rate; still lost/rate; new; reactivated; closing) | Plan-level proxy (opening; loss events; cohort gross lost/rate; still lost/rate; new; reactivated; closing) |
|---|---|---|
| 2023-01 | 0; 0; 0/UNDEFINED; 0/UNDEFINED; 2; 0; 2 | 0; 0; 0/UNDEFINED; 0/UNDEFINED; 3; 0; 3 |
| 2023-02 | 2; 0; 0/0.00%; 0/0.00%; 8; 0; 10 | 3; 0; 0/0.00%; 0/0.00%; 10; 0; 13 |
| 2023-03 | 10; 0; 0/0.00%; 0/0.00%; 11; 0; 21 | 13; 0; 0/0.00%; 0/0.00%; 15; 0; 28 |
| 2023-04 | 21; 1; 0/0.00%; 0/0.00%; 15; 1; 36 | 28; 1; 0/0.00%; 0/0.00%; 23; 0; 50 |
| 2023-05 | 36; 0; 0/0.00%; 0/0.00%; 14; 0; 50 | 50; 0; 0/0.00%; 0/0.00%; 21; 0; 71 |
| 2023-06 | 50; 0; 0/0.00%; 0/0.00%; 21; 0; 71 | 71; 0; 0/0.00%; 0/0.00%; 34; 0; 105 |
| 2023-07 | 71; 0; 0/0.00%; 0/0.00%; 18; 0; 89 | 105; 0; 0/0.00%; 0/0.00%; 36; 0; 141 |
| 2023-08 | 89; 0; 0/0.00%; 0/0.00%; 27; 0; 116 | 141; 0; 0/0.00%; 0/0.00%; 49; 0; 190 |
| 2023-09 | 116; 0; 0/0.00%; 0/0.00%; 15; 0; 131 | 190; 0; 0/0.00%; 0/0.00%; 33; 0; 223 |
| 2023-10 | 131; 0; 0/0.00%; 0/0.00%; 18; 0; 149 | 223; 1; 1/0.45%; 1/0.45%; 40; 0; 262 |
| 2023-11 | 149; 1; 1/0.67%; 1/0.67%; 22; 0; 170 | 262; 2; 2/0.76%; 2/0.76%; 60; 0; 320 |
| 2023-12 | 170; 0; 0/0.00%; 0/0.00%; 20; 0; 190 | 320; 2; 2/0.62%; 2/0.62%; 54; 2; 374 |
| 2024-01 | 190; 1; 0/0.00%; 0/0.00%; 26; 1; 216 | 374; 3; 2/0.53%; 2/0.53%; 59; 0; 430 |
| 2024-02 | 216; 0; 0/0.00%; 0/0.00%; 18; 1; 235 | 430; 3; 3/0.70%; 3/0.70%; 61; 1; 489 |
| 2024-03 | 235; 1; 1/0.43%; 0/0.00%; 25; 1; 260 | 489; 1; 1/0.20%; 0/0.00%; 77; 2; 567 |
| 2024-04 | 260; 1; 0/0.00%; 0/0.00%; 22; 1; 282 | 567; 4; 3/0.53%; 3/0.53%; 76; 4; 643 |
| 2024-05 | 282; 0; 0/0.00%; 0/0.00%; 28; 0; 310 | 643; 2; 2/0.31%; 1/0.16%; 78; 3; 722 |
| 2024-06 | 310; 0; 0/0.00%; 0/0.00%; 27; 0; 337 | 722; 0; 0/0.00%; 0/0.00%; 83; 2; 807 |
| 2024-07 | 337; 0; 0/0.00%; 0/0.00%; 28; 0; 365 | 807; 5; 5/0.62%; 4/0.50%; 87; 2; 891 |
| 2024-08 | 365; 0; 0/0.00%; 0/0.00%; 20; 0; 385 | 891; 5; 4/0.45%; 3/0.34%; 85; 2; 973 |
| 2024-09 | 385; 2; 2/0.52%; 1/0.26%; 31; 1; 415 | 973; 5; 3/0.31%; 2/0.21%; 104; 1; 1073 |
| 2024-10 | 415; 0; 0/0.00%; 0/0.00%; 23; 1; 439 | 1073; 9; 9/0.84%; 7/0.65%; 96; 6; 1166 |
| 2024-11 | 439; 1; 0/0.00%; 0/0.00%; 36; 1; 475 | 1166; 8; 5/0.43%; 3/0.26%; 113; 8; 1279 |
| 2024-12 | 475; 0; 0/0.00%; 0/0.00%; 25; 0; 500 | 1279; 11; 5/0.39%; 2/0.16%; 136; 10; 1414 |

The customer and plan values are not interchangeable. Gross loss events can include relationships acquired after the month opened; opening-cohort losses count distinct members of that opening population. A relationship lost and later reactivated in the same month may contribute to gross loss while remaining active at close. The endpoint is the source of the displayed series; all 24 monthly rows and 19 fields were matched to `outputs/g4-alignment/monthly-portfolio-summary.csv`.
