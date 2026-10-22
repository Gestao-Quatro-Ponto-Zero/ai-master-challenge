# RavenStack Contract Churn Forensics

**Investigation date:** 2026-10-21  
**Evidence:** original synthetic Rivalytics source CSVs; reproduced by `solution/analysis/contract_churn/investigate.py`  
**Status:** strong reconciliation of recorded rows; true commercial lifecycle remains unknown.

## 1. Executive summary

The 66 figure is **subscription-row attrition under the recorded end dates**, not 66 lost customers. The 66 opening subscription IDs belong to 57 distinct accounts. For every one of those 66 rows, another subscription belonging to the same account was date-active on the ended row's `end_date`. The union of subscription intervals covers the full 2024 calendar year for all 57 accounts, and all 57 have at least one subscription active at the 2025-01-01 boundary under the source's date rule. This is strong evidence of account-level continuity in these records, although it cannot prove paid commercial continuity because row semantics are not independently documented.

The 443/472 event discrepancy is also reproducible. It means 443 of the 472 2024 non-reactivation event rows occurred on dates when the same `account_id` had at least one subscription interval active. The event table has **no subscription ID**, so these are account-date conflicts, not proof the event is false or which contract it refers to. Those 443 rows represent 302 accounts; 395 rows had more than one subscription active on the event date.

Only 104/443 conflicting rows were within ±30 days of any 2024 subscription end on that account; 160/443 were within ±60 days. Thus 339/443 had no such end within 30 days. The proximity definition is account-level, symmetric and not a foreign-key match. It does not explain the events.

**Business conclusion:** separate subscription churn from logo churn, and stop interpreting the event table's “account left” wording as verified account loss until the data owner reconciles the model. No causal churn driver, lost recurring revenue, or validated future-risk score is established.

## 2. Question investigated

Does RavenStack lose customers, end individual subscriptions, replace contracts, or record events that do not mean the commercial relationship ended? The analysis tests what the three source tables can establish without assuming which system is authoritative.

## 3. Definitions and evidence rules

| Term | Operational rule used here | Evidence classification |
|---|---|---|
| Opening account | Distinct `account_id` with any subscription satisfying `start_date <= 2024-01-01` and (`end_date` blank or `end_date > 2024-01-01`) | Conditional on documented source dates |
| Opening subscription | Distinct `subscription_id` satisfying the same opening-boundary rule | Conditional on documented source dates |
| Ended opening subscription | Opening ID with a valid `end_date < 2025-01-01` | Observed row status / date |
| Active subscription at date | `[start_date, end_date)`; blank end treated as open-ended, per source README | Conditional; not commercially certified |
| Account continuity | At least one same-account subscription covers every day from 2024-01-01 to 2025-01-01 after unioning intervals | Inferred from dates; not verified paid status |
| Conflicting event | 2024 non-reactivation event for which at least one linked-by-account subscription is date-active on `churn_date` | Observed account-date coincidence; no contract link |
| Near an end | Absolute date distance to the nearest same-account subscription end in 2024 is ≤ 0, 7, 30 or 60 days | Sensitivity diagnostic, not an event-contract match |

Duplicate event rows are preserved as events; distinct account counts are reported separately. Concurrent subscriptions are unioned for account continuity and never multiplied into logo counts. Invalid/non-positive intervals are excluded from interval coverage by the existing reconstruction logic and remain in source-quality counts.

## 4. Source and reproducibility

The investigation uses `ravenstack_accounts.csv`, `ravenstack_subscriptions.csv` and `ravenstack_churn_events.csv`. Account ↔ subscription and account ↔ event relationships use `account_id`. `subscription_id` is unique in the analyzed source; `churn_event_id` is unique. There is no `subscription_id` in the event table.

Source file hashes are embedded in `solution/analysis/contract_churn/outputs/contract-churn-forensics.json`. Reproduce from the standalone `solution/` directory:

