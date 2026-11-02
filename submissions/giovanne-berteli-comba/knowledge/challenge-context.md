---
type: Challenge Context
title: Support redesign requirements and decisions
description: Requirements, confirmed choices, and unresolved questions for Challenge 002.
status: draft
challenge_id: "002"
generated:
  by: codex/gpt-6.1-sol
  at: 2026-11-02T16:52:06Z
sources:
  - id: brief
    resource: https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/blob/main/challenges/process-002-support/README.md
  - id: submission-rules
    resource: https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/blob/main/CONTRIBUTING.md
  - id: user-decisions
    resource: ../process-log/chat-exports/03-planning-chat.md
  - id: review-decisions
    resource: ../docs/architecture-review.md
---

# Requirements

The brief requires an operational diagnosis, an AI automation proposal drawing
on both datasets, and a process log. The prototype is listed as a differential;
we intend to include one to demonstrate the proposed automation.[^brief]

| Deliverable | Required evidence |
| --- | --- |
| Bottlenecks | Quantified comparisons by channel, priority, ticket type, and relevant combinations |
| Satisfaction | Associations and limitations; causal language only if justified |
| Recoverable waste | Hours with explicit assumptions; cost scenarios if defensible |
| Automation proposal | What to automate, human exceptions, and the proposed flow |
| Functional prototype | Real data, reproducible setup, useful output, measured limitations |
| Process log | AI tools, iterations, corrections, human decisions, and evidence |

The final PR must contain changes only inside this candidate's submission
directory and follow the repository's PR naming convention.[^submission-rules]

# Confirmed project decisions

- The user selected Challenge 002 after discussing alternatives and PR counts.
- Build the foundation now; decide dataset usage after auditing the files.
- Keep execution tasks in Markdown with evidence-backed checkboxes.
- Use English for implementation/internal technical documentation and Git;
  Portuguese for reviewer-facing narrative. Preserve original conversation text.
- Preserve accessible project conversations alongside a concise process narrative.
- Include meaningful unit and integration tests when implementation begins.
- Build the CodeTour after the code stabilizes. Consider dashboards and a
  component gallery only when they support a concrete need.[^user-decisions]
- F03 includes recording and filtering possible high and low anomalies against
  comparable references. Rare values are not automatically errors; numerical
  limits and resulting actions depend on the data audit and evaluation protocol.
- F06 designates the process log and chat exports as recruitment evidence,
  excluded from default operational context. Preserve current decisions here or
  in their authoritative document rather than requiring archive retrieval.
- Review decisions and adjustment state remain exclusively in the official
  F01–F07 table; approval does not imply technical validation.[^review-decisions]

# Audited data boundaries

D01 is recorded in [dataset quality](data-quality.md), with source manifests,
reproducible aggregate output and the reviewer-facing report. The acquired files
contain 8,469 customer-support rows and 47,837 IT-classification rows. Temporal
fields are timestamps without ticket creation time, and many response/resolution
pairs have inconsistent chronology. Do not treat them as full service durations.
Dataset usage and application architecture remain undecided.

# Open questions

- Original operational provenance and semantic trustworthiness of text/labels
  beyond the audited files and publisher-declared licensing.
- How to use the operational and IT-classification datasets together.
- Validity of any join, taxonomy mapping, or transfer across their domains.
- Automation choice, application stack, evaluation split, and quality targets.
- Operational assumptions needed to estimate saved effort and cost.

# Analytical constraints

Treat advertised dataset properties as unverified until audited. The brief
does not establish a common entity key between the datasets. Elapsed resolution
time may include waiting and cannot alone establish active work saved. Prevent
duplicate leakage and avoid using post-resolution information as triage input.

[^brief]: Challenge 002 brief.
[^submission-rules]: Repository contribution rules.
[^user-decisions]: Planning conversation snapshot; user decisions take precedence over earlier assistant suggestions.
[^review-decisions]: Official architecture review decisions and user additions to F03/F06.
