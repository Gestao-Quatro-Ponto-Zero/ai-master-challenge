# G4 public methodology addendum — customer churn mission

**Checked:** 2026-10-21. This addendum records public G4 material relevant to the final customer-churn investigation. It describes public teaching and our own implementation separately; it does not claim access to proprietary G4 course material.

## Public concepts verified

- G4's cohort material describes groups linked by a time-based starting event, then compares a consistent outcome across equal elapsed periods. It discusses cohort size, different follow-up lengths, and reading retention across a cohort over time. Sources: [Análise de coorte (portal)](https://g4educacao.com/portal/analise-de-coorte) and [O que é análise cohort? (blog)](https://g4educacao.com/blog/analise-de-coorte).
- G4's ICP article discusses using customer segmentation and cohort/LTV history to learn which customer profiles produce more value over time, including industry, geography, company size/budget and acquisition-channel questions. Source: [ICP — Ideal Customer Profile](https://g4educacao.com/portal/icp-ideal-customer-profile).
- G4's Customer Experience program description connects customer fit, the pre-to-post-sale journey, service consistency, relationship activation and retention. Source: [G4 Customer Experience](https://g4educacao.com/programas-online/g4-experiencia-do-cliente).
- G4's LTV article defines lifetime value through value returned over a customer's relationship and connects it to acquisition economics and customer experience. Source: [LTV: what it is and how to calculate](https://g4educacao.com/blog/o-que-e-ltv).

The G4 pages were checked through public indexed text on the date above; direct automated page retrieval returned HTTP 403 in this environment. The paraphrases above are limited to the publicly indexed content. No G4 proprietary formula or endorsement is asserted.

## RavenStack implementation choices

The classical customer KPI is defined here as unique eligible accounts lost during a period divided by unique active accounts at the beginning of that period. This formula is the challenge's stated business metric, not a formula attributed uniquely to G4. A cohort retention series requires an identifiable acquisition cohort, valid customer status at each elapsed-period boundary and sufficient follow-up. RavenStack can produce a first-subscription-start month and a date-rule activity diagnostic, but source lifecycle conflicts keep the result conditional and preclude publishing it as verified retention.

The ICP application is likewise a descriptive investigation: segment label prevalence is displayed with sample counts and is not called churn. Activation, support experience and product adoption are considered along the customer journey, but timestamps and outcome conflicts prevent causal claims. LTV and recurring revenue exposure remain unknown because the records do not form an account-period revenue history.
