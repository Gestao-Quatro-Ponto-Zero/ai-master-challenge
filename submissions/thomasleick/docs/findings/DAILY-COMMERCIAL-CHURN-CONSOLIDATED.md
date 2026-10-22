# Daily Commercial Churn — Consolidated Findings

**Project:** RavenStack — The Churn Paradox  
**Evidence classification:** `CONDITIONAL_DATE_RECONSTRUCTION`  
**Canonical grain:** account × plan tier × civil day  
**Actual product identity:** not identifiable; `plan_tier` is a **PLAN-LEVEL PROXY**  
**Observation window:** 2023-01-01 through 2024-12-31

## Executive conclusion

The source supports a reproducible daily reconstruction of account coverage by plan label. It does not identify products/services, verify the commercial meaning of every contract date, or provide a reconciled recurring-revenue ledger. The engine therefore reports conditional plan-proxy and account-coverage movements, not commercially verified product churn or revenue churn.

Across 731 civil days, the reconstructed ledger records **62 plan-proxy coverage losses** affecting **60 accounts**. **54 of the 62 loss events** occurred while the account still had another plan proxy active; the other **8 events** coincided with a complete loss of recorded plan coverage. Each of those eight accounts later regained coverage before the observation window ended. The result is eight gross, date-derived account-coverage loss events, eight subsequent account returns, and zero accounts without recorded coverage at the 2024-12-31 close. This is not evidence that a paid customer actually cancelled and returned: the relationship key is a plan-name proxy, and dates are not transaction timestamps.

The 2024 period ledger starts from the 2023-12-31 closing state: **190 accounts / 374 account-plan relations**. A date snapshot evaluated on 2024-01-01, after applying that date's starts, has **191 accounts / 379 relations**. Five relations begin on that date, including the first observed relation for one account. The annual ledger reports that boundary as daily movement; a classical calendar snapshot treats those same-date starts as already in the opening population. Both are shown because date-only data cannot establish the intraday ordering.

Recorded `mrr_amount` and `arr_amount` cannot be aggregated into observed revenue movement: currency, effective-period, versioning, and contract-lineage semantics are not established. Revenue expansion, contraction, gross revenue churn, net revenue churn, and actual lost MRR therefore remain **UNKNOWN**.

## 1. Source schema and product identity

The engine re-hashed all five original CSVs and recorded their real schemas in `analysis/daily_portfolio_churn/outputs/daily-portfolio-churn.json`.

| Table | Relevant fields | Role in this analysis |
|---|---|---|
| `ravenstack_accounts.csv` | `account_id`, `signup_date`, `plan_tier`, `industry`, `country`, `referral_source`, `seats`, `is_trial`, `churn_flag` | Account identifiers and descriptive segment attributes |
| `ravenstack_subscriptions.csv` | `subscription_id`, `account_id`, `start_date`, `end_date`, `plan_tier`, `mrr_amount`, `arr_amount`, `upgrade_flag`, `downgrade_flag`, `churn_flag`, `billing_frequency` | Date coverage and plan-level proxy; subscription ID is a contract-row key, not a product key |
| `ravenstack_feature_usage.csv` | `subscription_id`, `usage_date`, `feature_name`, `usage_count`, `usage_duration_secs`, `error_count`, `is_beta_feature` | Auxiliary usage evidence; no stable product identifier |
| `ravenstack_support_tickets.csv` | `account_id`, submission/closure timestamps, response/resolution measures, satisfaction, escalation | Account-level experience evidence; not linked to a particular plan |
| `ravenstack_churn_events.csv` | `account_id`, `churn_date`, `reason_code`, `refund_amount_usd`, reactivation marker, feedback | Account-level event context; no plan or subscription foreign key |

No stable product/service/SKU identifier exists in the source tables. `plan_tier` can group coverage labels, but it does not prove that each tier is a distinct service or that moving between tiers is a product migration. The canonical unit is consequently `(account_id, plan_tier, civil_date)`, explicitly **PLAN-LEVEL PROXY**. Subscription IDs are consolidated, not counted as products.

