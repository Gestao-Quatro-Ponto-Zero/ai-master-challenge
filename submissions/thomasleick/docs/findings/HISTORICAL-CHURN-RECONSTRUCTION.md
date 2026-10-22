# Historical Churn Reconstruction

**Project:** RavenStack — The Churn Paradox  
**Challenge:** G4 AI Master Challenge 001 — Diagnóstico de Churn  
**Analysis date:** 2026-10-21  
**Status:** Conditional date-based reconstruction; the dataset does not reconcile to a validated historical churn KPI.

## Executive answer

Applying the classic customer churn formula to the subscription dates produces:

| Metric | 2023 | 2024 | Interpretation |
|---|---:|---:|---|
| Distinct accounts active at period start | 0 | 191 | Any linked subscription active under `[start_date, end_date)` |
| Opening accounts with a full-relationship gap during the year | 0 | 0 | Date-derived gross logo-loss numerator |
| Classic logo churn | **Not calculable (0/0)** | **0.0% (0/191)** | 2023 has no denominator; 2024 result is conditional and contradicted by other status fields |
| Opening active subscriptions | 0 | 655 | Unique subscription IDs active at the start boundary |
| Opening subscriptions no longer active at next-year boundary | 0 | 66 | 2024 date-based subscription exit count |
| Opening subscription rows with `churn_flag=True` | 0 | 66 | The 2024 opening flags align with the 66 date-ended opening rows |
| Opening-cohort subscription churn | **Not calculable (0/0)** | **10.08% (66/655)** | Conditional subscription-level metric, not logo churn |
| Active accounts at next-year boundary | 191 | 500 | 2025-01-01 is a date-rule boundary, not an independently observed 2025 snapshot |

**Direct answer:** a strict date-only reconstruction is unable to calculate 2023 classic churn because there were no eligible opening accounts. It gives **0% in 2024**, with **0 of 191** opening accounts losing all linked subscription coverage during the year. That 2024 value is not suitable as a validated company KPI: 103 of those 191 accounts have at least one non-reactivation churn event dated in 2024, and 443 of the 472 non-reactivation event rows occur while at least one linked subscription is still active under the same date rule. The most accurate executive statement is therefore: **2023 is undefined; 2024 is 0% under the literal subscription-date interpretation, but true historical logo churn remains unreconciled.**

## 1. Formula and G4 cohort approach

The classic formula used is:

`Customer churn rate = distinct customers lost during period / distinct eligible customers active at period start × 100`.

