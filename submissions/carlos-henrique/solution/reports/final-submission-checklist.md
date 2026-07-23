# JourneyGraph Final Submission Checklist

This checklist separates validated repository work from actions that require the submission owner. A category receives PASS only when every internal item in that row is complete.

| Category | Check | Evidence | Status |
|---|---|---|---|
| Repository | Correct branch, scoped changes, no raw CSV or build artifact tracked | Git scope gate | PASS |
| Documentation | README, architecture, application guide, index, and final package linked | Documentation validator | PASS |
| Application | Local pt-BR evaluator routes build and render from fixed JSON | Build and Playwright gates | PASS |
| Data | Five source files remain immutable and unversioned; 15 snapshot files reconcile | Data contract and deterministic rebuild | PASS |
| Analytics | Canonical event, journey, survival, and diagnostic evidence remains unchanged | Metric matrix and hash comparison | PASS |
| Graph | Promoted patterns and transitions retain support, stability, and provenance | Graph validation | PASS |
| Review Queue | Seven deterministic queues remain investigation-only | Watchlist validation | PASS |
| Experiments | Eight designs retain `UNTESTED` status and readiness classifications | Experiment validation | PASS |
| Governance | Cutoff, quarantine, association limits, and action boundaries are explicit | Governance route and reports | PASS |
| Human Judgment | Candidate decisions, rejected paths, and interventions are documented | Human-judgment evidence | PASS |
| AI Trace | Assistance, corrections, verification, and human acceptance are auditable | AI trace and correction register | PASS |
| Testing | Primary Python 130/130; clean-room Python 128 plus two raw-source gates; Vitest 19/19; Playwright 36/36; build, lint, and typecheck | Technical and clean-room gates | PASS |
| Security | Next.js `16.2.11` and `sharp 0.35.3` are lockfile-controlled; production audit reports zero vulnerabilities; no credentials are required | Production audit and runtime contract | PASS |
| Privacy | Evaluator-facing account identities are anonymous and no PII is displayed | Privacy validation | PASS |
| Video | Script, storyboard, plan, draft subtitles, title, description, and thumbnail specification exist; recording and upload remain external | Video asset inventory | PENDING_USER_ACTION |
| Deployment | Readiness and runbook are complete; platform deployment and public validation remain external | Deployment readiness | PENDING_USER_ACTION |
| Pull Request | PR description is ready; creation, review, and merge remain external | PR draft | PENDING_USER_ACTION |
| Submission Form | Form copy is ready; final URLs, completion, and submission remain external | Form draft | PENDING_USER_ACTION |
| External Links | Repository remote is verified; public demo, video, PR, form confirmation, and optional LinkedIn values remain external | Link registry | PENDING_USER_ACTION |
| Final Review | Clean-room, adversarial, five-minute, consistency, and final technical reviews pass | Final review reports | PASS |

## Publication Boundary

No recording, deployment, upload, push, Pull Request, form completion, platform submission, or social publication has been performed. Those items remain under explicit user control.
