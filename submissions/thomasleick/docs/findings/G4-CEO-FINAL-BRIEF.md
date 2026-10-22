# RavenStack — CEO decision brief

## The decision

**Customer churn rate: UNKNOWN.** The source records do not reliably identify which customers were lost.

The classical formula is:

> Unique eligible customers lost during the period ÷ unique active customers at the start of the period.

For 2024, the literal subscription-date rule gives **0/191 = 0.0% conditional account-coverage loss**. Do not report that as RavenStack's actual churn rate: **103 of the same 191 opening accounts have a 2024 non-reactivation departure event**, and **443 of 472 non-reactivation event rows coincide with a date-active subscription**. 2023 has no opening customer denominator, so its annual rate is undefined.

## What is known

- The 2024 opening population contains 191 distinct accounts and 655 active subscription records.
- 66 opening subscription records end by the next annual boundary; this is 10.08% subscription-row attrition, not customer churn. The accounts remain covered by other recorded subscription rows under the date rule.
- The 2024 account bridge balances at 500 accounts at the next boundary, but this is only a date-boundary set reconciliation, not proof that no customers churned during the year.
- Event reasons include features (91/472), budget (82), support (81) and pricing (72). These labels direct investigation; they do not prove causes.
- DevTools is a review segment (35/113 account flags; 75/113 event-labeled in 2024). These are inconsistent label prevalences, not validated retention or risk.
- A date-rule cohort diagnostic has 24 cohorts and 300 age points, with four intermediate dips. Lifecycle conflict prevents calling it verified retention.
- Actual lost MRR, LTV, causal drivers and predictive risk remain unknown.

## Five actions

1. **Reconcile customer lifecycle** — Data/Engineering + RevOps; 0–30 days. Link accounts, subscriptions and events; define effective end, cancellation and reactivation. Success: auditable account-month state.
2. **Adjudicate repeated event cases** — Customer Success + RevOps; 0–30 days. Review cases such as `A-37f969`, `A-ee42db`, `A-1b9609` and `A-32fb14`. These are record-review priorities, not predicted churn.
3. **Rebuild ICP cohorts** — Marketing/Sales + Analytics; 31–60 days. Compare mature equal-age cohorts by acquisition, industry, country and plan after lifecycle repair.
4. **Instrument activation and value realization** — Product + Customer Success; 31–60 days. Capture onboarding completion, first value and account-level adoption at consistent timestamps.
5. **Pilot only after eligibility is reliable** — Customer Success + Analytics; prepare by day 60, launch by day 90 if sample size permits. Randomize by account; measure verified 90-day logo retention and discount/support guardrails.

**Do not launch a broad save campaign from current labels.** First reconcile who is active and who actually left; then test targeted interventions against a holdout.

## Evidence and limitations

The analysis uses the supplied synthetic Rivalytics data. The source says blank subscription ends mean active, but account-level events conflict with that state. See the detailed [customer churn report](G4-CUSTOMER-CHURN-FINAL.md) and the original [source dataset notes](../../solution/data/raw/README.md). Public G4 cohort and ICP concepts informed the investigation design; no proprietary G4 method or causal result is claimed.