All five CSV hashes are part of the generated JSON metadata. They matched the preflight source hashes. The CSVs were not changed.

## 2. Temporal model and daily ledger

The candidate interval convention is **`[start_date, end_date)`**: a row starts coverage on `start_date`, and `end_date` is treated as the first inactive civil date. The dataset description says a populated end date means ended and a null end date means active, but does not establish exact inclusive/exclusive business timing. Dates have no known timezone or time-of-day. Thus all date-derived movement results remain conditional.

Null end dates are right-censored at 2024-12-31; they do not create an exit. Rows with missing/invalid starts or nonpositive intervals are not silently discarded: **13 nonpositive intervals** are listed in `invalid_intervals` and the output artifact. There are **1,476 merged account-plan coverage intervals** after overlapping and adjacent rows for the same account and plan are joined. The observation window is built from source dates and is 2023-01-01–2024-12-31; the earliest subscription start is 2023-01-09.

Daily state processing applies endings, then starts, then evaluates the end-of-day portfolio. Therefore a same-day plan swap registers the old relation loss and new relation start, while customer churn is counted only if no plan proxy remains at day close. If a relation has a coverage gap and later restarts, the restart is a plan reactivation; an unbroken or adjacent renewal is one continuous relation. Multiple simultaneous subscription rows for one account-plan pair do not multiply the relationship count.

For a day `d`:

```text
opening plan relations − plan losses + first relations + plan reactivations = closing plan relations
opening customers + new customers + customer reactivations − complete customer losses = closing customers
```

Both daily identities close on every day: **0 plan bridge failures; 0 customer bridge failures**. These arithmetic invariants validate the engine's state transitions, not the source's commercial semantics.

Rates are distinct measures:

```text
Daily plan-proxy churn = date-derived plan relations lost / plan relations active before that date's transitions
Daily customer churn = accounts losing all plan-proxy coverage / accounts covered before that date's transitions
```

When the corresponding opening population is zero, the rate is `null`/undefined rather than zero. Period churn is calculated against the period-opening cohort from daily states, never as a mean of daily percentages. The output separates cohort relations lost at any time, cohort relations still lost at period close, gross loss events (including newly acquired relations), and reactivations.

## 3. Observed daily movement totals

| Movement | Reconstructed total | What the count means |
|---|---:|---|
| Daily rows | 731 | One row per civil date in the observation window |
| New customers | 500 | First observed account coverage during the source window; not a verified billing acquisition count |
| New account-plan relations | 1,433 | First observed coverage for each account-plan proxy |
| Plan-proxy reactivations | 43 | Previously lost account-plan coverage later resumes |
| Gross plan-proxy loss events | 62 | Merged account-plan coverage intervals end during the window |
| Accounts with at least one plan loss | 60 | Distinct accounts with one or more of the 62 events |
| Loss events while another plan remains | 54 | Relationship loss does not equal complete account loss |
| Loss events coincident with complete account loss | 8 | Account's end-of-day coverage falls to zero |
| Accounts retaining another plan after a loss | 53 | Distinct accounts; one account may have multiple loss events |
| Accounts losing all plan coverage | 8 | Distinct accounts; all later return in the observed window |
| Customer reactivations | 8 | Complete coverage returns after a recorded zero-coverage interval |
| Portfolio expansion account-days | 949 | Active customers with a larger count of active plan proxies at day close |
| Portfolio contraction account-days | 53 | Customers remaining covered all day with a smaller plan-proxy count at close |
| Unique accounts with expansion / contraction | 495 / 52 | Distinct accounts with at least one such retained-customer day |

Expansion/contraction here is only a **change in count of plan labels**, not value, seats, pricing, or revenue. A customer acquisition/loss is kept separate from within-customer portfolio expansion/contraction. These are not additive churn totals.

## 4. Period results

All rows below aggregate the daily ledger. `Losses` is the gross plan-proxy loss-event count. `Opening cohort loss` counts unique relations from the opening population that lost coverage at any point during the period. `At close` counts the opening relations still inactive at the period end. Reactivation can make the two differ.

