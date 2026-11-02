---
type: Decision Record
title: Complementary dataset roles and evaluation boundaries
description: D02 decision on diagnosis, classification, label conflicts and permissible claims.
status: draft
generated:
  by: codex
  at: 2026-11-02T18:19:03Z
sources:
  - id: audit
    resource: ../data/audit.json
  - id: measurement-boundaries
    resource: data-quality.md
  - id: evaluation-policy
    resource: ../docs/validation-strategy.md
---

# Decision and authority

D02 is executed as an agent implementation decision under the user's instruction
to advance the project. It is not a new human approval or a model-quality result.
This record owns dataset roles and their measurement/evaluation boundaries.
It supersedes the pending dataset-use choice in challenge context and status;
the D01 audit remains the evidence for the input limitations.

Use the datasets as complementary evidence for assisted triage, with separate
populations and taxonomies. Do not join their rows, pool their labels, or infer
that an IT benchmark demonstrates performance in the customer-support operation.
Application stack, final automation contract and quality targets remain for S01/V00.

# Roles and data contracts

| Dataset | Selected role | Inputs and allowed outputs | Exclusions |
| --- | --- | --- | --- |
| Customer support, 8,469 rows | A01 descriptive operational diagnosis and explicitly assumed effort scenarios | Original channel, priority, type and status; satisfaction within its observed population; volume/mix, nonclosed share and rated-closed comparisons | No supervised target for the first prototype; no full-duration/SLA/active-effort claims; no trusted answer generation from Resolution |
| IT service, 47,837 rows | In-domain offline classification benchmark supporting an assisted-triage prototype | Document as the only model feature; Topic_group as the eight-class target; category suggestion and later human-review handling | No status, priority, satisfaction or elapsed-time outcomes available; no claim of production routing correctness or customer-domain accuracy |

The operational diagnosis keeps all raw records, including duplicate descriptions
and conflicting labels. Counts describe recorded tickets, not independent people
or unique problems. Expose quality flags when interpreting ticket-type groups.
Names, emails, customer age/gender and purchase date are not necessary model inputs
or diagnostic segmentation in this scope. Keep raw data local and unchanged.

IT text is already provided in a processed field. The source does not establish
that every word was available when a ticket arrived; Document-only features do
not prove prospective entry-time validity. V00 must state this limitation and
inspect for outcome-like content before implementation. Do not infer production
entry-time performance from a retrospective benchmark.

# Mapping and rejected alternatives

There is no supported common entity key, shared cohort, time alignment or label
correspondence. The five customer Ticket Type labels and eight IT Topic_group
labels answer different questions. No mapping is approved by this decision.

- Reject concatenating the files into a shared supervised task: distinct labels,
  populations and available fields would make pooled accuracy uninterpretable.
- Reject mapping categories by similar names or asking a model to invent ground
  truth: no adjudicated correspondence exists.
- Reject treating customer Resolution as a reliable response library: D01 found
  short unvalidated content; semantic usefulness has not been established.
- Reject silently repairing chronology, inferring ticket opening from purchase,
  or dropping inconsistent pairs to present an apparently valid latency ranking.

These choices use both datasets in the proposal: one establishes operational
questions, populations and data gaps; the other tests the classification mechanism
in its own domain. A future operational pilot must supply representative labels,
entry-time inputs and routing owners before deployment claims.

# Label conflicts and evaluation boundaries (F02)

Customer descriptions have 54 repeated normalized-text groups, 49 with conflicting
Ticket Type labels (446 rows). Preserve their source labels and flag the conflict;
do not majority-relabel, discard the whole operational population, or train the
IT classifier on them. No customer-label accuracy/F1 will be reported for this
prototype. Any future supervised customer task requires a separate adjudication
protocol and versioned labels before inclusion.

For IT, V00 must freeze development/validation/final-test membership before
choosing model, prompt or thresholds. Group normalized duplicates using D01's
NFKC/casefold/whitespace rule; inspect near-duplicate/template risk before freezing
membership. The audited absence of exact/normalized duplicates does not prove
entity independence. Record unavailable entity identifiers as a limitation.

The planned classification baseline is a majority-class predictor fitted only on
training data, followed by a simple text baseline. Report macro F1 across the
eight classes, per-class precision/recall/F1/support, confusion and overall accuracy
as a secondary measure. V00 owns exact splits, candidate definitions, acceptance
criteria and selection rules; none has been executed here. Fit vocabulary and any
learned preprocessing on training data only. Use validation for model/threshold
selection; evaluate the selected version on the reserved final test.

Report errors among assisted cases together with assisted coverage, human-review
volume and technical failures. A model score is not automatically a probability.
Keep numerical rarity, uncertainty and failure distinct; S01/V00 define the
anomaly references, actions and thresholds before I01.

If customer descriptions are later passed through the IT prototype, record a
separate, unlabeled domain-shift probe: no borrowed Ticket Type targets, no pooled
metrics, and no accuracy/F1 or out-of-domain detection recall. Some topics may
overlap; membership in the other dataset is not ground truth that every ticket
is outside the taxonomy. Select any probe sample before inspecting model outputs
and state its exposure separately. This probe is optional, not required for D02.

# Operational metric contract (F07)

A01 must publish numerators, denominators, missingness and the exact group filters
for every comparison. Use channel, priority, type and their combinations only as
recorded categories. Small/empty groups retain their support and unavailable values;
do not replace missing scores with zero or claim that sparse rankings are stable.

| Measure | Numerator / denominator or population | Permitted interpretation |
| --- | --- | --- |
| Volume and mix | Group ticket rows / all rows in the stated filtered population | Recorded composition; no annual/monthly throughput without a known observation period |
| Nonclosed share | Open + Pending Customer Response / all tickets in the same group | Snapshot of nonclosed records; not age, arrival rate or proof of a bottleneck |
| Closed share | Closed / all tickets in the same group | Snapshot composition; not an operational closure rate over time |
| Satisfaction coverage | Valid rated rows / all group rows; also report valid rated closed rows / closed group rows | Visibility of the closed-only score population; no inference for unrated tickets |
| Satisfaction distribution and mean | Counts per score and sum of valid 1–5 scores / valid rated closed rows in that group | Descriptive association; keep distribution/support beside the mean, with no causal claim |
| Low satisfaction share | Closed scores 1 or 2 / valid rated closed rows in the same group | Explicit descriptive convention, not a supplied business SLA or causal risk model |
| Time-quality diagnostics | Negative pairs / all valid response-resolution pairs; nonnegative interval summaries separately labeled | Data-quality appendix only; no full-resolution or first-response latency ranking |

The briefing's 30,000 tickets/year is scenario context, not the observed annual
coverage of this 8,469-row file. A01 may use it only as a named hypothetical volume,
separate from file counts. Do not annualize the file or infer a year from purchase dates.

Hours/cost estimates must be scenarios with explicit volume/period, eligibility,
assisted coverage, manual and assisted active minutes, incremental review/rework,
fixed overhead and optional hourly cost. Keep negative net savings visible; avoid
double-counting review already included in assisted minutes. Do not substitute
IT benchmark coverage/error rates for customer-operation parameters. Measured
savings require a representative operational pilot with active-effort measurements.

# Completion and handoff

D02 completes the roles, mapping decision, label-conflict policy and evaluation/
metric boundaries. It does not complete A01, S01, V00 or I01. Implementation and
numerical acceptance targets remain pending; no split or model has been created.

R01 is complete; see the [bounded PR research](../docs/pr-review.md). A01 is next.
Research can inform differentiation but cannot override these data limitations
or replace validation. Published metrics from other tasks are not our targets.
