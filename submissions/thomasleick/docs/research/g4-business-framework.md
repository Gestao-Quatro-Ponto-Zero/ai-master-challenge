# Public G4 business concepts and RavenStack investigation

**Research checked:** 2026-10-21. This document summarizes public material; it does not claim access to G4's internal curriculum or a proprietary G4 framework.

## Source review

| Public source | What the source teaches | RavenStack translation |
|---|---|---|
| [G4 — Análise de coorte](https://g4educacao.com/blog/analise-de-coorte) | A cohort groups customers around a shared starting event/time. Compare a common outcome at equal elapsed intervals; newer cohorts have less follow-up, cohort size matters, and a retention matrix is useful only when the underlying dates and eligible population are sound. | Test signup and first-subscription-start cohorts. Do not call “ever had an event” a retention curve. Establish follow-up and cancellation eligibility before publishing rates. |
| [G4 — Customer Experience](https://g4educacao.com/programas-online/g4-experiencia-do-cliente) and [G4 Customer Experience](https://g4educacao.com/programas-presenciais/g4-customer-experience) | Public program descriptions connect customer experience to the end-to-end journey, customer needs, post-sale relationships, retention and recurring purchase. The public page describes retention/fidelization and customer-centered decisions. | Treat support and satisfaction as journey signals. Compare ticket experience with account-level outcomes, retain missing-score denominators, and avoid interpreting a cross-sectional association as a cause. |
| [G4 — Ideal Customer Profile](https://g4educacao.com/portal/icp-ideal-customer-profile) | The public article describes using customer segmentation and cohort/LTV patterns to identify profiles that create value, including sector, geography, budget/revenue and acquisition-channel questions. | Compare acquisition source, industry, country, plan, seats and trial status under each available churn label. Revenue/LTV-based ICP is not identifiable here because contract rows are not a reconciled revenue history. |
| [G4 — Estratégia comercial](https://g4educacao.com/portal/estrategia-comercial-passo-a-passo) | The public article describes using customer history to find profitable customer groups and aligning acquisition with durable value. | Examine whether acquisition channels have different label prevalence, controlling interpretation for segment size and label disagreement; do not infer channel quality from raw event volume. |
| [G4 — O que é LTV](https://g4educacao.com/blog/o-que-e-ltv) | Public material presents lifetime value as value accumulated over the customer relationship and relates it to acquisition economics. | Keep recorded MRR/ARR fields separate from current recurring revenue, lost revenue and lifetime value. No customer lifetime or reconciled revenue history is supplied. |
| [G4 — Marketing de relacionamento](https://g4educacao.com/blog/o-que-e-marketing-de-relacionamento) | The public article discusses relationship-building beyond acquisition, including retention and loyalty. | Prioritize a measurable post-sale journey, but test any outreach with a prospective comparison rather than claiming the current records prove its impact. |
| [G4 public portal](https://g4educacao.com/) | Public entry point to G4's business, growth, management and customer-experience material. | Use public claims as framing only; conclusions below come from RavenStack data, not from G4 endorsement. |

### Access and attribution notes

The direct cohort article was available through public indexed content and its canonical URL. Direct page access to some G4 pages may return access-denied responses to automated clients; where that occurred, this review relied on the official page's indexed public text and linked page metadata, not on private or course material. G4 pages are in Portuguese; English summaries above are our paraphrases. No long source excerpts are reproduced.

## Business investigation model (our interpretation)

This is an operational translation of the public concepts, not an official G4 framework.

| Dimension | Business question | Fields available | Current testability |
|---|---|---|---|
| Acquisition and ICP | Do channel or customer profiles show different outcome signals, at comparable denominators? | `referral_source`, `industry`, `country`, `seats`, account/subscription `plan_tier`, `is_trial`, label fields | Descriptive, label-conditioned comparisons are possible. Acquisition quality, CAC, margin and durable value are not present. |
| Activation and time to value | Does a new account reach meaningful first use after onboarding? | signup/start dates and dated feature-use rows | A first observed usage proxy can be calculated only for rows inside subscription bounds. Signup may not equal onboarding or subscription start; chronology is materially inconsistent. True activation/TTV is not established. |
| Adoption and engagement | Is usage broad across customers and product features, or concentrated? | `feature_name`, `usage_count`, duration, errors, beta flag, subscription ID | Descriptive concentration and valid-interval sensitivity can be calculated. Event-time pre-churn adoption is not reliable without a clean cancellation timeline. |
| Customer experience and friction | Are service experience signals associated with account outcome labels? | ticket date, priority, response/resolution time, satisfaction, escalation | Ticket and account rollups are descriptive. Satisfaction is missing for 825/2,000 tickets; temporal alignment and independent customer-level observations are unavailable. |
| Perceived value and economics | Do price, billing, contract movement or reason codes suggest value mismatch? | row-level MRR/ARR, billing frequency, upgrade/downgrade, refunds and reason codes | Recorded fields can be profiled. Repeated contract rows, missing lifecycle mapping and no verified snapshot date prevent current MRR, GRR/NRR, loss, LTV or recoverable exposure. |

## Cohort decision rules

The candidate signup cohort is `accounts.signup_date` grouped by calendar quarter. A first-subscription-start cohort is also considered, but an account can have multiple subscription rows and there is no reliable “first paid/eligible contract” definition. Trial status and plan are categorical attributes, not time cohorts by themselves. Event records can be summarized by elapsed time only as a data-quality diagnostic; conflicting outcome labels and absent exposure/eligibility prevent a retention heatmap. Any valid cohort work must show cohort size and follow-up/censoring explicitly.

## Investigation priorities

1. Resolve the account/subscription lifecycle and record an eligible-customer denominator.
2. Persist account-level acquisition, activation, feature-use, support and contract snapshots on a shared time axis.
3. Use the available data for descriptive, explicitly label-conditioned segment and journey diagnostics.
4. Test an intervention prospectively with an account-level holdout and defined retention outcome.
5. Rebuild an ICP/LTV view only after contract revenue and customer lifecycle are reconciled.

## References

- G4 public portal: https://g4educacao.com/
- G4 cohort analysis: https://g4educacao.com/blog/analise-de-coorte
- G4 Customer Experience (online): https://g4educacao.com/programas-online/g4-experiencia-do-cliente
- G4 Customer Experience (in person): https://g4educacao.com/programas-presenciais/g4-customer-experience
- G4 Ideal Customer Profile: https://g4educacao.com/portal/icp-ideal-customer-profile
- G4 commercial strategy: https://g4educacao.com/portal/estrategia-comercial-passo-a-passo
- G4 LTV: https://g4educacao.com/blog/o-que-e-ltv
- G4 relationship marketing: https://g4educacao.com/blog/o-que-e-marketing-de-relacionamento
