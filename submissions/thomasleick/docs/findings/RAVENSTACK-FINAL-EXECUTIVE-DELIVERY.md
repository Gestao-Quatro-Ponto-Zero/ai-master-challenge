# RavenStack — Final Executive Delivery

**G4 AI Master Challenge 001 · Consolidation run: 2026-10-22**

## Executive thesis

RavenStack's data show daily movement in account × plan coverage, but do not establish commercially verified customer churn. The only defensible primary customer-churn answer remains **UNKNOWN**. A separate, date-derived plan-proxy calculation shows 7 of 374 opening 2024 account-plan relations lost coverage at least once (1.87%); 3 of 374 were still without coverage at year close (0.80%); none of the 190 opening accounts lost all plan-proxy coverage under that date rule (0/190). These are conditional reconstructions, not certified commercial KPIs.

Across 2023–2024, the daily ledger reconstructs 62 account × plan-proxy loss events affecting 60 accounts. In 54 of the 62 events, another plan proxy remained active; 8 coincided with all account coverage reaching zero. All eight accounts later regained some plan-proxy coverage within the observed window. This describes lifecycle motion under source dates, not confirmed product cancellation, future risk or causal churn.

## The decision in five minutes

| Executive question | Answer supported by the evidence |
|---|---|
| **What is causing churn?** | No causal root cause is established. Recorded event reasons are not linked to subscriptions; account status, event history and date-derived coverage conflict. The immediate finding is measurement and lifecycle reconciliation debt. |
| **Who needs attention?** | Sixty accounts had at least one reconstructed plan-proxy loss; eight had a complete coverage gap followed by return. These are retrospective reconciliation cases, not predicted-risk accounts. Enterprise has 5/120 opening plan proxies with at least one conditional 2024 loss (4.17%), Basic 2/132 (1.52%), and Pro 0/122 (0.00%). Plan identity/order and date semantics remain conditional; do not interpret this as validated segment risk. |
| **What should RavenStack do?** | First link lifecycle events to stable contract/product keys and validate active status and recurring value. Reconcile the 60 account records and eight full-gap timelines. Then measure account cohorts and run a powered, account-randomized retention pilot with a holdout. |

## Four-chapter application narrative

### 01 — The Paradox

The opening now distinguishes the verified commercial customer-churn KPI (**UNKNOWN**) from three date-derived plan-proxy measures and total reconstructed plan-loss events. The 2023 customer denominator is zero, so no rate is reported for that year. The 2024 figures use the ledger opening cohort: 7/374 (1.87%) with any loss; 3/374 (0.80%) inactive at close; and 0/190 (0.00%) full account-coverage loss.

### 02 — Follow the Evidence

The daily-ledger view is the source for daily, monthly, quarterly, semiannual and annual summaries. Period percentages use the period-opening cohort; daily rates are not averaged to construct larger-period rates. The table exposes both any-time opening-cohort loss and closing loss with their denominators. All 60 loss-associated accounts are inspectable; an expandable timeline lists the eight complete-coverage gap-and-return accounts.

The Jan 1 boundary labels are explicit: **Start of Day** is 190 accounts / 374 account-plan relations before that date's transitions; **End of Day** is 191 / 379 after same-day starts. Five account-plan relations begin on that date. The difference is two instants, not annual churn or growth.

The plan-tier summary is proxy-level only. It shows 2024 opening cohort loss counts/denominators as Enterprise 5/120, Basic 2/132 and Pro 0/122. Name-based transition pairs (52 possible upgrades and 51 possible downgrades within 30 days) remain possible pairs, not confirmed migrations. Supplied upgrade/downgrade flags are separately labelled source fields.

### 03 — The Cost of Inaction

The economic point is that plan coverage can contract without complete customer loss. Of the 62 reconstructed plan-loss events over 2023–2024, 54 occurred while another plan proxy remained active. However, this package cannot establish MRR loss, gross revenue churn, net revenue churn, LTV exposure or preventable loss. Repeated MRR/ARR rows and refund values are not treated as recurring-revenue outcomes. The Decision Lab continues to use editable, generic units and hypothetical incremental retention lift; its outputs are scenario arithmetic, not observed impact or ROI.