The published [G4 article on cohort analysis](https://g4educacao.com/blog/analise-de-coorte) describes cohorts as groups sharing a time-linked acquisition or purchase event, then compares behavior at equal elapsed periods to understand retention and customer lifecycle. It distinguishes a cohort from a non-temporal segment and explains reading retention across cohort age. This implementation uses the earliest valid subscription start month as a candidate relationship-start cohort and checks activity at monthly boundaries. It does not treat segment composition as retention.

The source is G4 public educational material, accessed 2026-10-21. The interpretation of its approach for this dataset is our analytical translation, not a claim about proprietary G4 methods. Since the dataset’s lifecycle records conflict, a date-based cohort series is labeled conditional rather than validated retention.

## 2. Data and source audit

The computation uses `solution/data/raw/ravenstack_accounts.csv`, `ravenstack_subscriptions.csv`, and `ravenstack_churn_events.csv`; the other two source tables remain unchanged and are not needed to determine subscription interval coverage.

| Source | Rows | Relevant fields | SHA-256 |
|---|---:|---|---|
| Accounts | 500 | `account_id`, `signup_date`, `churn_flag` | `348d8ba906b7776894b5236b2e7aa91a503d41670dbc9aad30c37b503c9abef5` |
| Subscriptions | 5,000 | `subscription_id`, `account_id`, `start_date`, `end_date`, `churn_flag` | `dcf1d93ca9a35e0dcba0ab686d255f0e9ec26512970bbf0944cf19cbef2d751a` |
| Churn events | 600 | `account_id`, `churn_date`, `is_reactivation` | `6391c41d8291b7b4845ec9a84d3837c2ed230a33a32a854ec33d4e66dc150940` |

All 5,000 subscription IDs are unique. Every account has multiple subscription rows. The provided schema notes that a blank end date denotes an active subscription; therefore all date calculations treat a null end as open-ended. This assumption is not a substitute for a source-system extraction timestamp or verified contractual status. The latest non-null subscription end, latest start and latest event date are all 2024-12-31. Thus 2025-01-01 is a computational boundary; it is not evidence that a new 2025 snapshot was collected.

Thirteen subscription rows have `end_date <= start_date`. They cannot form a positive-length active interval and are excluded from interval continuity; they remain present in the source and are counted as data-quality exceptions. Subscription `churn_flag=True` agrees with presence of an end date in the source schema, but that agreement does not establish whether the date means effective cancellation or planned/administrative end.

## 3. Reconstructed populations and annual calculations

The required date rule is applied literally:

`start_date <= snapshot_date AND (end_date is absent OR end_date > snapshot_date)`.

| Snapshot | Active account logos | Active subscription rows | Accounts with >1 active row |
|---|---:|---:|---:|
| 2023-01-01 | 0 | 0 | 0 |
| 2024-01-01 | 191 | 655 | 164 |
| 2025-01-01 | 500 | 4,514 | 500 |

Multiple simultaneous rows are collapsed to one account for logo churn. At 2024 opening, 164/191 accounts have multiple active subscription rows. At 2025 boundary all 500 accounts have multiple active rows. This strongly cautions against treating subscription rows as independent customers or summing their recurring revenue.

### 2023

- Opening account base: **0**. There is no denominator, so the classic rate is **undefined**, not zero.
- First subscription starts dated during 2023: **191 accounts**. Of these, **190** are active at the 2024-01-01 date boundary; **one** is not.
- The 2024-01-01 boundary includes **one account whose first subscription starts exactly on that boundary**. It is correctly included in the 2024 opening snapshot and is not an acquisition inside the 2023 interval.
- Subscription end-date rows in calendar 2023: **18**. These include subscriptions created and ended within 2023 and cannot supply an opening-cohort subscription churn denominator.
- Churn events: **73 rows**, including **67 non-reactivation rows**; 59 accounts have a non-reactivation event in the year. These are event records, not eligible-base customer churn.

### 2024

- Opening account base: **191**; closing boundary account set: **500**.
- Opening accounts with an all-subscription date-interval gap in the year: **0**; account-date gross logo churn is `0 / 191 = 0.0%`.
- Opening accounts inactive at the 2025-01-01 date boundary: **0**; end-state loss is also `0 / 191`.
- **308** accounts with first observed subscription after the opening boundary are active at close. One previously recorded account not in the opening base starts a new subscription and is active at close. The count bridge is `191 + 308 + 1 − 0 = 500`, with residual **0**. This is a set-count bridge at boundaries, not a complete transaction ledger.
- Of 655 subscription IDs active at opening, **66** are not active at the next-year boundary: `66 / 655 = 10.0763%`, displayed as **10.08%**. There are **468** end-dated subscription rows across all accounts in 2024, including those that did not belong to the opening snapshot.
- Those same **66 of 655** opening subscription rows have `subscription.churn_flag=True`; this aligns with the source’s “flag means ended” definition but does not establish account-level loss.
- **103/191** opening accounts have a non-reactivation event in 2024 (53.9% event-label incidence). **49/191** have `account.churn_flag=True` (25.7%). The event feed also contains **55 rows marked reactivation** across 49 accounts; 14 of those marked-reactivation accounts are in the 2024 opening set. These are labels/records, not proven reactivation flows.
- The date reconstruction identifies one previously seen account outside the opening base that returns to active subscription coverage in 2024. There are **zero** date-derived exits followed by reactivation among the 191 opening logos.

### Metric classification

| Definition | 2023 | 2024 | Classification and limitation |
|---|---:|---:|---|
| Account date-interval logo loss / opening active accounts | 0/0 | 0/191 = 0.0% | 2023 undefined; 2024 conditional on all linked subscription dates being effective lifecycle states |
| Opening subscription IDs no longer active at year-end / opening active subscription IDs | 0/0 | 66/655 = 10.08% | 2024 conditional subscription churn; a row-level unit and not a customer-loss rate |
| Accounts with non-reactivation event / opening accounts | 0/0 | 103/191 = 53.9% | Event-label incidence, not validated churn rate |
| Accounts with account-level churn flag / opening accounts | 0/0 | 49/191 = 25.7% | Persistent “churned at any point” flag in opening population; not necessarily year-specific |
| Event row count | 73 | 527 | Counts records, including repeats and reactivation-marked records; no denominator |

## 4. Event and status reconciliation

The event table says `churn_date` is when the account left. Under the subscription date rule, **47 of 67** non-reactivation event rows in 2023 and **443 of 472** in 2024 occur while at least one subscription on that account is active. This can reflect parallel products, lifecycle mismatch, or event semantics that do not mean full account loss; the available keys cannot distinguish these explanations. It is not valid to count each such row as a lost logo.

The 2024 opening population comparison is particularly material:

- Date-interval account losses: **0 / 191**.
- Accounts with a non-reactivation churn event: **103 / 191**.
- Accounts with a persistent account churn flag: **49 / 191**.
- Opening subscription records not active at year-end: **66 / 655**.

Monthly snapshots do expose several short-interval, date-derived account gaps among each month’s opening base:

| Month | Opening accounts | Full-account interval gaps | Conditional monthly logo churn | Reactivated by next boundary |
|---|---:|---:|---:|---:|
| 2023-11 | 149 | 1 | 0.671% | 0 |
| 2024-03 | 235 | 1 | 0.426% | 1 |
| 2024-04 | 264 | 1 | 0.379% | 1 |
| 2024-09 | 385 | 2 | 0.519% | 1 |

The remaining 20 of 24 monthly periods have no date-derived account gap (2023-01 has a zero opening denominator and is undefined). One of two September 2024 accounts is active again by the next boundary. These monthly calculations use distinct accounts active at each monthly opening and include within-year acquisitions, so they do not contradict the 0/191 annual opening-cohort result: the denominator populations differ. Every monthly number is still conditional on date fields accurately representing effective account lifecycle.

These measures answer different questions and do not reconcile. The 66 ended opening subscriptions do not imply 66 lost accounts because 164 opening accounts have multiple active subscription rows and other rows can remain open. Conversely, an open-ended row does not prove that the customer relationship was commercially active at extraction time.

### Movement identity

For 2024, boundary counts satisfy `ending base = beginning base + first-observed additions active at close + previously seen return active at close − opening accounts inactive at close`: `500 = 191 + 308 + 1 − 0`, residual **0**. This identity is possible because counts are distinct account sets and the one prior-history return is separated. It does not validate event dates or establish an acquisition source.

For 2023, 191 first-subscription accounts start during the calendar year, 190 are active at the next boundary, and one account starts exactly at 2024-01-01. The closing snapshot is 191. This boundary result is consistent as a set count after accounting for the next-period start, but no opening base exists from which to calculate classical churn.

## 5. Cohort retention diagnostic

The module groups accounts by earliest positive-length subscription start month. At each equal elapsed-month boundary, an account is active if any subscription spans that boundary. It produces **24 monthly cohorts and 300 cohort-month points**. Four points are below 100% under the date rule:

| Cohort | Elapsed month | Boundary | Active / initial | Conditional date-rule activity |
|---|---:|---|---:|---:|
| 2023-09 | 2 | 2023-12-01 | 14 / 15 | 93.33% |
| 2023-09 | 3 | 2024-01-01 | 14 / 15 | 93.33% |
| 2024-01 | 0 | 2024-02-01 | 25 / 26 | 96.15% |
| 2024-06 | 3 | 2024-10-01 | 26 / 27 | 96.30% |

Every cohort is back to 100% at its latest available boundary (2025-01-01). This may reflect real reactivation, but every account also has open-ended subscription rows, and the event and account flags materially disagree with date-derived activity. Consequently, the output is a **conditional lifecycle diagnostic**, not a defensible retention curve or executive cohort heatmap. Cohort analysis cannot settle the true churn rate until lifecycle fields are reconciled.

## 6. Business conclusions

1. **There is no classical 2023 rate:** the observed opening base is empty. Any 2023 rate derived from the 73 events, 18 ended subscription rows, or account flags would use a mismatched population or denominator.
2. **A literal 2024 date reconstruction is 0% logo churn:** 0 of 191 opening accounts loses all subscription coverage. The same rule yields 10.08% opening subscription churn. These are different units.
3. **Neither date-based result is validated as company churn:** 103 opening accounts have non-reactivation events, 49 are marked churned on account records, and most non-reactivation event rows coincide with at least one date-active subscription.
4. **The dates are useful enough to quantify the competing interpretations.** The proper response is not to discard them; it is to publish the 0/191 conditional estimate next to the conflicting 103/191 event incidence and 49/191 flag incidence.
5. **No 2025 snapshot is verified.** 500 active accounts at 2025-01-01 follows directly from open-ended records and should not be described as observed 2025 retention.

## 7. Required data to establish an official rate

RavenStack should provide an immutable account-subscription lifecycle ledger with subscription/account IDs, product or workspace ID, effective start/end timestamps, status-change reason, cancellation-request date, service-access termination date, billing termination date, and reactivation date. Each extract needs an explicit `as_of_timestamp`, currency and recurring-revenue grain. The event stream must link to a subscription or explicitly state whether a churn event means product cancellation or complete customer loss. Define the eligible denominator (paid accounts vs. trials) and the reactivation convention before publication.

## 8. Implementation and reproducibility

Added `solution/analysis/historical_churn/reconstruct.py`, standard-library tests, and JSON/CSV outputs. Added `GET /api/historical-churn`, served from the original source CSVs at API startup, and a historical reconstruction panel to Chapter 02. Existing analysis outputs and four-chapter navigation are preserved. No source CSV was changed.

From `submissions/thomasleick/solution/`:

```bash
python analysis/historical_churn/reconstruct.py
python -m unittest discover -s analysis/historical_churn/tests -v
docker compose config --quiet
docker compose up --build
```

The module writes `historical-churn.json`, `annual-reconciliation.csv`, and `cohort-retention-conditional.csv` under `analysis/historical_churn/outputs/`. API, frontend and Docker verification results are recorded in the corresponding new process-log checkpoint; they must be interpreted only after the current run executes them.

## 9. Known limitations

- `end_date` semantics are taken from the dataset README, but cannot be independently verified as an effective termination timestamp.
- Null end dates can mean active or unobserved; no extraction timestamp settles this.
- The 2025-01-01 boundary is one day after the latest source event/start/end date and is not an observed snapshot.
- The source has 13 non-positive subscription intervals and multiple simultaneous rows per account.
- Event dates, account flags, subscription flags and interval state do not identify one consistent outcome label.
- No event-to-subscription foreign key exists, so subscription endings cannot be attributed to a particular churn event.
- There is no defensible account-month at-risk panel, exact retention curve, revenue churn, GRR, NRR or causal effect from these data.
- The cohort calculations are exploratory/conditional and do not establish a valid G4-style business retention finding.