### Annual

| Year | Opening relations | First relations | Reactivations | Gross plan losses | Opening relations lost any time | Opening relations lost at close | Closing relations | Opening accounts | Gross customer-loss events | New accounts | Customer returns | Closing accounts | Plan bridge residual | Customer bridge residual |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 0 | 378 | 2 | 6 | 0 | 0 | 374 | 0 | 2 | 191 | 1 | 190 | 0 | 0 |
| 2024 | 374 | 1,055 | 41 | 56 | 7 | 3 | 1,414 | 190 | 6 | 309 | 7 | 500 | 0 | 0 |

For the 2024 opening relation cohort, **7/374 = 1.87%** had at least one loss during the year; **3/374 = 0.80%** remained inactive at year end; 4 of the 7 were active again at close. For the daily-ledger account opening population, **0/190 = 0%** had a date-derived full-coverage loss. The alternative 2024-01-01 calendar snapshot contains 191 accounts; its conditional ratio is also 0/191, but it treats same-day starts differently. Neither is a commercially verified churn KPI.

2023 opening denominators are zero, so annual opening-cohort rates are undefined. The two gross customer loss events during 2023 are not an opening-cohort churn rate: both involve accounts acquired in-period, and both accounts later return.

### Quarterly

| Quarter | Opening → closing relations | New / reactivated relations | Gross relation losses | Opening relations lost any time / at close | Opening → closing customers | Gross customer-loss events | Possible upgrades / downgrades* | Expansion / contraction account-days |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023-Q1 | 0 → 28 | 28 / 0 | 0 | 0 / 0 | 0 → 21 | 0 | 0 / 0 | 7 / 0 |
| 2023-Q2 | 28 → 105 | 78 / 0 | 1 | 0 / 0 | 21 → 71 | 1 | 0 / 1 | 26 / 0 |
| 2023-Q3 | 105 → 223 | 118 / 0 | 0 | 0 / 0 | 71 → 131 | 0 | 0 / 0 | 58 / 0 |
| 2023-Q4 | 223 → 374 | 154 / 2 | 5 | 3 / 2 | 131 → 190 | 1 | 3 / 5 | 96 / 4 |
| 2024-Q1 | 374 → 567 | 197 / 3 | 7 | 4 / 4 | 190 → 260 | 2 | 0 / 8 | 128 / 5 |
| 2024-Q2 | 567 → 807 | 237 / 9 | 6 | 4 / 2 | 260 → 337 | 1 | 6 / 2 | 168 / 5 |
| 2024-Q3 | 807 → 1,073 | 276 / 5 | 15 | 9 / 7 | 337 → 415 | 2 | 17 / 8 | 196 / 12 |
| 2024-Q4 | 1,073 → 1,414 | 345 / 24 | 28 | 13 / 5 | 415 → 500 | 1 | 26 / 27 | 270 / 27 |

### Semiannual

| Half | Opening → closing relations | New / reactivated relations | Gross relation losses | Opening relations lost any time / at close | Opening → closing customers | Gross customer-loss events | Possible upgrades / downgrades* | Expansion / contraction account-days |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023-H1 | 0 → 105 | 106 / 0 | 1 | 0 / 0 | 0 → 71 | 1 | 0 / 1 | 33 / 0 |
| 2023-H2 | 105 → 374 | 272 / 2 | 5 | 0 / 0 | 71 → 190 | 1 | 3 / 5 | 154 / 4 |
| 2024-H1 | 374 → 807 | 434 / 12 | 13 | 5 / 1 | 190 → 337 | 3 | 6 / 10 | 296 / 10 |
| 2024-H2 | 807 → 1,414 | 621 / 29 | 43 | 13 / 6 | 337 → 500 | 3 | 43 / 35 | 466 / 39 |

### Monthly and daily

