# RavenStack — Beyond the Churn Headline

## A monthly, evidence-driven diagnosis of growth, retention and commercial movement

**Prepared by Thomas Leick**  
G4 AI Master Challenge 001 — Diagnóstico de Churn  
Independent submission · 22 October 2026

> **Executive conclusion.** RavenStack recorded more churn events and more plan-coverage losses in 2024, while its reconstructed complete-account-loss intensity fell. The data therefore show a mixed retention picture, not proof that customer churn worsened. Growth explains most of the increase in event volume as an arithmetic exposure effect; product-tier losses also rose relative to plan-month exposure. No causal root cause is established. Leadership should reconcile lifecycle records, investigate Enterprise and the eight loss-and-return histories, then test a targeted intervention only on a verified eligible population.

## Page 2 — Executive answer

### Q1 — What is causing churn?

**Diagnosis:** The date reconstruction records 62 account–plan-tier coverage losses across 2023–2024. In 54 cases (87.1%), another plan-tier relation remained active, so most reconstructed plan losses were not complete losses of account coverage. **Priority hypotheses:** feature/value fit (114/600 event rows; 19.0%), support (104/600; 17.3%), and budget/affordability (104/600; 17.3%). **Causal conclusion:** these are reasons declared in event records; they do not prove why customers actually ended a commercial relationship. The event, account-flag and subscription histories also disagree: 312/500 accounts differ between the account churn flag and the “any event” indicator. Usage and support evidence do not establish a pre-loss mechanism.

**Decision:** First repair account/subscription/event linkage and validate the reason codes with customers. Then test feature adoption, support friction and price/value separately. **Confidence:** high for recorded counts and reconstructed movements; low for causal interpretation.

### Q2 — Which segments and accounts need attention?

**Answer:** In the conditional 2024 opening cohort, Enterprise had 5/120 plan-tier relationships lose coverage at least once (4.17%), Basic 2/132 (1.52%), and Pro 0/122 (0%). The 95% Wilson intervals are wide and overlap: Enterprise 1.79–9.38%, Basic 0.42–5.36%, Pro 0–3.05%. This is a reason to review Enterprise renewal/value evidence, not proof that Enterprise customers are predictively riskier. Eight accounts experienced reconstructed complete coverage loss followed by return; their dates and plans appear on page 5. They are historical reconciliation candidates, not a forecast list.

**Decision:** Reconcile those eight customer histories first; inspect all 60 accounts with any reconstructed plan loss next. **Confidence:** moderate for counts under the date rule; low for current/future risk.

### Q3 — What should RavenStack do, and what impact could it have?

**Answer:** Instrument lifecycle data, verify the 60 affected histories, audit tier-change flags, and then run an account-randomized customer-success pilot with verified eligibility and a 90-day customer-coverage outcome. A numerical sensitivity model on an *assumed* 60 currently eligible accounts produces net modeled value from **−$1,056** in a conservative case to **+$16,080** in an optimistic case, after an assumed $1,200 outreach cost. Neither value is observed revenue or a measured intervention effect; the negative case is decision-relevant.

**Decision:** Approve measurement and case reconciliation now; defer broad discounts or a scaled retention campaign until the pilot identifies incremental benefit. **Confidence:** high in the arithmetic; low in every scenario assumption.

## Page 3 — Monthly churn mathematics

The ledger is daily; executive rates are calculated from each month's opening cohort, not by averaging daily rates. “Account-month” and “relation-month” below are exposure units summed across monthly openings, not counts of distinct customers or products.