```bash
python analysis/contract_churn/investigate.py
python -m unittest discover -s analysis/contract_churn/tests -v
```

Outputs: JSON summary plus a 66-row ended-subscription audit, a 443-row conflicting-event audit, a 55-row reactivation-marker audit, and a 191-row opening-account indicator reconciliation. The full event inventory records active subscription IDs only as same-account/date context and explicitly marks the event-to-contract relationship UNKNOWN.

## 5. Revalidation of historical counts

| Measure | Numerator / denominator | Result | Origin and interpretation |
|---|---:|---:|---|
| Opening accounts | 191 / distinct accounts | 191 | 2024-01-01 boundary, date rule above |
| Opening subscriptions | 655 / distinct IDs | 655 | Same boundary; one account can contribute multiple IDs |
| Ended opening subscriptions | 66 / 655 | 10.08% | Opening IDs not active at 2025-01-01; subscription-level conditional exit share |
| Accounts represented in 66 | 57 / distinct accounts | 57 | Deduplicated `account_id` across ended IDs |
| 2024 non-reactivation events | 472 / event rows | 472 | `churn_date` in `[2024-01-01, 2025-01-01)` and `is_reactivation=False` |
| Events with active subscription | 443 / 472 | 93.86% | Same-account interval active on event date; conflict, not account truth |
| Conflict accounts | 302 / distinct account IDs | 302 | Deduplicated among 443 rows |

`account.churn_flag`, subscription `churn_flag`, event rows and date coverage are different measurements. These numbers are not interchangeable churn rates.

## 6. Inventory of 66 ended subscriptions

The row-level evidence is in `outputs/ended-opening-subscriptions-2024.csv`; the API exposes all 66 rows.

| Exclusive primary observed pattern | Subscription rows | Rule |
|---|---:|---|
| Other subscription active at termination | 66 | At least one different same-account interval spans the ended row's `end_date`; takes precedence in exclusive case taxonomy |
| Later subscription after gap | 0 | No other active-at-end contract and a subsequent start |
| No successor and account inactive at close | 0 | No active peer and inactive on 2025-01-01 |
| Account active at close, successor timing ambiguous | 0 | Fallback for rows not covered above |

Additional non-exclusive attributes:

- The 66 rows belong to 57 accounts; every row has `subscription.churn_flag=True` in the source.
- All 66 rows have another subscription active on the exact termination date; all 57 accounts maintain merged interval coverage throughout 2024 and are active at the 2025-01-01 boundary.
- 55 ended rows have another subscription start on or after the end date. These are **unconfirmed successor candidates**; no migration/replacement foreign key exists.
- The ended row's plan differs from the account-level `plan_tier` in 48/66 rows. The account field is described as an initial plan, so this is a possible plan-change signal, not a migration record.
- 8 ended rows have `upgrade_flag=True`; 1 has `downgrade_flag=True`. These flags describe a plan event, not which row replaced which.
- 0/57 accounts have a full-coverage gap under the interval-union rule. Therefore complete account loss is not observed for the 57 during this period under this model.

The exclusive taxonomy does not imply categories are inherently mutually exclusive: successor starts and plan flags are retained as separate attributes. It simply chooses the strongest visible same-day continuity pattern as the primary description.

## 7. Investigation of the 443 conflicting events

The machine-readable row-level inventory is `outputs/conflicting-nonreactivation-events-2024.csv`. It includes event ID, account, date, reason, feedback, active subscription IDs and count on that date, all 2024 end dates for the account, nearest end/date delta, account attributes, and an explicit no-FK warning.

### 7.1 Multiplicity and proximity sensitivity

| Window to any same-account 2024 end | Among all 472 non-reactivation rows | Among 443 rows with an active subscription |
|---|---:|---:|
| Same day (0 days) | 5 | 5 |
| Within ±7 days | 39 | 39 |
| Within ±30 days | 107 | 104 |
| Within ±60 days | 164 | 160 |
| No end within ±30 days (conflict rows) | — | 339 (76.5%) |
| No end within ±60 days (conflict rows) | — | 283 (63.9%) |