### 04 — The Decision Room

The opening of the chapter states the three challenge answers directly. The existing editable scenario controls, conditional arithmetic, sensitivity, five-or-fewer prioritized recommendations and 30/60/90-day plan remain. The recommended test randomizes eligible verified accounts, uses account-level assignment, measures 90-day logo retention and verified MRR separately, and tracks satisfaction, discounting, complaints and cost as guardrails. No pilot has been run.

## Priority actions

1. **Lifecycle instrumentation — RevOps / Data Engineering, days 1–30.** Add durable product and contract identifiers, renewal lineage, effective status, cancellation and reactivation timestamps, and a direct event-to-contract foreign key. Success: lifecycle records reconcile to account-period snapshots without ambiguous joins.
2. **Reconcile observed cases — Customer Success Operations / RevOps, days 1–30.** Review all 60 account-plan loss candidates and the eight full-coverage gap-return timelines against operational records. Success: each case receives a documented disposition (confirmed cancellation, renewal, plan change, reactivation or unresolved).
3. **Define revenue movement — Finance / RevOps, days 1–30.** Publish currency, billing-period and effective-date rules; build an account-month MRR bridge with opening value, new, expansion, contraction, lost, reactivated and closing value. Success: bridge residual is zero for eligible months; until then, recurring-revenue exposure stays UNKNOWN.
4. **Measure acquisition and value realization — Product Analytics / Customer Success, days 31–60.** Instrument first-value milestone and account-level adoption with reliable dates; compare equal-age acquisition cohorts and document censoring. Success: a reproducible activation and retention cohort has denominators and complete follow-up.
5. **Test one retention intervention — Customer Success / Analytics, days 61–90 or after adequate follow-up.** Select verified active accounts with a defined renewal window, stratify and randomize at account level, and use intention-to-treat. Success: estimate the treatment-control difference with uncertainty and guardrails before scaling. Do not infer expected lift from the current synthetic dataset.

## Verified data and method

All five CSVs are present under `solution/data/raw/`; current hashes are recorded in `process-log/evidence/final-consolidation-runtime.json`. The source window is 2023-01-01 through 2024-12-31 (731 civil days). The module unions overlapping and contiguous `[start_date, end_date)` intervals at `(account_id, plan_tier)`, right-censors null ends at the observation boundary, retains invalid intervals in diagnostics, and derives daily transitions. `plan_tier` is a **PLAN-LEVEL PROXY**, not product identity.

Current raw-ledger re-execution: 1,476 merged intervals; 1,433 first account-plan relations; 43 plan reactivations; 62 plan-proxy losses affecting 60 accounts; 8 full-coverage loss events; 500 first-observed customers; 8 account reactivations; 949 account-days of portfolio expansion and 53 account-days of contraction. Daily plan and customer bridge checks each have zero failure days. These arithmetic checks do not certify commercial semantics.

The event table has only account-level linkage. In the current daily endpoint, 0/600 event rows match an account-plan loss on the same civil date; 1/600 are within one day, 4/600 within seven days, 26/600 within 30 days and 37/600 within 60 days of a plan-proxy loss. The earlier event-versus-subscription forensic comparison found 443/472 non-reactivation 2024 events on dates with at least one active subscription and 339/472 with no account-level subscription end in ±30 days. Neither join proves event-to-contract identity.

## Financial and causal limits

- Product/service identity is not supplied; only plan-tier proxy analysis is supported.
- `end_date` is interpreted as the first inactive civil date under `[start_date, end_date)`, but the source does not establish whether it is an effective termination or an administrative/contractual date.
- Event records have no subscription key; source event reasons are reported reasons, not verified causes.
- The data do not support commercially validated customer churn, calibrated future-risk ranking, current MRR, lost MRR, GRR/NRR, LTV, causal uplift or intervention ROI.
- The data are synthetic. Usage, support, satisfaction and event outcomes have temporal/entity limitations documented in the analytical reports.

## Engineering and runtime evidence

