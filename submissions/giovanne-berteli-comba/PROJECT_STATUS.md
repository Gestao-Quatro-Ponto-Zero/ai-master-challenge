# Project status

Updated: 2026-11-02 (America/Sao_Paulo).

- Selected challenge: **002 — Support redesign** (explicit user decision).
- Current phase: V00 completed before fitting. See [evaluation protocol/setup](docs/evaluation-protocol.md)
  and [authoritative rules](knowledge/evaluation-protocol.md). Prototype implementation is next.
- Submission slug: inherited from the existing Git branch. Display name and
  LinkedIn still require confirmation before final submission.
- Completed: shared instructions, minimal OKF bundle, execution checklist,
  validation strategy, process-log policy and conversation snapshots; adversarial
  foundation review, reproducible consistency checks, input-hash invalidation and
  regression probes. See [controls and scope](docs/foundation-controls.md).
- Data evidence: official version-1 archives acquired, hashes frozen, both schemas
  and quality audited, and audit reproduced from a clean directory. See
  [D01 report](docs/data-audit.md) and [setup](data/README.md).
- Not performed: prototype implementation,
  model training/evaluation, deployment, or PR.
- Dataset-use decision: customer support for descriptive diagnosis; IT service
  for an in-domain classification benchmark. No row join or taxonomy mapping.
- Next action: I01 — implement the S01 triage/review contract and frozen V00
  training/validation selection. Use train examples only in development/UI; reserve
  final-test prediction/performance for V01 after artifact/configuration freeze.
- V00 evidence: train 33,485 / validation 7,177 / final test 7,175; whole near-text
  groups, no quarantine; locked isolated environment imports/checks and 37 software
  tests passed. No classifier fitted or AI quality measured.
- Selected design: local assisted IT category triage with mandatory confirmation,
  failure handoff and persisted/filterable high/low anomalies. No external actions.
- Selected stack: Python 3.12, scikit-learn, Streamlit, SQLite. Exact tested
  dependency versions and numerical selection/acceptance rules are frozen in V00;
  targets are design criteria, not achieved quality or approved business costs.
- The [official review table](docs/architecture-review.md#lista-oficial-para-validação)
  is the sole record of F01–F07 review decisions and adjustment state. Current
  working context comes from instructions, this handoff, the plan and relevant
  knowledge; process logs and chat archives serve recruitment evidence only.

Start with the [execution plan](execution/plan.md), then follow the
[knowledge index](knowledge/index.md). No conversation-archive reading is needed
to resume execution.