395/443 conflict rows had more than one active subscription on the event date. This is 89.2% of event rows; 278/302 conflict accounts had at least one event date with multiple active subscriptions. The event counts therefore include repeated observations and cannot be treated as independent customer-level churn outcomes.

### 7.2 Recorded reason patterns

| Reason code | All 472 event rows | With an active subscription | Same-account end within ±30 days (all rows in reason group) |
|---|---:|---:|---:|
| features | 91 | 85 | 16 |
| budget | 82 | 73 | 22 |
| support | 81 | 79 | 26 |
| unknown | 77 | 73 | 16 |
| pricing | 72 | 67 | 13 |
| competitor | 69 | 66 | 14 |

These are reason-code counts, not established root causes. “Support,” “pricing,” “budget,” “features,” and “competitor” are plausible customer-reported mechanisms, but there is no validated event-to-contract link, no adjudicated reason taxonomy, and no comparison group showing causal effect. 104 of the 443 conflict events lie within ±30 days of some same-account end; the other 339 do not under this window. Even the 104 are only date proximity.

The 55 rows explicitly marked `is_reactivation=True` (49 accounts) are retained separately in `outputs/reactivation-marked-events-2024.csv`. Of these, 51 rows occur while at least one same-account subscription is date-active; 20 follow some same-account subscription end, 45 precede a later same-account subscription start, and 33 follow an earlier non-reactivation event row. Fourteen of the 49 accounts are present in the 2024 opening base. These overlaps show that the marker alone is not a reliable transition label: the account may already have an active contract or multiple event rows. They do not establish false marking, reversal, or the exact reactivated contract.

### 7.3 Segment concentration

The diagnostic below counts **unique accounts with at least one conflicting event** divided by all source accounts in that account-level segment. It is event-record incidence, not churn/risk. Accounts may have repeated events; segment fields are account-level labels.

| Dimension | Segment | Accounts with conflict / segment accounts | Share |
|---|---|---:|---:|
| Industry | EdTech | 53 / 79 | 67.1% |
| Industry | DevTools | 71 / 113 | 62.8% |
| Plan (account initial plan) | Pro | 111 / 178 | 62.4% |
| Plan (account initial plan) | Enterprise | 95 / 154 | 61.7% |
| Acquisition | organic | 74 / 114 | 64.9% |
| Acquisition | ads | 53 / 98 | 54.1% |
| Country | UK | 40 / 58 | 69.0% |
| Country | France | 16 / 22 | 72.7% |

Small segments such as France (n=22) require caution. The range is relatively narrow in large groups, and the event model itself is unresolved; no ICP mismatch or segment churn conclusion follows. Full tables for plan, industry, country and referral source are in the JSON output and exposed through the API.

## 8. Account-level examples

These are **record-reconciliation cases**, not risk-ranked customers or forecasts.

- `A-0a62f5`: 5 non-reactivation events, all 5 on dates with active subscription coverage; account flag is false and no subscription end date was recorded for the account in 2024. Event reasons span pricing, features, budget and support. This is a direct event/state conflict, not evidence the account actually departed.
- `A-180abf`: account flag true, 4 non-reactivation events and all 4 have active subscription context. It has a subscription end date on 2024-04-19; event dates include 2024-03-09 (41 days before), 2024-05-04 (15 days after), 2024-05-08 (19 days after), and 2024-09-12 (146 days after). A later plan row may coexist, but the source has no event-contract mapping.
- `A-029f69`: 3 conflicting events; account-level 2024 end dates include 2024-08-23, 2024-09-19 and 2024-11-16. One event is 16 days from the nearest end and another 28 days. This density is useful for lifecycle audit only; it does not validate causal linkage.

## 9. Account/subscription indicator reconciliation

