# AI and Implementation Errors Corrected During JourneyGraph

## Attribution Policy

This register distinguishes source-data conditions, design risks, AI-assisted implementation errors, implementation oversights, documentation gaps, and repository-control events. It does not attribute every defect to the AI coding assistant. Each entry is limited to evidence preserved in reports, logs, commits, or reconstructed instruction summaries.

## Corrected Errors and Risks

### AEC-001 — Mega-join or row multiplication risk

- **Phase:** Dataset audit.
- **Initial output or suggestion:** A consolidated join was considered as a convenience path; this was a design risk, not a committed analytical result.
- **Why it was wrong or insufficient:** One-to-many chains expanded 500 accounts to 147,896 rows.
- **How it was detected:** Relationship cardinality simulation.
- **Human decision:** Prohibit the mega-table and preserve source grains.
- **Correction:** Build source-specific canonical events and reconcile every downstream grain.
- **Validation:** [Relationship audit](../solution/reports/relationship-audit.md) and [data contract](../docs/data-contract.md) record the 295.792× multiplier and prohibition.
- **Residual risk:** Future contributors can still create an unsafe ad hoc join outside the governed pipeline.

### AEC-002 — Invalid temporal records initially unsuitable for direct analysis

- **Phase:** Dataset audit and event log.
- **Initial output or suggestion:** Direct analysis of parseable timestamps would have treated syntax as lifecycle validity; the root condition came from source data.
- **Why it was wrong or insufficient:** Parseable records still occurred before account or subscription starts, after ends, or in contradictory order.
- **How it was detected:** Temporal predecessor and lifecycle checks.
- **Human decision:** Preserve fatal cases in quarantine instead of silently repairing them.
- **Correction:** Add explicit quality status, reasons, and an active/quarantine split.
- **Validation:** [Temporal audit](../solution/reports/temporal-audit.md), [quarantine report](../solution/reports/quarantine-report.md), and event-log tests.
- **Residual risk:** Upstream correction is required before quarantined rows can support behavior.

### AEC-003 — Overly broad interpretation of churn as a single final state