Complete daily, weekly, monthly, quarterly, semiannual and annual results are generated in `analysis/daily_portfolio_churn/outputs/`. In particular, `daily-ledger.csv` contains all 731 daily rows; `movement-ledger.csv` contains every classified movement; monthly rows include zero-loss months as well as the loss periods. The 2024 monthly loss event counts are: Jan 3, Feb 3, Mar 1, Apr 4, May 2, Jul 5, Aug 5, Sep 5, Oct 9, Nov 8, Dec 11; June has no loss events. Period cohort counts and closing balances are in `monthly-portfolio-summary.csv`.

The largest observed gross loss concentration is 2024-Q4 (28 events) and December 2024 (11). This is an absolute date-derived count while the plan-proxy base grew rapidly; it does not by itself demonstrate deteriorating retention. In 2024-Q4, 13 of 1,073 opening relations had some loss (1.21%), while 5 (0.47%) remained inactive at quarter close. These rates are conditional plan-proxy cohort measures.

## 5. Plan proxy, expansion and contraction

| Plan label | Subscription source rows | Distinct accounts represented | Plan-proxy losses | First relations | Reactivations | 2024 opening relations | 2024 cohort lost any time | Lost at close | Closing relations |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Basic | 1,602 | 480 | 22 | 480 | 14 | 132 | 2 (1.52%) | 1 | 472 |
| Enterprise | 1,723 | 479 | 25 | 479 | 20 | 120 | 5 (4.17%) | 2 | 474 |
| Pro | 1,675 | 474 | 15 | 474 | 9 | 122 | 0 (0.00%) | 0 | 468 |

The plan labels show uneven observed counts, but this is not enough to conclude Enterprise is less retentive: the 2024 opening cohorts are small, there is no product/service identity, and date-derived statuses may be administrative. No confidence claim or causal conclusion is attached. The UI supports industry, country, referral source, account plan label, and trial-state views. For example, over the full window the conditional ledger records plan losses for 14/100 Cybersecurity accounts (14 events), 15/113 DevTools accounts (16 events), 7/79 EdTech accounts (7), 11/112 FinTech accounts (11), and 13/96 HealthTech accounts (14). The US has 38/291 accounts with at least one loss (40 events), including six accounts with a full-coverage loss. These are descriptive full-window counts, not comparable forward-looking risk rates.

At the subscription-row level, 529 rows carry `upgrade_flag` and 218 carry `downgrade_flag`; 23 rows carry both. These are **source-reported flags**, not validated movement counts. Unique accounts with those flags: 307 and 177 respectively. Do not merge them with date-inferred plan transitions.

## 6. Upgrade/downgrade sensitivity

There is no source-defined rank field or explicit old-plan/new-plan contract link. The engine uses the name order Basic < Pro < Enterprise only to create **possible** candidate pairs. No upgrade or downgrade is marked confirmed or inferred as a fact.

| Window from plan loss to different plan start | Possible upgrade pairs | Possible downgrade pairs | Accounts represented |
|---:|---:|---:|---:|
| Same day | 48 | 42 | 53 |
| ≤1 day | 49 | 43 | 53 |
| ≤7 days | 49 | 45 | 55 |
| ≤30 days | 52 | 51 | 57 |

The candidate inventory also records timing, including a different tier already active at the old tier's loss date. Such a case is not a confirmed migration. Increasing the window adds coincidences; the movement can only be called a possible upgrade/downgrade pending verified tier economics and contract linkage. Loss of an upper tier while a lower tier is already active is a portfolio contraction by plan count; calling it a downgrade remains an unverified interpretation.

## 7. Churn events and lifecycle conflicts

The source contains **600 account-level churn-event rows** across **352 distinct accounts**. It provides no subscription ID or plan key. Comparing each event to same-account date-derived plan losses:

| Absolute proximity to a plan-loss date | Event rows |
|---|---:|
| Same day | 0 / 600 |
| ≤1 day | 1 / 600 |
| ≤7 days | 4 / 600 |
| ≤30 days | 26 / 600 |
| ≤60 days | 37 / 600 |

The closest-date comparison is account-only and is not a causal or contract match. The window is symmetric in absolute distance. By reason, 114 events are labeled `features`, 104 `support`, 104 `budget`, 95 `unknown`, 92 `competitor`, and 91 `pricing`. At a 60-day account-level window, the counts are 5, 7, 7, 5, 10, and 3 respectively. A reason code is a recorded explanation, not independently established root cause. Most events do not coincide near a reconstructed plan loss; the reason why remains undocumented at the relationship level.