| Measure | 2023 | 2024 | What it says |
|---|---:|---:|---|
| Recorded churn-event rows | 73 | 527 | Event volume, not unique customers lost |
| Opening account exposure | 845 account-months | 3,909 account-months | 4.63× the exposure |
| Event rows / 100 account-months | 8.64 | 13.48 | Recorded-event intensity increased 56.1% |
| Reconstructed plan-proxy losses | 6 | 56 | Date-derived account × plan-tier coverage exits |
| Opening relation exposure | 1,406 relation-months | 9,414 relation-months | 6.70× relation exposure |
| Plan losses / 100 relation-months | 0.427 | 0.595 | Conditional plan-loss intensity increased 39.4% |
| Complete account-coverage-loss episodes | 2 | 6 | All eight episodes later returned by horizon end |
| Complete-loss episodes / 100 account-months | 0.237 | 0.153 | Conditional episode intensity decreased 35.2% |

Events rose by 454 rows. A symmetric rate/exposure decomposition attributes **338.9 rows (74.6%)** arithmetically to greater account-month exposure and **115.1 (25.4%)** to the higher recorded-event rate. This splits an identity; it does not establish what caused the rate change or whether event logging changed. For plan losses, both exposure and rate increased. For complete account-coverage-loss episodes, the normalized intensity fell. Thus “more cancellations because the business grew” is partly consistent with the data, but growth alone does not explain every event-rate movement.

The monthly chart in the PDF plots opening-cohort gross plan-proxy loss, persistent closing plan-proxy loss and complete-account loss as three distinct rates. January 2023 is undefined because its opening base is zero. October 2024 had the period's highest opening-cohort plan-loss rate: 9/1,073 = **0.84%**. December 2024 had the highest absolute count, **11 gross plan-loss events**; five opening-cohort relations lost coverage, 5/1,279 = **0.39%**. These numerators differ: December's 11 gross events are not the same measure as its five opening-cohort losses. The absolute-flow chart separates plan losses from new plan relationships, customer acquisitions and reactivations.

## Page 4 — Drivers and cross-table evidence

### Product value and price — declared signal, not root cause

The six event reason codes sum to 600 rows: features 114 (19.0%), support 104 (17.3%), budget 104 (17.3%), unknown 95 (15.8%), competitor 92 (15.3%), and pricing 91 (15.2%). The near-even spread supports investigating value realization, service and affordability; it does not identify a dominant causal driver. Event rows are not unique lost customers and the event table has no subscription ID.

### Usage — broadly stable recorded volume, weak temporal validity

Recorded usage count moved from 124,561 in 2023 to 125,964 in 2024 (+1.13%). Per observed usage account-month it moved from 24.462 to 24.747 (+1.17%). This modest aggregate increase is not evidence that every segment adopted more. Of 25,000 usage rows, 19,142 predate the linked subscription start and 290 follow a recorded end; only 5,568 rows fall within the reconstructed subscription intervals. The date-valid subset is a sensitivity, not a verified pre-cancellation window. Do not use it to claim a usage trajectory caused or prevented churn.

### Support — no clear descriptive separation

Among accounts with any event history, satisfaction averaged 3.9804 over 815 scored tickets (580/1,395 missing, 41.6%); among accounts without event history it averaged 3.9833 over 360 scored tickets (245/605 missing, 40.5%). Account-clustered satisfaction averages were 3.9616 across 330 scored accounts vs. 3.9703 across 136. Median first response was 89 vs. 87 minutes; median resolution was 35 hours in both groups. Account-level mean escalation rates were 4.93% vs. 4.49%. These retrospective, non-temporal differences are small and do not support a claim that service caused the recorded outcomes.

### Lifecycle records — the most actionable data finding

There are 500 accounts, 5,000 subscriptions, 25,000 usage rows, 2,000 tickets and 600 event rows. Any-event history marks 352 accounts; 110 account churn flags and 312 accounts with at least one flagged subscription are separate indicators. Account churn flag vs. any-event history disagrees for 312 accounts. The 5,000 subscription rows include 529 `upgrade_flag` and 218 `downgrade_flag` rows (23 with both), but no dated, linked from/to contract pair. This is why the next priority is measurement and reconciliation—not a premature root-cause campaign.

## Page 5 — Segments and account cases

### 2024 opening-cohort plan-tier comparison

