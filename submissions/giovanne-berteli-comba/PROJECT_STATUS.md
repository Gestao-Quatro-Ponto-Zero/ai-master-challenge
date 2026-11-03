# Project status

Updated: 2026-11-02 (America/Sao_Paulo).

- Selected challenge: **002 — Support redesign** (explicit user decision).
- Current phase: I01 local prototype completed. See [setup and development results](docs/prototype.md)
  and [implementation handoff](knowledge/prototype.md). V01 final evaluation is next.
- Submission slug: inherited from the existing Git branch. Display name and
  LinkedIn still require confirmation before final submission.
- Completed: shared instructions, minimal OKF bundle, execution checklist,
  validation strategy, process-log policy and conversation snapshots; adversarial
  foundation review, reproducible consistency checks, input-hash invalidation and
  regression probes. See [controls and scope](docs/foundation-controls.md).
- Data evidence: official version-1 archives acquired, hashes frozen, both schemas
  and quality audited, and audit reproduced from a clean directory. See
  [D01 report](docs/data-audit.md) and [setup](data/README.md).
- Not performed: final-test prediction/evaluation, human adjudication of anomalies,
  measured operational savings, deployment, or PR. Prototype and train/validation
  selection are implemented; development metrics are not final-test evidence.
- Dataset-use decision: customer support for descriptive diagnosis; IT service
  for an in-domain classification benchmark. No row join or taxonomy mapping.
- Next action: V01 — freeze the evaluation driver/software and assess the selected
  model/gate/reference on reserved final_test, reporting all eight classes, errors
  with coverage/workload, failures and end-to-end latency. No further selection or
  refit from final-test results. UI/demo examples remain train-only.
- I01 selection: logistic C=2, validation macro F1 0.852554; threshold 0.80, tail 0.01.
  All four fits completed, no validation refit. Seven unique functional-smoke
  requests persisted atomically; original values and append-only reviews survive
  reload. These development checks do not establish final-test/production quality.
- Setup correction: `bash run.sh` prepares/opens the local app, supplies managed
  Python without system venv/ensurepip when needed, and reuses verified completed
  training. Clean install plus offline repeat tested; no new original-workspace fits.
- I01 software evidence: 64 tests passed in the locked environment, including both
  AppTest flows and real train-only inference. No skipped tests or additional fits.
- V00 evidence: train 33,485 / validation 7,177 / final test 7,175; whole near-text
  groups, no quarantine; locked isolated environment imports/checks and 37 software
  tests passed at V00. I01 separately trained/selected using train/validation only.
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