One row per 2024 opening account is written to `outputs/opening-account-reconciliation-2024.csv`. The matrix compares account lifetime `churn_flag`, any subscription flag across its observed rows, 2024 non-reactivation event presence, 2024 subscription end presence, continuous interval coverage, and activity at the next-year boundary. The API returns pairwise cross-tabs and the underlying 191 account rows.

The salient reconciliation result is that a subscription can end while the account remains covered by another subscription. For the 66 ending rows, this occurs on every row. Event occurrence and account flags are not used to override that date-derived fact, nor are dates used to erase the reported event. Truth about commercial logo status remains UNKNOWN until the source-of-truth contract is clarified.

## 10. Economic impact

The 66 ended rows have recorded per-row MRR values from 0 to 7,960 (median 655.50) and ARR from 0 to 95,520 (median 7,866). The unweighted row sums are 93,159 MRR units and 1,117,908 ARR units; **they are not current revenue, lost MRR, ARR churn or exposure** because row uniqueness/version semantics and concurrent contract economics are unverified. 48/66 recorded subscription plans differ from account initial plan, further weakening the interpretation of row sums as a set of distinct current contracts.

The 443 conflicting event rows include 110 nonzero event refund values totaling $7,044.82 (the source field is labeled USD). Across all 527 2024 events, 131 nonzero refunds sum to $7,884.72. These amounts are event-level values and cannot be assigned to an ended subscription or customer loss. There is no defensible estimate of recurring revenue lost or recoverable from this evidence.

## 11. Candidate business mechanisms

| Candidate | Supporting observation | Counterevidence / status | Decision use |
|---|---|---|---|
| Individual contract cancellation while account continues | All 66 opening subscription ends have another active same-account subscription at end | Row semantics may mean version/snapshot; paid continuity unverified | Audit contract granularity and split subscription/logo KPIs |
| Contract replacement / plan change | 55 later starts on/after an end; 48 plan-vs-initial-plan differences; 9 upgrade/downgrade flags | No replacement ID or signed amendment link; flags do not map old to new | Reconcile amendment and renewal records before calling migration |
| Account loss reflected in event rows | Events labeled “account left”; reason codes present | 443 of 472 rows have active subscription context; 339 lack an end within ±30 days; no subscription FK | Treat as unresolved lifecycle events; do not trigger broad save campaign from rows alone |
| Price/budget/product/support issue | 326/472 reason rows are features, budget, support or pricing | Generated/self-reported reason codes, repetitions by account, no counterfactual or validated churn outcome | Use as discovery interview / instrumentation categories, not cause attribution |
| Data model / instrumentation mismatch | Grain mismatch, event/subscription conflict, multiple active rows common | Synthetic source may intentionally include edge cases; generator rules not verified for every row | Highest-priority measurement remediation |

No hypothesis is established as a causal root cause.

## 12. Direct answers to the G4 challenge

### Question 1 — What causes churn?

**Not identifiable from these records.** The strongest demonstrated explanation for the apparent discrepancy is a metric/lifecycle reconciliation problem: 66 subscription IDs end across 57 accounts while all 57 remain covered; event rows are account-grain and collide with subscription activity. Reasons suggest product, budget, support and pricing topics but are unvalidated reports, not causal effects.

### Question 2 — Which segments and accounts merit attention?

For **data-quality investigation**, inspect accounts with repeated event rows and conflicting status. Examples include `A-0a62f5`, `A-180abf` and `A-029f69`; their supplied flags, event histories and contract dates are shown above and in the downloadable analysis artifacts. Segment-level conflicting-event incidence ranges from 54.1% to 72.7% in the examples shown, with France n=22. These are not calibrated risk scores or verified churn rates. There are no validated future-risk estimates.

### Question 3 — What should RavenStack do?