| Plan-tier proxy | Opening relations | Lost at least once | Conditional rate (95% Wilson interval) | Still lost at year end |
|---|---:|---:|---:|---:|
| Enterprise | 120 | 5 | 4.17% (1.79–9.38%) | 2 |
| Basic | 132 | 2 | 1.52% (0.42–5.36%) | 1 |
| Pro | 122 | 0 | 0.00% (0.00–3.05%) | 0 |

Enterprise is 2.65 percentage points above Basic in this small reconstructed cohort. The intervals are broad and overlapping; selection, timing and tier semantics remain unresolved. Use this as an audit order, not a customer-risk score.

### Eight complete-coverage-loss episodes followed by return

Each row is a date-derived account-level episode. “Return” is the next observed customer coverage restoration; it may begin with a different tier. Account-only event reasons cannot be assigned to a specific plan transition.

| Account | Segment / source | First complete loss → return | Plan movement visible in ledger |
|---|---|---|---|
| A-180abf | DevTools · US · event | 2023-11-06 → 2024-01-17 | Enterprise lost; Basic restored; later Pro/Enterprise coverage |
| A-432483 | Cybersecurity · US · ads | 2023-04-05 → 2023-04-11 | Pro lost; Basic restored; later Enterprise and Pro coverage |
| A-40a557 | Cybersecurity · AU · partner | 2024-01-16 → 2024-02-12 | Enterprise lost and reactivated; later Pro/Basic added |
| A-8adedc | EdTech · US · event | 2024-03-09 → 2024-03-16 | Enterprise lost; Basic restored; Enterprise reactivated |
| A-c9bb3e | EdTech · US · ads | 2024-04-02 → 2024-04-25 | Pro lost and reactivated; Basic/Enterprise later added |
| A-0baac2 | FinTech · DE · organic | 2024-09-13 → 2024-10-14 | Enterprise lost; Basic restored; Enterprise reactivated |
| A-0a282f | DevTools · US · organic | 2024-09-25 → 2024-09-28 | Enterprise lost; coverage returned; Basic/Pro later added |
| A-410e86 | FinTech · US · organic | 2024-11-22 → 2024-11-29 | Enterprise lost and reactivated; Basic/Pro later added |

**Follow-up:** confirm whether each interval represents an actual service interruption, billing pause, administrative end date or data correction. Do not contact these accounts as if they are current at-risk customers without checking present status and permission.

## Page 6 — Decisions and quantified impact

### Five actions, in order

1. **Instrument lifecycle truth — Data/RevOps, days 0–30.** Add effective timestamps and a stable subscription/event link for cancellation, reactivation and plan change. KPI: share of lifecycle events tied to an eligible contract and reconciled.
2. **Reconcile historical cases — CS Operations + RevOps, days 0–30.** Review the 60 accounts with any date-derived plan loss, starting with the eight complete-loss/return histories. Planning effort: 60 × 15 minutes plus 8 × 30 minutes = **19 analyst/CS-operations hours**; this is a workload assumption, not a measured cost. KPI: reviewed cases with documented commercial state and reason.
3. **Audit Enterprise and plan transitions — RevOps, days 30–60.** Validate the 5/120 Enterprise result and inspect explicit upgrade/downgrade flags against contract source/destination, dates and comparable values. KPI: verified transition records, not flag counts.
4. **Validate the reason codes — CS + Product, days 30–60.** Sample feature, support and budget cases with structured follow-up. KPI: reason confirmed or corrected with a linked event and customer response.
5. **Run a controlled retention pilot — CS + Analytics, days 60–90.** After eligibility is fixed, randomize at account level to outreach/holdout; choose sample size by power analysis. Primary outcome: verified customer coverage at 90 days. Guardrails: downgrade, support burden and satisfaction.

### Scenario: what could an outreach pilot return?