- API: FastAPI serves the existing analysis and daily-ledger contracts; scenario validation is exercised through REST.
- Frontend: React/TypeScript executive investigation with four chapters, API-backed metrics, period selection, disclosure tables and editable scenario assumptions.
- Docker: separate API and web images, Compose health dependency; both services were built and reached healthy state. The local defaults 8000/5173 were occupied by other existing RavenStack containers. This run preserved them and used ports 18201/15176.
- Runtime evidence: API health, daily-ledger response, frontend root, JavaScript/CSS assets, frontend `/api` proxy, valid hypothetical scenario (200) and invalid effectiveness (422) were verified. Runtime evidence is summarized in `process-log/evidence/final-consolidation-runtime.json`.
- Tests: 57 API/analysis tests passed; frontend Vitest 6/6 passed; Ruff passed on API and daily-ledger sources; TypeScript/Vite build passed.
- Bundle split: before split, one minified JS file was 708.10 kB. After split, app entry 269.63 kB, charts 420.58 kB and icons 16.29 kB (706.50 kB combined; gzip 196.51 kB combined). This improves per-chunk sizing/cache boundaries, not total transfer size.
- Browser visual inspection and viewport screenshots were not performed in this run. The local browser surface had previously denied access; it was not retried or bypassed. Responsive appearance remains UNKNOWN despite static breakpoints and DOM-level component tests.

## G4 challenge answers

1. **What is causing churn?** No causal cause is established. The strongest supported issue is that event, status and subscription-date sources do not describe a single consistent customer lifecycle. Plan-proxy loss counts and reported reasons are descriptive signals for reconciliation and future testing, not causal explanation.
2. **Which segments/accounts are most at risk?** There are no validated future-risk estimates. Sixty named account IDs are listed in the live Evidence chapter as historical plan-loss reconciliation candidates; eight accounts show full coverage gaps followed by later date-derived returns. Enterprise's opening 2024 proxy cohort has 5/120 losses (4.17%), Basic 2/132 (1.52%), and Pro 0/122 (0.00%), conditional on dates and plan-tier proxy. These rates are exploratory, not calibrated risk.
3. **What should the company do?** Reconcile product/contract identity and lifecycle first; review the 60 cases, establish an account-month recurring-revenue bridge, instrument activation/adoption and equal-age cohorts, then run a randomized account-level retention pilot with guardrails.

## Reproduction

From `submissions/thomasleick/solution/`:

```bash
docker compose up --build
```

If the default ports are already occupied, use:

```bash
API_PORT=18201 WEB_PORT=15176 docker compose --env-file .env.example up --build
```

For a direct daily-ledger reproduction with Python:

```bash
PYTHONPATH=analysis python -m daily_portfolio_churn \
  --data-dir data/raw \
  --output-dir analysis/daily_portfolio_churn/outputs
```

The command writes only analytical outputs; it does not modify source CSVs.

## Submission status

The package is locally consolidated and ready for human review. It has not been committed, pushed or submitted as a Pull Request. The official workflow requires a fork, a `submission/<name>` branch and a Pull Request; those Git effects remain outside this execution's authorization. Browser visuals remain unverified, and the official business KPI remains UNKNOWN, so this is not a PASS on all challenge criteria.


## Addendum — monthly rate versus exposure analysis (2026-10-22)

The 24-month ledger comparison is now primary for executive interpretation. Recorded event rows increased 73→527 while reconstructed opening account-month exposure increased 845→3,909; event rows per 100 account-months increased 8.64→13.48. Conditional plan-proxy loss events increased 6→56 and 0.427→0.595 per 100 relation-months. Complete account-coverage loss episodes rose 2→6, while their exposure-normalized rate fell 0.237→0.153 per 100 account-months. Usage count changed +1.13% and per observed account-month +1.17%; 19,142/25,000 usage rows predate linked subscription starts. These mixed, conditional indicators do not establish verified churn deterioration. Monthly movements are also cross-tabulated by industry, country and referral source with separate customer and plan-proxy denominators; segment-months with fewer than 30 opening customers are visibly flagged. The monthly account-segment CSV is `solution/analysis/daily_portfolio_churn/outputs/g4-alignment/monthly-account-segment-summary.csv`. See `G4-MONTHLY-CHURN-ANALYSIS.md` and `G4-CHALLENGE-FINAL-ANSWERS.md`; original report text and prior checkpoints remain unchanged.
