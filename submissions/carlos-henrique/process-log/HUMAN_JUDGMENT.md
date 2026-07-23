# Human Judgment in JourneyGraph

## Purpose

This document records the human decisions that changed the scope, method, architecture, governance, and product of JourneyGraph. It separates implementation proposals from the final choices approved by Carlos Henrique and links every material judgment to repository evidence.

## Decision Framework

Decisions were reviewed against data validity, temporal integrity, analytical defensibility, privacy, reproducibility, evaluator clarity, operational safety, and scope discipline. A proposal advanced only when its assumptions, evidence boundary, validation path, and residual limitation were explicit.

## Key Human Decisions

### HJ-001 — Reject the mega-join approach

- **Context:** The five sources use different grains and one-to-many relationships.
- **AI or implementation suggestion:** A consolidated table appeared to simplify downstream analysis.
- **Human concern:** Row multiplication would inflate counts and financial aggregates while obscuring provenance.
- **Final decision:** Keep source-specific grains and build temporal events instead of a mega-table.
- **Evidence:** [Relationship audit](../solution/reports/relationship-audit.md) measured 147,896 rows from 500 accounts (295.792×); [D014](decisions.md#d014--política-contra-mega-join) prohibits the join.
- **Impact:** All later evidence retains an explicit grain and reconciliation path.
- **Trade-off:** More transformation logic in exchange for defensible totals.
- **What would have happened otherwise:** Plausible-looking counts and MRR sums could have been materially overstated.

### HJ-002 — Build a canonical event log before analysis

- **Context:** Account, subscription, usage, support, and churn timestamps were fragmented.
- **AI or implementation suggestion:** Analyze each source directly and reconcile later.
- **Human concern:** Journey order and cutoffs would vary across analyses.
- **Final decision:** Normalize governed events first, then derive diagnostics and journeys.
- **Evidence:** [Event-log validation](../solution/reports/event-log-validation.md), [temporal rules](../solution/reports/temporal-rules.md), and commit `75be8ef0663f0f49b425092735ffe0a3c6ed65f6`.
- **Impact:** Downstream phases share one temporal contract.
- **Trade-off:** An additional foundation phase before business analysis.
- **What would have happened otherwise:** Each analysis could have embedded incompatible time and identity rules.

### HJ-003 — Quarantine invalid or temporally ambiguous records

- **Context:** 21,659 event opportunities violated fatal temporal rules.
- **AI or implementation suggestion:** Repair or drop invalid-looking rows to simplify the active set.
- **Human concern:** Silent correction or deletion would erase the quality trail.
- **Final decision:** Preserve those rows as `QUARANTINED` and exclude them from behavioral evidence.
- **Evidence:** [Quarantine report](../solution/reports/quarantine-report.md), [D023](decisions.md#d023--política-de-quarentena), and commit `75be8ef0663f0f49b425092735ffe0a3c6ed65f6`.
- **Impact:** Quality debt remains measurable without contaminating behavior.
- **Trade-off:** Lower usable coverage in exchange for temporal integrity.
- **What would have happened otherwise:** Invalid chronology could have entered journeys as if observed.

### HJ-004 — Separate MAIN and STRICT populations

- **Context:** Warnings were usable with caveats, but not equivalent to fully valid events.
- **AI or implementation suggestion:** Use one maximum-coverage population.
- **Human concern:** A single population would hide sensitivity to temporal quality.
- **Final decision:** Define MAIN as `VALID + VALID_WITH_WARNING` and STRICT as `VALID`, with quarantine excluded from both.
- **Evidence:** [Survival sensitivity](../solution/reports/survival-sensitivity.md), [D046](decisions.md#d046--populações-estrita-e-principal), and commit `83d9b16a270e2227bd67c52e4ebf3ce4aae3eb61`.
- **Impact:** Findings expose coverage and stability differences.
- **Trade-off:** More reporting complexity and fewer simple headline claims.
- **What would have happened otherwise:** Warning-sensitive conclusions could have appeared stable.

### HJ-005 — Preserve recurrent churn and reactivation episodes

- **Context:** Accounts can churn repeatedly and later reactivate.
- **AI or implementation suggestion:** Reduce each account to one final churn state.
- **Human concern:** A terminal label would erase lifecycle recurrence and return episodes.
- **Final decision:** Preserve ordered churn events and explicit reactivations as distinct events.
- **Evidence:** [Churn diagnostic](../solution/reports/churn-diagnostic.md), [D025](decisions.md#d025--modelo-de-churn-recorrente), [D026](decisions.md#d026--modelo-de-reativação), and commit `dd1f013cc502d9e690a1790331397897729edfd3`.
- **Impact:** Journeys can represent recurrent churn and post-reactivation behavior.
- **Trade-off:** More complex outcome taxonomy.
- **What would have happened otherwise:** Recurrence and reactivation would have been misclassified or lost.

### HJ-006 — Reject Cox proportional hazards for the final deliverable

- **Context:** The STRICT population had 46 eligible events, endpoints were warning-sensitive, and proportional-hazards stability was not established.
- **AI or implementation suggestion:** Add Cox regression as the central survival result.
- **Human concern:** Coefficients and hazard ratios would overstate an unsupported model.
- **Final decision:** Do not execute Cox; retain descriptive survival curves, at-risk tables, RMST, and sensitivity evidence.
- **Evidence:** [Survival assumptions](../solution/reports/survival-assumptions.md), [survival analysis](../solution/reports/survival-analysis.md), [D050](decisions.md#d050--critérios-para-cox), and commit `83d9b16a270e2227bd67c52e4ebf3ce4aae3eb61`.
- **Impact:** The deliverable contains no Cox coefficient, score, or hazard ratio.
- **Trade-off:** Less model sophistication in exchange for methodological honesty.
- **What would have happened otherwise:** An unstable model could have become the most visible result.

### HJ-007 — Promote only stable journey patterns

- **Context:** Frequency alone did not establish cross-population stability or safe same-day ordering.
- **AI or implementation suggestion:** Add every frequent pattern to the graph.
- **Human concern:** Unsupported or order-sensitive patterns would gain unwarranted authority.
- **Final decision:** Promote only ROBUST or SENSITIVE evidence that passes support, sample, denominator, and same-day dependency gates.
- **Evidence:** [Journey stability](../solution/reports/journey-stability.md), [graph methodology](../solution/reports/graph-methodology.md), [D061](decisions.md#d061--estabilidade-principal-versus-estrita), and commit `1c31ae22632d27ac45137af5b55acee1d6f19f86`.
- **Impact:** Rejected patterns remain counted but are absent from promoted graph evidence.
- **Trade-off:** A smaller graph with clearer provenance.
- **What would have happened otherwise:** Fragile frequency could have been mistaken for reliable structure.

### HJ-008 — Use NetworkX first and make Neo4j optional

- **Context:** The evaluation needed to run locally without a graph server or credentials.
- **AI or implementation suggestion:** Make Neo4j the primary runtime for graph sophistication.
- **Human concern:** A mandatory external service would weaken reproducibility and evaluator access.
- **Final decision:** Use NetworkX as the reference runtime and provide Neo4j only as an optional export.
- **Evidence:** [Graph methodology](../solution/reports/graph-methodology.md), [Neo4j guide](../solution/reports/neo4j-guide.md), [D064](decisions.md#d064--networkx-como-referência), and commit `1c31ae22632d27ac45137af5b55acee1d6f19f86`.
- **Impact:** The graph is inspectable with the local Python environment.
- **Trade-off:** Fewer live graph-database capabilities in the demonstration.
- **What would have happened otherwise:** Evaluation would depend on infrastructure outside the repository.

### HJ-009 — Build deterministic review queues instead of churn probabilities

- **Context:** No validated predictive model existed for individual prioritization.
- **AI or implementation suggestion:** Produce a probability-based ranking for operational appeal.
- **Human concern:** Numeric precision would imply predictive validation that had not occurred.
- **Final decision:** Use versioned deterministic rules, discrete priority components, evidence packets, and human disposition.
- **Evidence:** [Watchlist methodology](../solution/reports/watchlist-methodology.md), [intervention watchlist](../solution/reports/intervention-watchlist.md), [D078](decisions.md#d078--prioridade-sem-score-preditivo), and commit `1ed6655cf86f9068f56a10af25537ea8747a25b1`.
- **Impact:** Inclusion is explainable and review-oriented.
- **Trade-off:** No individualized forecast or optimized ranking.
- **What would have happened otherwise:** A deterministic heuristic could have been misread as a validated model.

### HJ-010 — Distinguish behavioral review from data-quality review

- **Context:** Quarantined or warning-heavy histories require remediation, not behavioral interpretation.
- **AI or implementation suggestion:** Combine all noteworthy accounts in one operational list.
- **Human concern:** Data defects could be mistaken for customer behavior.
- **Final decision:** Keep `DATA_QUALITY_REVIEW` separate and prevent quarantine from producing behavioral signals.
- **Evidence:** [Watchlist methodology](../solution/reports/watchlist-methodology.md), [watchlist validation](../solution/reports/watchlist-validation.md), [D079](decisions.md#d079--qualidade-antes-de-comportamento), and commit `1ed6655cf86f9068f56a10af25537ea8747a25b1`.
- **Impact:** Queue purpose and owner remain explicit.
- **Trade-off:** Some accounts can appear in separate quality and behavioral workflows.
- **What would have happened otherwise:** Operational review could have acted on measurement failure.

### HJ-011 — Treat associated MRR as context, not revenue at risk

- **Context:** MRR can be associated with an account or queue at a governed cutoff.
- **AI or implementation suggestion:** Translate associated MRR into a financial-loss headline.
- **Human concern:** Association does not establish loss, recovery, or intervention impact.
- **Final decision:** Show deduplicated associated MRR only as descriptive context.
- **Evidence:** [Revenue diagnostic](../solution/reports/revenue-diagnostic.md), [watchlist validation](../solution/reports/watchlist-validation.md), [D082](decisions.md#d082--mrr-deduplicado-e-contextual), and commit `1ed6655cf86f9068f56a10af25537ea8747a25b1`.
- **Impact:** Financial interpretation remains bounded to the historical snapshot.
- **Trade-off:** Less dramatic executive framing.
- **What would have happened otherwise:** Historical association could have been presented as attributable value.

### HJ-012 — Classify experiment readiness instead of claiming experiment success

- **Context:** The repository contains design specifications and assignment simulations, not executed interventions or outcomes.
- **AI or implementation suggestion:** Present the catalog as a set of validated opportunities.
- **Human concern:** Planning readiness could be confused with measured effectiveness.
- **Final decision:** Keep causal status `UNTESTED` and classify planning feasibility as ready for review, pilot only, underpowered, or not feasible.
- **Evidence:** [Experiment registry](../solution/reports/experiment-registry.md), [experiment validation](../solution/reports/experiment-validation.md), [D086](decisions.md#d086--desenho-não-execução), and commit `3e96b07e9f113c15ec2a9635324054c3e7b27b00`.
- **Impact:** Eight test designs remain hypotheses rather than results.
- **Trade-off:** The product demonstrates governance, not uplift.
- **What would have happened otherwise:** Unevaluated designs could have sounded completed.

### HJ-013 — Keep human review mandatory

- **Context:** Review queues can surface evidence but cannot authorize a customer intervention.
- **AI or implementation suggestion:** Attach automatic actions to prioritized cases.
- **Human concern:** Evidence quality, consent, policy, and experiment assignment still require accountable review.
- **Final decision:** Require a human reviewer for every disposition and prohibit automatic contact or intervention.
- **Evidence:** [Intervention watchlist](../solution/reports/intervention-watchlist.md), [experiment governance](../solution/reports/experiment-governance.md), [D084](decisions.md#d084--nenhuma-intervenção-automática), and commit `1ed6655cf86f9068f56a10af25537ea8747a25b1`.
- **Impact:** JourneyGraph supports investigation rather than customer treatment.
- **Trade-off:** Lower operational automation.
- **What would have happened otherwise:** A review aid could have crossed into an unapproved decision system.

### HJ-014 — Use a fixed deterministic demo

- **Context:** Evaluators needed a reproducible product surface with no external services.
- **AI or implementation suggestion:** Use live data or runtime-generated explanations for a richer demo.
- **Human concern:** Network, credentials, model variability, and changing inputs would prevent repeatable review.
- **Final decision:** Build the interface from fixed, validated local JSON snapshots and controlled copy.
- **Evidence:** [Dashboard data contract](../solution/reports/dashboard-data-contract.md), [dashboard validation](../solution/reports/dashboard-validation.md), [D099](decisions.md#d099--json-local-e-determinístico), and commit `fb6f09a34be2a77b3917b798ec22ed9fd56728ff`.
- **Impact:** The same governed evidence is available offline on every run.
- **Trade-off:** No live ingestion or runtime generation in the demonstration.
- **What would have happened otherwise:** Evaluator results could depend on external state.

### HJ-015 — Localize the interface to pt-BR

- **Context:** The first dashboard release used English while the demonstration audience required Brazilian Portuguese.
- **AI or implementation suggestion:** Retain the English interface for broad enterprise familiarity.
- **Human concern:** The visible product was inconsistent with the intended demonstration and user feedback.
- **Final decision:** Localize every visible route, shared surface, metadata item, and accessibility label to pt-BR.
- **Evidence:** [Localization validation](../solution/reports/localization-validation.md), [D109](decisions.md#d109---interface-final-localizada-em-pt-br), and commit `de4ca14c66d33319af15aae492d04caadb910ff1`.
- **Impact:** Nine routes and shared components use controlled pt-BR copy.
- **Trade-off:** Submission documentation remains English while the product interface is pt-BR.
- **What would have happened otherwise:** The evaluator would encounter a bilingual, audience-misaligned product.

### HJ-016 — Remove visible account identifiers from the demo

- **Context:** Internal analytical keys were useful for joins but unnecessary on screen.
- **AI or implementation suggestion:** Display internal keys to make examples traceable.
- **Human concern:** Visible operational-looking identifiers increased privacy and interpretation risk.
- **Final decision:** Keep keys internal and render only controlled anonymous profile aliases.
- **Evidence:** [Localization validation](../solution/reports/localization-validation.md), [dashboard validation](../solution/reports/dashboard-validation.md), [D112](decisions.md#d112---identificadores-demo-mantidos-apenas-internamente), and commit `de4ca14c66d33319af15aae492d04caadb910ff1`.
- **Impact:** The demo remains traceable internally without exposing account keys visually.
- **Trade-off:** On-screen examples cannot be copied back to an operational account.
- **What would have happened otherwise:** Internal identifiers would have remained visible in an evaluator-facing surface.

### HJ-017 — Reject generic lexical translation

- **Context:** Word-by-word substitution produced mixed-language and grammatically invalid phrases.
- **AI or implementation suggestion:** Translate dynamically through a generic lexical mapping.
- **Human concern:** Partial replacement changed meaning and failed on unknown values.
- **Final decision:** Use complete reviewed messages and closed mappings only for known enums and statuses.
- **Evidence:** [Localization validation](../solution/reports/localization-validation.md), [D111](decisions.md#d111---proibição-de-tradução-lexical-genérica), error E074 in [workflow](workflow.md), and commit `de4ca14c66d33319af15aae492d04caadb910ff1`.
- **Impact:** Copy is semantically controlled and unknown values remain intact.
- **Trade-off:** More deliberate message maintenance.
- **What would have happened otherwise:** New phrases could have rendered as broken hybrid text.

### HJ-018 — Make `build:data` cross-platform

- **Context:** The documented npm command failed under the default Windows shell.
- **AI or implementation suggestion:** Keep a direct Python workaround in the Quick Start.
- **Human concern:** The official evaluator path did not match the tested product path across operating systems.
- **Final decision:** Add a dependency-free Node wrapper and restore `npm run build:data` as the official command.
- **Evidence:** [Metric consistency matrix](../solution/reports/metric-consistency-matrix.md), [D121](decisions.md#d121--npm-builddata-must-be-cross-platform), [D122](decisions.md#d122--node-wrapper-over-shell-specific-package-script), and commit `8f785e25d3652068a356f213fc6f596d76f8b266`.
- **Impact:** Windows, Linux, and macOS use one evaluator workflow.
- **Trade-off:** A small wrapper is retained instead of a shorter package alias.
- **What would have happened otherwise:** Evaluators could have needed platform-specific manual steps.

## Limitations

These entries are a curated synthesis, not a transcript of every interaction. The repository proves the final decision, implementation, and validation state; transient suggestions are described only to the level supported by logs and corrective artifacts. Human approval remains responsible for interpretation, scope, and any future operational use.