All eight date-reconstructed full-coverage-loss accounts later regain recorded coverage by the horizon close. Examples from the movement ledger: `A-432483` lost full coverage on 2023-04-05; `A-180abf` on 2023-11-06; `A-40a557` on 2024-01-16; `A-8adedc` on 2024-03-09; `A-c9bb3e` on 2024-04-02; `A-0baac2` on 2024-09-13; `A-0a282f` on 2024-09-25; and `A-410e86` on 2024-11-22. Each is a historical reconciliation candidate, not a predictive risk score or verified cancellation.

## 8. Economic interpretation

`mrr_amount` and `arr_amount` occur on subscription rows, but the data do not establish a currency code, a canonical effective date, whether rows are snapshots/versions, or the contract lineage needed to deduplicate values over time. Consequently:

- Historical MRR/ARR lost: **UNKNOWN**.
- Revenue contraction/expansion: **UNKNOWN**.
- Gross and net revenue churn: **UNKNOWN**.
- Lost LTV or recoverable revenue: **UNKNOWN**.
- Plan-count contraction: observed conditionally, but not a monetary proxy.
- `refund_amount_usd`: a refund field on event rows, not recurring revenue loss.

Leadership may use plan loss as an operational prompt to investigate contract changes, but must not translate it to dollars until a dated, currency-aware, deduplicated billing ledger is available.

## 9. Answers to the G4 challenge

### Q1 — What is associated with churn?

No cause is demonstrated. Under the conditional date reconstruction, 54/62 plan-proxy loss events happen while another plan label remains active; 8 coincide with full coverage loss, and all 8 accounts later return by the observed close. Only 37/600 account events fall within 60 days of any plan loss; the join is ambiguous. Reason codes offer customer-stated hypotheses but cannot establish cause. Usage, support, acquisition-fit and pricing hypotheses require reliable temporal alignment and verified customer outcomes.

### Q2 — Which accounts and segments need attention?

Investigate the eight full-coverage gap accounts above and all 60 accounts with a plan-proxy loss. They are historical reconciliation cases only. Segment counts are available by industry, country, acquisition source, account plan label and trial state in the API/UI and CSV artifacts. No future-risk model is supported by these data.

### Q3 — What should RavenStack do?

1. **Instrument contract lifecycle** (RevOps / Data): add durable customer, product/SKU, contract-line, effective start/end, cancellation, replacement, upgrade/downgrade, reactivation and currency-aware recurring-value fields. Success: daily account-product ledger reconciles exactly to billing and CRM.
2. **Reconcile the eight full-coverage gaps and 60 plan-loss accounts** (Customer Success / RevOps): review contract history and customer communications; record actual relationship outcome. Success: every candidate receives verified reason and successor link or remains explicitly unknown.
3. **Review churn-event taxonomy** (CX / Product Operations): require event type, affected contract/product, effective date and source; keep reason codes separate from status. Success: event-to-contract linkage completeness and lower unresolved conflict rate.
4. **Instrument activation and adoption** (Product Analytics / Customer Success): link usage to account-product and first-value milestones with event timestamps. Success: complete time-to-first-value and active-adoption cohorts.
5. **Then test a targeted retention intervention** (Customer Success / Analytics): randomize eligible verified at-risk relationships at account level, keep an untreated control, measure account retention and guardrails over an agreed renewal window. Do not use current date-proxy cases as a production churn model.

The 30/60/90-day sequence is: days 0–30 define and reconcile lifecycle contracts; days 31–60 complete instrumentation and baseline cohort definitions; days 61–90 run a powered pilot only after eligibility and outcomes are reliable. Cost, effect and ROI are unestimated because no operational cost or causal uplift evidence is present.

## 10. G4 cohort framing

