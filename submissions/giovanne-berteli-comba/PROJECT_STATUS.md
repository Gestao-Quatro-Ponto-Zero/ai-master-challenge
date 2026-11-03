# Project status

Updated: 2026-11-03 (America/Sao_Paulo).

- Selected challenge: **002 — Support redesign** (explicit user decision).
- Current phase: R02 pre-submission investigation completed at the user's request.
  See the [five-principle review](docs/pre-submission-review.md) and prioritized
  [backlog](execution/backlog.md). E01 packaging remains available in the
  [reviewer guide](docs/review-guide.md). P01 has not started.
- Submission slug: inherited from the existing Git branch. Display name and
  LinkedIn still require confirmation before final submission.
- Completed: shared instructions, minimal OKF bundle, execution checklist,
  validation strategy, process-log policy and conversation snapshots; adversarial
  foundation review, reproducible consistency checks, input-hash invalidation and
  regression probes. See [controls and scope](docs/foundation-controls.md).
- Data evidence: official version-1 archives acquired, hashes frozen, both schemas
  and quality audited, and audit reproduced from a clean directory. See
  [D01 report](docs/data-audit.md) and [setup](data/README.md).
- Not performed: actual human anomaly adjudication, measured operational savings,
  production/domain-transfer validation, deployment or PR. Offline final-test
  criteria passed; this is not business approval or production readiness.
- Dataset-use decision: customer support for descriptive diagnosis; IT service
  for an in-domain classification benchmark. No row join or taxonomy mapping.
- Next action: use R02's recommendation to select a bounded improvement pass before
  P01: executive entry/demo, a read-only management/results view, and setup/status
  clarity. These are proposals; no new product features were implemented in R02.
  P01 still requires candidate identity, final review and PR preparation. Nothing
  is submitted/published yet.
- R02 verification: prepared setup succeeded in 0.288 s on this host with 23
  data/model hashes and mtimes unchanged; saved 7,175-case outputs reconciled with
  zero model loads, new predictions or fits. Cold setup/platform limits and the
  obsolete reserved-test console message are documented in the review. No browser
  visual inspection or new operational savings measurement was performed.
- E01: template narrative and evidence/decision map; 11 passive source-anchored tour
  steps and one-command review workspace; current inventory: 22 captures / 162 message occurrences / 120
  distinct explicit IDs. 42 legacy no-ID occurrences and platform/cutoff omissions
  remain disclosed. No new test inference, model fitting or frozen source changes.
- CodeTour correction: `bash review.sh` opens the correct VS Code workspace, reuses/
  installs the official extension and offers the tour. Actual isolated extension
  hosts reproduced root discovery failure and verified all 11 editor anchors in the
  review workspace. 74 software tests passed; user review window opened successfully.
- V01: 7,175 final-test cases; macro F1 0.844612 vs text baseline 0.646094;
  standard coverage 27.19%, agreement 96.57% (1,884/1,951; 67 errors). 50 errors
  have specialist-policy true labels: mandatory confirmation remains essential.
  All six numerical targets passed, plus persistence/runtime parity/fault checks.
- Final-test exposure is consumed. No new model/gate/reference was chosen or fitted.
  UI/demo examples remain train-only; later choices informed by this test need
  disclosed exploratory status or new evaluation data.
- Actual sequential runtime sample: 64/64 stored, no failed outcomes, p95≈600.84 ms
  including commit on this host. Small sample, not SLA; raw external-clock samples
  were not persisted. 72 software tests passed before freeze/prediction.
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