1. **Immediately:** publish separate definitions for account/logo churn and subscription churn; make `churn_event_id` reference an explicit `subscription_id` where applicable and add lifecycle event type/status.
2. **Within 30 days:** reconcile the 66 ended IDs and 55 successor candidates to billing amendments, renewals, product entitlements and invoice status. Establish whether overlapping rows are products, versions, snapshots or simultaneous contracts.
3. **Within 60 days:** backfill event outcomes (effective cancellation, subscription cancellation, downgrade, migration, reversal, administrative correction) and exact effective timestamps. Require accountable review for reason codes.
4. **Within 90 days:** rebuild an eligible account-month/renewal cohort from verified paid status; only then test a retention treatment with account-level randomization, holdout, 90-day logo retention as primary outcome, and verified MRR/discount/support guardrails.

Owners are recommended functions (Data/RevOps, Billing/Finance, Product/Data Engineering, Customer Success), not assigned employees. No monetary intervention impact is estimated because true lost revenue and causal effectiveness are unknown.

## 13. Product changes

Added the independent `solution/analysis/contract_churn/` module and JSON/CSV audit outputs. Added `GET /api/contract-churn`, a typed response contract, and Chapter 02's **Account vs. Subscription Churn** experience. The UI shows the 66/655 and 443/472 counts, account coverage, event/end-date windows, reason counts, per-subscription details and a reason-filtered event inspection. It explicitly warns that event IDs have no subscription foreign key and that successor starts are not confirmed migration. Prior history views and the four-chapter navigation remain intact.

## 14. Validation

Validation performed in this execution:

- `python analysis/contract_churn/investigate.py`: completed from original CSVs and wrote JSON/CSV inventories.
- `python -m unittest discover -s analysis/contract_churn/tests -v`: 5/5 passed (real-source counts, boundary behavior, interval union/gaps, synthetic overlap/successor/reactivation/event-link behavior, and revenue-sum safeguards).
- `npm test -- --run`: 6/6 passed after adding contract forensics UI fixtures/assertions.
- `npm run build`: TypeScript and Vite build passed. Bundle warning remains: 681.34 kB minified JS (190.91 kB gzip).
- `docker build --target test -t ravenstack-contract-api-test -f apps/api/Dockerfile .` and `docker run --rm --name ravenstack-contract-api-test-final ravenstack-contract-api-test`: 16/16 API tests passed (one Starlette/AnyIO deprecation warning).
- Ruff 0.11.8 in the API test image passed for the new module, API route/schema and tests.
- `docker compose config --quiet` passed. `API_PORT=18100 WEB_PORT=15174 docker compose -p ravenstack-contract up --build -d` built both images and started both services healthy.
- HTTP smoke: API health, OpenAPI (route present), contract endpoint, frontend root, and frontend `/api/contract-churn` proxy returned HTTP 200. API and proxy returned the same 629,567-byte response with 66 ended subscriptions, 443 conflicts and 55 reactivation rows.
- Browser inspection was attempted against `http://127.0.0.1:15174/` but the browser surface denied permission. No alternate browser or workaround was used. Rendered visual/interactivity verification is UNKNOWN; UI behavior is covered by Vitest rendering tests, and HTTP proxy is verified separately.

## 15. Limitations and next evidence needed

- Account-level event rows lack subscription foreign keys and event types.
- `end_date` is described as ended in the supplied README but could still represent an administrative/version boundary rather than loss of paid entitlement.
- Blank end dates are treated as active by source documentation; source extraction timestamp and inactive-but-unclosed contracts are unavailable.
- Successor starts, changed plans, and upgrade/downgrade flags do not identify contract replacement.
- The dataset is synthetic. CRM, billing, invoice, entitlement and account-status sources are unavailable.
- No validated account churn KPI, actual lost MRR, cohort retention curve, causal driver or future-risk probability is produced.

The decisive follow-up is a source-system contract defining account status, subscription identity/versioning, effective cancellation, product entitlement and event-to-subscription linkage. Until that is available, report the 66/655 result as conditional subscription-row exits, not logo churn.
