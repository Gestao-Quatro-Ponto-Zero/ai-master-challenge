# Executive paper acceptance review

**Scope:** rewritten executive paper only.  
**Status:** PASS for the paper deliverable; this does not certify commercial churn, root cause, recurring revenue, or intervention effects.

## Official challenge alignment

The current official Challenge 001 identifies three required diagnostic answers: cause of churn using cross-table evidence, segments and specific accounts with data, and concrete prioritized actions with estimated impact. It lists five-table joins, verifiable insights, actionable recommendations, correlation/causality distinction, and CEO readability as quality criteria. A predictive model or dashboard is presented as optional differentiation, while the process log is mandatory. The submission guide accepts a PDF/Markdown analysis and a written process narrative. Sources: [Challenge 001](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/blob/main/challenges/data-001-churn/README.md), [submission guide](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/blob/main/submission-guide.md), [contribution rules](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/blob/main/CONTRIBUTING.md), [README template](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/blob/main/templates/submission-template.md).

| Official question / criterion | Answer in the paper | Numerical evidence | Business interpretation and decision | Confidence / status |
|---|---|---|---|---|
| Q1. What is causing churn? | No causal root cause is established. The leading declared reason themes are product/features, support, and budget/value; lifecycle conflicts are the strongest operational finding. | Reasons: 114/600 features, 104/600 support, 104/600 budget. Account flag vs. any-event label differs for 312/500 accounts. Date ledger: 62 plan-proxy losses, 54 with another plan active, 8 complete account-coverage-loss episodes; all eight later returned. | Link events to subscriptions and effective dates; validate reason codes with customers; test the three themes separately. | PASS as an evidence-based diagnostic answer. Root-cause causality remains UNKNOWN and is stated specifically. |
| Q2. Which segments and specific accounts need attention? | Enterprise is the first segment to audit, followed by Basic; eight named historical full-coverage-loss/return cases are case-review candidates. | Enterprise 5/120 (4.17%, Wilson 95% 1.79–9.38); Basic 2/132 (1.52%, 0.42–5.36); Pro 0/122 (0–3.05). Eight accounts have dated loss/return histories; 60 accounts have any reconstructed plan loss. | Review historical cases and verify current status before outreach. Do not use the list as calibrated future risk. | PASS for historical descriptive prioritization; future-risk prediction remains UNKNOWN. |
| Q3. What should RavenStack do, and what impact could actions have? | Five sequenced actions: lifecycle instrumentation; historical case review; tier/flag audit; reason-code validation; randomized retention pilot. | Conditional impact for a hypothetical 60-account eligible cohort: modeled net value −$1,056 / +$960 / +$16,080 across conservative/base/optimistic assumptions; assumed contact cost $1,200. | Fund measurement and focused review first; test outreach after population and outcome definitions are valid. Conservative downside is visible. | PASS for a transparent scenario, not measured revenue, causal uplift, or accounting ROI. |
| Cross all five datasets | Accounts, subscriptions, usage, tickets and churn events are used at their native grains and compared with explicit time/identity caveats. | 500 / 5,000 / 25,000 / 2,000 / 600 source rows. | Outcome labels do not share a proven single lifecycle definition; one-to-many data are not mistaken for customer counts. | PASS; source hashes and artifact hashes are recorded in both manifests. |
| CEO readability | Seven-page executive structure with direct answers on page 2, monthly trends on page 3, evidence and account cases on pages 4–5, action and scenarios on page 6, and method/roadmap on page 7. | Three distinct units/rates and their denominators are labeled. | Action follows the evidence instead of opening with a standalone UNKNOWN block. | PASS by rendered PDF inspection; this is not React/browser QA. |
| Process log | Existing chronological process log retained; this rewrite adds prompt reference and checkpoint 52. | Current work, actual correction, commands and results are recorded. | No historical human decisions or AI mistakes were invented. | PASS for written narrative. |

## Numerical review

The original five CSVs were rehashed and matched the daily ledger metadata. The existing business-driver script and daily ledger engine were rerun into a temporary directory inside the authorized package; business JSON was byte-semantically identical and ledger summaries, periods, segments, candidates and reconciliation sections matched the preserved G4-alignment outputs. The final revision also verifies that January 2023 has a zero opening denominator and null rates, and labels its monthly churn `UNDEFINED` rather than 0%.

