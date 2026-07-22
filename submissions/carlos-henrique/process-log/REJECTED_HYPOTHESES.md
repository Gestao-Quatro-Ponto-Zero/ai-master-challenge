# Rejected Hypotheses and Approaches

## Purpose

These alternatives appeared plausible during implementation but were rejected after human review of repository evidence. Rejection applies to the current fixed snapshot and evaluation scope; residual uncertainty records what new evidence would be needed to revisit a choice.

## Rejection Register

### RH-001 — One consolidated join would simplify analysis

- **Hypothesis or approach:** Join all five sources into one analytical table.
- **Why it appeared plausible:** A single table can reduce query complexity.
- **Evidence reviewed:** [Relationship audit](../solution/reports/relationship-audit.md) and [data contract](../docs/data-contract.md).
- **Reason for rejection:** The chain produced 147,896 rows from 500 accounts and would inflate measures.
- **Decision:** Preserve source grains and normalize temporal events.
- **Residual uncertainty:** A purpose-specific aggregate may be safe only with an explicit grain and reconciliation.

### RH-002 — A single account-level churn label would be sufficient

- **Hypothesis or approach:** Represent each account by one terminal churn flag.
- **Why it appeared plausible:** It simplifies segmentation and reporting.
- **Evidence reviewed:** [Churn diagnostic](../solution/reports/churn-diagnostic.md) and [event-log validation](../solution/reports/event-log-validation.md).
- **Reason for rejection:** It removes recurrent churn and explicit reactivation episodes.
- **Decision:** Preserve event sequences and derive a controlled summary outcome separately.
- **Residual uncertainty:** A terminal label may remain useful for a narrowly defined report if recurrence is still accessible.

### RH-003 — All temporally valid-looking records could remain in the main population

- **Hypothesis or approach:** Treat all parseable timestamps as equally usable.
- **Why it appeared plausible:** Parsing success looks like a simple quality gate.
- **Evidence reviewed:** [Temporal audit](../solution/reports/temporal-audit.md), [quarantine report](../solution/reports/quarantine-report.md), and [survival sensitivity](../solution/reports/survival-sensitivity.md).
- **Reason for rejection:** Lifecycle contradictions and warnings materially change coverage and some findings.
- **Decision:** Separate quarantine, MAIN, and STRICT populations.
- **Residual uncertainty:** Upstream corrections could move individual rows between populations.

### RH-004 — All frequent patterns should be promoted to the graph

- **Hypothesis or approach:** Use frequency as the sole graph admission rule.
- **Why it appeared plausible:** Frequent sequences are easy to explain and visualize.
- **Evidence reviewed:** [Journey stability](../solution/reports/journey-stability.md) and [graph methodology](../solution/reports/graph-methodology.md).
- **Reason for rejection:** Some patterns are unstable, under-supported, or dependent on assigned same-day order.
- **Decision:** Admit only ROBUST or SENSITIVE patterns that pass all promotion gates.
- **Residual uncertainty:** Stability must be retested on a future snapshot.

### RH-005 — A churn probability score would improve prioritization

- **Hypothesis or approach:** Rank accounts using a numeric probability.
- **Why it appeared plausible:** A single number is operationally convenient.
- **Evidence reviewed:** [Watchlist methodology](../solution/reports/watchlist-methodology.md) and [watchlist validation](../solution/reports/watchlist-validation.md).
- **Reason for rejection:** No predictive training, calibration, holdout evaluation, or prospective validation was performed.
- **Decision:** Use transparent deterministic review rules and evidence packets.
- **Residual uncertainty:** A future model could be evaluated under a separate governed protocol.

### RH-006 — Associated MRR could represent revenue at risk

- **Hypothesis or approach:** Convert associated MRR into an expected-loss measure.
- **Why it appeared plausible:** MRR provides useful commercial context.
- **Evidence reviewed:** [Revenue diagnostic](../solution/reports/revenue-diagnostic.md) and [watchlist validation](../solution/reports/watchlist-validation.md).
- **Reason for rejection:** Association at a cutoff does not prove loss, cause, recovery, or intervention impact.
- **Decision:** Retain deduplicated associated MRR as descriptive context only.
- **Residual uncertainty:** A separate finance-approved causal measurement design would be required.

### RH-007 — JourneyGraph should automatically recommend a customer action

