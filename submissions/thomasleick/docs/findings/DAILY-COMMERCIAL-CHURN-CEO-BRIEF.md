# RavenStack — Daily Commercial Churn
## CEO brief

### What we can say

The five source tables do not include a product/service identifier. We therefore reconstructed daily coverage by **account × plan label**, explicitly a **PLAN-LEVEL PROXY**. Date semantics are also conditional: the calculation uses `[start_date, end_date)`, treats blank end dates as right-censored through 2024-12-31, and has date-only records with no known timezone.

Over 2023-01-01 to 2024-12-31, this model records:

- **62** losses of account-plan coverage across **60 accounts**.
- **54/62** plan losses while another plan label remained active.
- **8** full account-coverage loss events across **8 accounts**; all eight later regained recorded coverage before the observed window ended.
- **43** plan-relation returns and **8** full-account coverage returns.
- **949** plan-count expansion account-days and **53** plan-count contraction account-days among accounts that remained covered throughout the day.
- **0** daily plan bridge failures and **0** daily customer bridge failures.

These are reproducible date-based movements, not commercially verified churn or product migration. A same-day transition is represented as an exit from the old plan label and a start of the new one; it is not called a migration without contract linkage.

### 2024 view

The daily-ledger period opens from 2023-12-31 close with **190 accounts / 374 plan proxies**. During 2024 it records **1,055 first plan-proxy starts**, **41 returns**, **56 gross plan-proxy losses**, and closes with **500 accounts / 1,414 plan proxies**. Seven of the 374 opening plan relations lost coverage at some point (**1.87%**); three were still inactive at year close (**0.80%**). The ledger records six gross full-account loss events and seven account returns in 2024; no opening account remains without coverage at year close (**0/190** under the pre-transition ledger boundary).

A snapshot on 2024-01-01 after that date's starts instead shows **191 accounts / 379 plan proxies**. Five relations start on Jan 1, including one new account. Date-only data cannot resolve intraday order, so these two valid boundary conventions are reported separately. Neither supports an unconditional, official customer churn KPI.

### What remains unknown

- A true product/service churn rate: product identity is absent.
- Commercially verified customer churn: event records and date-derived coverage conflict, and end-date semantics are not contractually precise.
- Upgrade/downgrade truth: the Basic/Pro/Enterprise ranking is not documented and there is no explicit contract transition key. At a 30-day candidate window, 52 possible upgrade pairs and 51 possible downgrade pairs are generated; these are not confirmed.
- Lost MRR, revenue contraction, gross/net revenue churn and LTV: row-level MRR/ARR lack verified currency, effective-period and version/lineage semantics.
- Root cause and predictive account risk: the records are synthetic and do not provide reliable causal or future-risk labels.

### Decisions for leadership

1. **Repair commercial lifecycle instrumentation first.** RevOps and Data should add stable customer/product/contract-line IDs, effective dates, cancellation/renewal/replacement links, event types and currency-aware recurring value.
2. **Reconcile the 60 accounts with plan losses**, prioritizing the eight full coverage gaps. Customer Success and RevOps should document whether each was a true cancellation, pause, administrative row ending, renewal, or other lifecycle event.
3. **Separate customer loss from plan loss in reporting.** Never use event-row counts or subscription flags as customer churn.
4. **Instrument activation and adoption against a stable account-product identity.** Define first value and equal elapsed cohort windows before inferring acquisition quality or journey problems.
5. **Run an intervention experiment only after eligibility is valid.** Randomize accounts, use a concurrent control, and measure verified account retention and guardrails over the relevant renewal window.

### 30/60/90-day sequence

| Window | Owner function | Deliverable | Success measure |
|---|---|---|---|
| Days 0–30 | RevOps + Data | Contract lifecycle dictionary and reconciliation of 60 observed candidates | Every candidate has a verified outcome or explicit unresolved status |
| Days 31–60 | Product Analytics + Customer Success | Stable identity, activation milestones, product usage and support joins | Complete account-product timeline and measured time-to-first-value |
| Days 61–90 | Customer Success + Analytics | Pilot retention experiment, if eligible population and baseline are valid | Treatment-control difference in verified retention with guardrails and uncertainty |

No financial impact, intervention lift or cost is claimed. The local evidence dashboard is available at `http://localhost:15175` when the project Compose services are running. Browser visual QA was blocked by the browser security surface in this run, so the live visual layout is not certified.