- **Phase:** Event log and churn diagnostics.
- **Initial output or suggestion:** A single account-level flag appeared sufficient; this was a modeling risk.
- **Why it was wrong or insufficient:** It erased repeated churn and explicit reactivation sequences.
- **How it was detected:** Counts of multiple churn events and reactivation flags by account.
- **Human decision:** Model ordered churn and reactivation events, then derive one executive classification without deleting episodes.
- **Correction:** Add recurrent sequences, previous/next links, and controlled outcome precedence.
- **Validation:** [Churn diagnostic](../solution/reports/churn-diagnostic.md), [event-log validation](../solution/reports/event-log-validation.md), and [D025–D026](decisions.md#d025--modelo-de-churn-recorrente).
- **Residual risk:** Executive summaries can still be overread if the episode-level evidence is ignored.

### AEC-004 — Unstable or unsupported journey patterns

- **Phase:** Journey mining.
- **Initial output or suggestion:** Frequency-first selection could admit patterns with weak support or MAIN/STRICT divergence; this was an analytical gate risk.
- **Why it was wrong or insufficient:** Frequency did not guarantee stability, adequate denominator, or safe same-day ordering.
- **How it was detected:** Population sensitivity, support, sample-size, exposure, and ordering checks.
- **Human decision:** Classify patterns as ROBUST, SENSITIVE, or UNSTABLE and exclude failed evidence from promotion.
- **Correction:** Add explicit promotion criteria and rejection counts.
- **Validation:** [Journey stability](../solution/reports/journey-stability.md) and [journey mining](../solution/reports/journey-mining.md).
- **Residual risk:** A promoted historical pattern remains descriptive and may not persist in new data.

### AEC-005 — Potential overstatement of graph evidence

- **Phase:** Graph construction and dashboard.
- **Initial output or suggestion:** A dense graph and centrality/path outputs could appear more authoritative than their evidence boundary; this was a communication and visualization risk.
- **Why it was wrong or insufficient:** Direction and structure do not establish customer-level cause or future outcome.
- **How it was detected:** Graph quality review and visual inspection; the first dashboard capture was also too dense (workflow E072).
- **Human decision:** Promote only gated evidence, label graph semantics as descriptive, and reduce the initial visible edge set.
- **Correction:** Add promotion metadata, bounded views, limitations, and a 16-relationship initial display.
- **Validation:** [Graph methodology](../solution/reports/graph-methodology.md), [graph validation](../solution/reports/graph-validation.md), and [dashboard validation](../solution/reports/dashboard-validation.md).
- **Residual risk:** Viewers may still infer importance from layout unless limitations remain visible.

### AEC-006 — Risk of presenting a deterministic watchlist as predictive scoring

- **Phase:** Intervention watchlist.
- **Initial output or suggestion:** A ranked list could be described with model-like language; this was a product-communication risk.
- **Why it was wrong or insufficient:** No predictive model, probability calibration, or prospective validation existed.
- **How it was detected:** Review of rule semantics, priority fields, and prohibited interpretations.
- **Human decision:** Keep discrete rule components separate and require reviewer disposition.
- **Correction:** Use versioned rules, evidence packets, confidence gates, and seven named review queues.
- **Validation:** [Watchlist methodology](../solution/reports/watchlist-methodology.md) and [watchlist validation](../solution/reports/watchlist-validation.md).
- **Residual risk:** Consumers can misuse queue order if they disregard the methodology.

### AEC-007 — Risk of treating associated MRR as revenue at risk

- **Phase:** Churn diagnostics and watchlist.
- **Initial output or suggestion:** MRR association could be framed as a financial-loss estimate; this was a claim-design risk.
- **Why it was wrong or insufficient:** The snapshot does not establish loss, attribution, recovery, or intervention effect.
- **How it was detected:** Grain and cutoff review plus financial-language checks.
- **Human decision:** Deduplicate at account/queue scope and label the value as associated context only.
- **Correction:** Add explicit limitations in reports, data contracts, and UI copy.
- **Validation:** [Revenue diagnostic](../solution/reports/revenue-diagnostic.md), [watchlist validation](../solution/reports/watchlist-validation.md), and [metric consistency matrix](../solution/reports/metric-consistency-matrix.md).
- **Residual risk:** The label requires continued governance in derivative presentations.

### AEC-008 — Experiment designs initially at risk of sounding like completed evidence

- **Phase:** Experiment Lab.
- **Initial output or suggestion:** Design readiness language could be read as effectiveness evidence; this was a documentation risk.
- **Why it was wrong or insufficient:** No intervention or outcome measurement occurred.
- **How it was detected:** Registry, assignment, uplift, and execution-state validation.
- **Human decision:** Keep every causal status `UNTESTED` and separate feasibility from approval.
- **Correction:** Classify one ready for review, one pilot only, four underpowered, and two not feasible.
- **Validation:** [Experiment registry](../solution/reports/experiment-registry.md), [experiment validation](../solution/reports/experiment-validation.md), and [experiment governance](../solution/reports/experiment-governance.md).
- **Residual risk:** Readers can still confuse planning maturity with measured impact if status definitions are omitted.

### AEC-009 — Partial localization created bilingual UI

- **Phase:** Localization rework.
- **Initial output or suggestion:** Partial route and component translation left English copy visible; this was an implementation oversight recorded as E075.
- **Why it was wrong or insufficient:** The user experience was inconsistent and did not meet the pt-BR product requirement.
- **How it was detected:** Route-by-route copy audit and browser review.
- **Human decision:** Localize all visible routes, shared surfaces, metadata, states, and accessibility labels.
- **Correction:** Replace remaining copy with reviewed pt-BR messages.
- **Validation:** [Localization validation](../solution/reports/localization-validation.md), 18 Vitest checks, 36 Playwright checks, and commit `de4ca14c66d33319af15aae492d04caadb910ff1`.
- **Residual risk:** Future UI copy requires the same controlled review.

### AEC-010 — Generic lexical translation produced invalid phrases

- **Phase:** Localization rework.
- **Initial output or suggestion:** AI-assisted implementation used word-level substitutions, recorded as E074.
- **Why it was wrong or insufficient:** Partial replacement produced grammatically invalid or mixed-language phrases.
- **How it was detected:** Human reading of rendered text and targeted tests.
- **Human decision:** Remove generic lexical translation.
- **Correction:** Use complete messages and closed maps for known enums/statuses; preserve unknown values intact.
- **Validation:** [Localization validation](../solution/reports/localization-validation.md), [D110–D111](decisions.md#d110---tradução-controlada-por-mensagens-completas), and commit `de4ca14c66d33319af15aae492d04caadb910ff1`.
- **Residual risk:** A newly introduced enum needs an explicit mapping.

### AEC-011 — Tests were not initially aligned with pt-BR labels

- **Phase:** Localization rework.
- **Initial output or suggestion:** Six expectations retained English-era assumptions after the copy changed; this was an implementation oversight recorded as E076.
- **Why it was wrong or insufficient:** Tests failed for stale text and ambiguous selectors rather than product behavior.
- **How it was detected:** Vitest and Playwright failures.
- **Human decision:** Rewrite assertions around controlled pt-BR semantics, privacy, accessibility, and exact states.
- **Correction:** Update focused unit and browser expectations without weakening guardrails.
- **Validation:** [Localization validation](../solution/reports/localization-validation.md) records 18/18 Vitest and 36/36 Playwright checks.
- **Residual risk:** Brittle copy assertions can recur if messages are changed without contract review.

### AEC-012 — Demo exposed internal account identifiers visually

- **Phase:** Localization and anonymization rework.
- **Initial output or suggestion:** Internal `account_key` and pattern keys were rendered for traceability; this was an implementation oversight recorded as E083.
- **Why it was wrong or insufficient:** Internal analytical identifiers had no evaluator-facing purpose and increased exposure risk.
- **How it was detected:** Visual review of the real build.
- **Human decision:** Retain keys only for internal joins and display controlled anonymous aliases.
- **Correction:** Replace visible keys and remove arbitrary truncation.
- **Validation:** [Localization validation](../solution/reports/localization-validation.md), [dashboard validation](../solution/reports/dashboard-validation.md), and commit `de4ca14c66d33319af15aae492d04caadb910ff1`.
- **Residual risk:** New components must continue to prevent key rendering.

### AEC-013 — `npm run build:data` failed on Windows

- **Phase:** Cross-platform hardening.
- **Initial output or suggestion:** A package alias mixed a POSIX relative executable path with a hardcoded Windows virtual-environment layout; this was an AI-assisted implementation error recorded as E084.
- **Why it was wrong or insufficient:** The default npm shell on Windows returned exit code 1.
- **How it was detected:** The documented Quick Start was executed exactly from the evaluator path.
- **Human decision:** Replace the shell-specific alias with a dependency-free Node wrapper.
- **Correction:** Resolve paths from `import.meta.url`, select controlled Python candidates, use `shell: false`, and propagate the exit code.
- **Validation:** [Metric consistency matrix](../solution/reports/metric-consistency-matrix.md), focused Vitest coverage, deterministic rebuilds, and commit `8f785e25d3652068a356f213fc6f596d76f8b266`.
- **Residual risk:** Machines still need a supported Node.js and Python 3 installation.

### AEC-014 — Quick Start initially depended on a manual Python workaround

- **Phase:** Submission documentation and cross-platform hardening.
- **Initial output or suggestion:** Documentation temporarily instructed evaluators to call Python directly; this was a documentation workaround recorded as E085.
- **Why it was wrong or insufficient:** It diverged from the product's official npm workflow and exposed platform-specific paths.
- **How it was detected:** Documentation-to-execution audit.
- **Human decision:** Restore one tested npm command as the primary path.
- **Correction:** Update both Quick Starts after the wrapper passed.
- **Validation:** [Main README](../README.md), [app README](../solution/app/README.md), [documentation validator](../solution/scripts/validate_documentation.py), and commit `bffa9a29b3b471f876d02e5fb784fc2bb5fa7c4d`.
- **Residual risk:** Setup can still fail when required runtimes are missing; troubleshooting is explicit.

### AEC-015 — Dirty working tree blocked finalization

- **Phase:** Recovery gate before final documentation.
- **Initial output or suggestion:** Finalization could not proceed while unrelated or accidental local changes were unresolved; this was a repository-state control event, not attributed to AI.
- **Why it was wrong or insufficient:** An unclean scope would make commit provenance and validation ambiguous.
- **How it was detected:** Git precondition checks at the recovery boundary.
- **Human decision:** Stop, audit the local changes, restore the authorized baseline, and resume only from a clean state.
- **Correction:** The subsequent Phase 10A record begins from the reviewed documentation-only scope; no transient diff was committed.
- **Validation:** [Prompts log](prompts.md#recovery-gate-before-phase-10a) identifies this as a `reconstructed instruction summary`; [workflow](workflow.md) records the clean Phase 10A boundary and commits `8f785e25d3652068a356f213fc6f596d76f8b266` and `bffa9a29b3b471f876d02e5fb784fc2bb5fa7c4d` preserve the accepted state.
- **Residual risk:** The exact transient filenames and diff are not preserved in Git, so no stronger attribution is made.

### AEC-016 — Screenshot regeneration risk during a read-only audit

- **Phase:** Dashboard evidence recovery and localization.
- **Initial output or suggestion:** Running the screenshot capture path during inspection could rewrite approved PNG evidence; this was an operational risk, not a recorded overwritten final artifact.
- **Why it was wrong or insufficient:** A read-only audit must not mutate the evidence it is evaluating.
- **How it was detected:** Review of the smoke/capture workflow and the earlier need to replace obsolete screenshots (E078).
- **Human decision:** Separate inspection from capture and regenerate only after code gates passed.
- **Correction:** D113 requires green lint, typecheck, Vitest, and build before recapture, followed by visual review.
- **Validation:** [Localization validation](../solution/reports/localization-validation.md), [dashboard validation](../solution/reports/dashboard-validation.md), and [D113](decisions.md#d113---screenshots-regenerados-após-localização-completa).
- **Residual risk:** Future smoke commands that include capture remain write-producing and must be identified before a read-only review.

## Limitations

The register includes both corrected defects and risks rejected before they became accepted outputs. Transient terminal state is weaker evidence than a committed report; AEC-015 and AEC-016 therefore state their evidentiary limits explicitly. No item establishes intent, and no source-data defect is assigned to the AI coding assistant.