- **Hypothesis or approach:** Convert each review item into an automatic recommendation.
- **Why it appeared plausible:** It shortens the path from evidence to operations.
- **Evidence reviewed:** [Intervention watchlist](../solution/reports/intervention-watchlist.md) and [experiment governance](../solution/reports/experiment-governance.md).
- **Reason for rejection:** Consent, policy, data quality, treatment eligibility, and experimental controls remain unresolved.
- **Decision:** Keep the system investigation-only with manual disposition.
- **Residual uncertainty:** Approved playbooks could be added only after governance and experimental evidence exist.

### RH-008 — All experiments could be marked ready

- **Hypothesis or approach:** Treat every specified design as ready for launch review.
- **Why it appeared plausible:** All eight entries contain hypotheses, metrics, and safeguards.
- **Evidence reviewed:** [Experiment registry](../solution/reports/experiment-registry.md), [experiment lab](../solution/reports/experiment-lab.md), and [experiment validation](../solution/reports/experiment-validation.md).
- **Reason for rejection:** Power, feasible units, and operating conditions differ materially.
- **Decision:** Classify one ready for review, one pilot only, four underpowered, and two not feasible; all remain `UNTESTED`.
- **Residual uncertainty:** Eligibility volume and operational constraints can change in future data.

### RH-009 — Cox regression should be the central survival model

- **Hypothesis or approach:** Center the survival phase on a proportional-hazards regression.
- **Why it appeared plausible:** Cox is a common multivariable time-to-event method.
- **Evidence reviewed:** [Survival assumptions](../solution/reports/survival-assumptions.md), [survival sensitivity](../solution/reports/survival-sensitivity.md), and [D050](decisions.md#d050--critérios-para-cox).
- **Reason for rejection:** STRICT had only 46 eligible events, endpoints were warning-sensitive, and proportional-hazards stability was not established.
- **Decision:** Do not execute Cox; retain descriptive survival estimates and sensitivity analysis.
- **Residual uncertainty:** A larger, cleaner prospective dataset could support a new model gate.

### RH-010 — Neo4j should be a mandatory runtime dependency

- **Hypothesis or approach:** Require a live Neo4j service for graph exploration.
- **Why it appeared plausible:** It offers graph-native storage and interactive querying.
- **Evidence reviewed:** [Graph methodology](../solution/reports/graph-methodology.md), [Neo4j guide](../solution/reports/neo4j-guide.md), and [architecture](../docs/architecture.md).
- **Reason for rejection:** Credentials and external infrastructure would weaken local reproducibility.
- **Decision:** Use NetworkX locally and keep Neo4j as an optional export.
- **Residual uncertainty:** An enterprise deployment may justify a managed graph database later.

### RH-011 — Runtime AI would improve the demo

- **Hypothesis or approach:** Generate explanations or actions dynamically during evaluation.
- **Why it appeared plausible:** Dynamic text can feel responsive and personalized.
- **Evidence reviewed:** [Dashboard data contract](../solution/reports/dashboard-data-contract.md), [dashboard validation](../solution/reports/dashboard-validation.md), and [architecture](../docs/architecture.md).
- **Reason for rejection:** Runtime generation adds credentials, cost, latency, variability, and a new claim-validation surface.
- **Decision:** Use fixed validated evidence and deterministic copy.
- **Residual uncertainty:** A separately evaluated enterprise layer could add bounded generation with traceable sources.

### RH-012 — Generic runtime translation would accelerate localization

- **Hypothesis or approach:** Translate UI text using word-level substitutions at render time.
- **Why it appeared plausible:** One mapping appears faster than editing complete messages.
- **Evidence reviewed:** [Localization validation](../solution/reports/localization-validation.md), [D110–D111](decisions.md#d110---tradução-controlada-por-mensagens-completas), and workflow error E074.
- **Reason for rejection:** It produced mixed-language and grammatically invalid phrases.
- **Decision:** Use complete reviewed messages and closed mappings for known values.
- **Residual uncertainty:** New copy still requires explicit localization review.

### RH-013 — Direct Python command was acceptable as the official Quick Start

- **Hypothesis or approach:** Document a platform-specific Python call as the main setup path.
- **Why it appeared plausible:** It bypassed the failing npm alias locally.
- **Evidence reviewed:** [Metric consistency matrix](../solution/reports/metric-consistency-matrix.md), [main README](../README.md), and workflow errors E084–E085.
- **Reason for rejection:** The evaluator workflow needed one tested command across Windows, Linux, and macOS.
- **Decision:** Make the Node wrapper-backed `npm run build:data` the official path.
- **Residual uncertainty:** Supported runtimes remain prerequisites.

## Limitations

These rejections do not prove that an approach is universally invalid. They document why it was unsuitable for this dataset, evidence quality, operating boundary, or evaluation goal. Reconsideration requires new evidence and a fresh human gate.