- 2023 / 2024 event exposure: 73/845 and 527/3,909 = 8.6391 and 13.4817 recorded event rows per 100 account-months.
- 2023 / 2024 plan proxy: 6/1,406 and 56/9,414 = 0.4267 and 0.5949 coverage-loss events per 100 relation-months.
- 2023 / 2024 full-account coverage-loss episodes: 2/845 and 6/3,909 = 0.2367 and 0.1535 per 100 account-months.
- Symmetric rate/exposure decomposition of the 454 added event rows: +338.9 from greater exposure and +115.1 from changed event intensity. This is an arithmetic identity decomposition, not a causal attribution.
- The 2024 opening cohort has 190 accounts and 374 account-plan-tier relations; 7/374 lost at least once, 3/374 remained uncovered at year-end, and 0/190 opening accounts lost all coverage under the conditional date reconstruction.
- The support, usage, reason-code, plan-segment, and subscription-flag figures in the paper match their source analysis outputs and original CSV fields. The independent paper test verifies their key denominators.

All scenario arithmetic is shown in [the numerical manifest](../paper/PAPER-NUMERICAL-EVIDENCE-MANIFEST.md). Values are illustrative USD-equivalent assumptions, not amounts observed in the dataset. The potential outcome is modeled value less assumed outreach cost only; it is not accounting profit.

## Editorial and visual review

The previous PDF, Markdown, generator, and JSON manifest were copied to `docs/paper/archive/2026-10-22-pre-rewrite/` before replacement. The revised PDF uses seven A4 pages, keeps methodology to the final page, brings the three answers and business interpretation forward, adds a readable 24-month trend and flow charts, and replaces symbolic-only impact with explicit negative/base/positive cases. The chart distinguishes plan-proxy gross loss, persistent loss and complete-account coverage loss. The 95% Wilson intervals make the small segment samples visible.

All seven final pages were rendered at 160 dpi and inspected in the final render set. Full-resolution review caught and corrected a slightly over-wide support table and a note overlapping its final row; the January 2023 subtitle now explicitly states the zero-denominator rule. The scenario arithmetic test initially failed on exact binary-float equality; it was corrected to compare at 9 decimal places without changing the calculations. No React/browser visual claim is made here.

## Acceptance matrix

| Paper acceptance item | Status | Evidence |
|---|---|---|
| Current official questions and submission requirements reviewed | PASS | Public official sources linked above. |
| Executive answers direct and substantive | PASS | Page 2 and the full answer table in this review. |
| Reproducible numeric evidence | PASS | Source script rerun, hash validation, evidence manifest and tests. |
| Segments show denominators and uncertainty | PASS | 2024 opening-cohort counts and Wilson intervals. |
| Specific accounts are justified | PASS | Eight dated complete-loss/return histories with segment and plan movement. |
| Actions are prioritized and tied to findings | PASS | Five actions, responsible functions, timing, KPIs and experiment plan. |
| Numeric impact and downside included | PASS | Three transparent, hypothetical cases; conservative case is negative. |
| Causality, proxy units and monetary limits clear | PASS | Page-level labels and method definitions. |
| PDF generated, seven pages, rendered and inspected | PASS | `pdfinfo`, Poppler renders, visual inspection; current PDF hash in manifest. |
| Zero-denominator month not rendered as 0% | PASS | Jan-23 source rates are null; PDF says `UNDEFINED, not 0%`; regression assertion added. |
| Historical paper recoverable | PASS | Four prior artifacts preserved in archive folder. |
| README and process log updated | PASS | Candidate README, prompt record, checkpoint 52 and progress log. |

## Remaining boundaries

- No causal root cause or causal effect is identified by the synthetic observational dataset.
- Customer churn as an officially verified commercial KPI, current eligible accounts, MRR/ARR churn and calibrated future risk remain UNKNOWN.
- The three financial cases are decision sensitivities, not forecasts; replace their assumed unit values, contact cost, uptake, lift and horizon with approved internal inputs before budgeting.
- Browser viewport QA applies to the companion frontend and remains separate from the completed PDF visual inspection.
- No Git or remote operation was performed.