The **60-account** count is a historical case-pool size used only to make the arithmetic concrete. It is not a current eligible list. Every monetary input below is an illustrative USD-equivalent assumption, not RavenStack revenue or market research. Cost is assumed for all 60 contacts. “Incremental lift” is a hypothetical percentage-point effect among participants; expected retained accounts can be fractional.

| Scenario | Uptake × lift | Expected retained equivalents | Assumed monthly value × horizon | Gross modeled value | Contact cost | Net modeled value | Break-even monthly value |
|---|---:|---:|---:|---:|---:|---:|---:|
| Conservative | 40% × 2 pp | 0.48 | $100 × 3 mo | $144 | $1,200 | **−$1,056** | $833.33 |
| Base | 60% × 5 pp | 1.80 | $200 × 6 mo | $2,160 | $1,200 | **+$960** | $111.11 |
| Optimistic | 80% × 10 pp | 4.80 | $400 × 9 mo | $17,280 | $1,200 | **+$16,080** | $27.78 |

> The 60 accounts are historical investigation cases, not a verified current eligible retention population. All scenarios assume eligibility and hypothetical values; they are not observed revenue or causal ROI.

Formula: retained equivalents = eligible accounts × uptake × incremental lift; gross value = retained equivalents × assumed monthly value × horizon; net modeled value = gross value − contact cost; break-even monthly value = contact cost ÷ (retained equivalents × horizon). The conservative case is negative. None is a forecast, causal estimate or accounting profit; excludes labor beyond assumed contact cost, margin, discounting, taxes and value after the stated horizon.

## Page 7 — Roadmap, method and limits

### 30 / 60 / 90 days

- **Days 0–30:** define active customer and cancellation events; reconcile effective dates; review the eight complete-loss/return cases and the remaining historical cases; assign lifecycle data owner by function.
- **Days 31–60:** audit Enterprise and transition flags; validate reason-code meaning; instrument activation and adoption timestamps; agree on recurring-revenue contract semantics.
- **Days 61–90:** only after eligibility and outcome are stable, launch an account-randomized outreach pilot; preregister primary/guardrail metrics and sample size; report effect with uncertainty before scaling.

### Definitions and confidence

- **Customer churn rate:** unique eligible customers lost in a period ÷ unique active customers at its opening. A commercially verified customer churn KPI is not identifiable from the conflicting account/event/subscription lifecycle records.
- **Plan-coverage proxy rate:** unique opening account × `plan_tier` relations losing date-derived coverage ÷ opening relations. For the 2024 opening cohort: 7/374 = 1.87% lost at any point; 3/374 = 0.80% still lost at year end; 0/190 opening accounts lost all coverage under this conditional reconstruction.
- **Recorded-event intensity:** event rows ÷ opening account-month exposure; 73/845 and 527/3,909. It is not a customer churn rate.
- The daily model unions same-account/same-plan intervals using `[start_date, end_date)`; null end dates are open only through the observation horizon. Thirteen nonpositive intervals remain excluded and disclosed. There is no stable `product_id`, no event-to-subscription foreign key, and no reconciled effective-dated recurring-revenue ledger.
- Usage totals are descriptive and most rows fall outside linked subscription intervals. Ticket comparisons are retrospective with 41.25% satisfaction missing. Reason codes are stated reasons, not causal proof. Tier flags lack dated from/to links. There is no calibrated future-risk model.

### Reproduce and explore

The five-table evidence and daily/monthly ledger are reproducible from the original CSVs; instructions are in `solution/README.md`. Start the complementary monthly lab from `solution/` with `docker compose up --build`. The lab distinguishes observed ledger rows from hypothetical scenario assumptions. The analysis uses the synthetic public dataset; credit River @ Rivalytics under its permissive MIT-like terms. G4 materials informed the challenge context, but this is an independent submission and does not imply G4 endorsement.

**Signature:** Observe (coffee) · Decompose (cube) · Persist (discipline) · Build (code)  
Prepared by Thomas Leick. No unverified credentials or personal claims are asserted.