The public G4 article describes cohorts as groups sharing a time-based entry event and recommends tracking how their behavior changes over elapsed periods, comparing cohorts to understand acquisition effectiveness and retention. This solution applies that general longitudinal framing to account-plan coverage and aggregates one canonical daily ledger. The ledger mechanics and assumed tier ordering are our implementation, not a proprietary G4 formula. Existing account acquisition-cohort diagnostics remain separate. The plan-proxy period tables here are **opening-period cohorts**, not a full acquisition-month retention heatmap.

Source: [G4 — O que é análise cohort? Tudo que você precisa saber](https://g4educacao.com/blog/analise-de-coorte). Direct automated fetch returned HTTP 403 in this run; the indexed public result exposed the article content. No protected course content was accessed.

## 11. Application and reproducibility

Added isolated engine `solution/analysis/daily_portfolio_churn/`; it reads the unchanged five raw CSVs, calculates daily interval states and materializes JSON/CSV outputs. API endpoint: `GET /api/daily-portfolio-churn`. Chapter 02 now displays plan-proxy losses, account losses, daily and selectable period aggregates, plan breakdown, transition-window sensitivity, segments, account reconciliation candidates, source upgrade/downgrade flags, boundary snapshots, event conflicts, and visible UNKNOWN financial fields.

Reproduce from the standalone submission runtime root:

```bash
cd submissions/thomasleick/solution
PYTHONPATH=analysis python3.12 -m daily_portfolio_churn --data-dir data/raw --output-dir analysis/daily_portfolio_churn/outputs
```

Key outputs: `daily-portfolio-churn.json`, `daily-ledger.csv`, `movement-ledger.csv`, `weekly-portfolio-summary.csv`, `monthly-portfolio-summary.csv`, `quarterly-portfolio-summary.csv`, `semiannual-portfolio-summary.csv`, `annual-portfolio-summary.csv`, and `plan-proxy-summary.csv`.

## 12. Validation evidence and limitations

- Daily analysis regenerated successfully from the original CSVs; all five SHA-256 hashes are in JSON output.
- Python API + engine tests in Docker: **30 passed**, one upstream Starlette/AnyIO deprecation warning. The final run includes explicit same-day-start boundary and invalid-interval preservation tests.
- Ruff on the new analysis, API schema, endpoint and API tests: passed. First invocation failed because the unprivileged container could not create the default Ruff cache; rerun with `RUFF_CACHE_DIR=/tmp/ruff-cache` passed. Ruff found one unused local, which was removed before the passing run.
- Frontend Vitest: **6 passed**. TypeScript/Vite build passed; Vite reports a 703.02 kB minified JS bundle (194.92 kB gzip), above its 500 kB advisory threshold.
- `docker compose config --quiet`: passed. Project services rebuilt/recreated under existing project `ravenstack-g4-final`; API healthy at `http://localhost:18200`, frontend healthy at `http://localhost:15175`.
- Runtime smoke checks: `/api/health`, `/api/daily-portfolio-churn`, frontend root, and frontend API proxy returned HTTP 200. Direct API and proxy reported the same 62 loss events and 8 full-coverage-loss events. The response included the 2024 boundary snapshot and calendar transition opening values.
- Docker emitted a warning that buildx is unavailable and used the legacy builder. Images still built successfully.
- Browser visual inspection was denied by the browser security surface for the local URL. No alternative browser or execution path was attempted. Rendered visual behavior, viewport layout and live navigation are **UNKNOWN** in this run; screenshots were not captured.
- Date-only timestamps, unknown timezone, synthetic source data, uncertain commercial meaning of plan labels/end dates, account-only event joins, unverified plan hierarchy, right censoring at 2024-12-31, and non-reconciled MRR/ARR prevent commercial validation.

### Evidence status

**Demonstrated:** deterministic account-plan ledger, daily/period bridge invariants, output generation, schema-validated API, frontend test/build, local container health, direct and proxied HTTP responses.  
**Conditional:** every historical churn, return, segment, and plan-transition result derived from dates and plan names.  
**Unknown:** product-level churn, commercially confirmed logo churn, actual revenue churn, causal drivers, calibrated future risk, and browser visual QA.
