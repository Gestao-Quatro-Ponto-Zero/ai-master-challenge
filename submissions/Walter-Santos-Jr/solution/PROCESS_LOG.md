# Process log — AI-assisted implementation

## Business framing (human-directed)
- User supplied G4 README and Head of RevOps problem statement: subjective prioritization and sales capacity wasted on low-potential deals.
- Defined primary outcome as **revenue per sales capacity**, not AUC or score distribution.
- Decided to provide working seller-facing software with explanations and next actions.

## Data diagnosis (AI-assisted, human review required)
- Inspected 8,800 CRM records and joined accounts, products and teams.
- Found 2,089 open opportunities; 1,425 have no account; 500 Prospecting deals have no engagement date.
- Identified `GTXPro` product alias and normalized it.
- Explored historical models; weak discriminative results led to rejecting a probability claim.

## Policy choice (AI-assisted, explicit assumptions)
- V2 heuristic: stage 40%, product 35%, account scale 25%; missing account neutral.
- Detected stage bias: all high-priority cases are Engaging in this dataset.
- Retained stage filters and separate data-confidence signal; did not optimize weights to fabricate predictive lift.
- Marked policy experimental and provided contribution-level explanations.

## Implementation (AI-generated code, testable artifact)
- Python standard-library HTTP/JSON backend, static HTML/CSS/JS and SQLite storage.
- Endpoints: `/api/health`, `/api/dashboard`, `/api/opportunities/{id}` and POST qualification/activity routes.
- Client-side user interactions trigger server-side persistence and dashboard refresh.
- HTML escaping for user data, payload validation and parameterized SQL; localhost-only binding.
- Chose no dependency web stack to maximize reproducibility in the evaluation environment; no need to install Dash or Streamlit.

## Validation and remaining human tasks
- Automated unittest suite verifies counts, filters, explanation arithmetic, persistence and invalid inputs.
- HTTP smoke test verifies API response and POST persistence.
- Human evaluator should perform browser UX acceptance tests, assess business plausibility of policy weights and verify against their own environment.
- This artifact is a working prototype, not a production-ready multiuser CRM.

## Human vs AI responsibility
- **Human:** business objective, acceptance criteria, strategic constraints, selection and approval of final policy, submission.
- **AI:** draft implementation, tests, documentation, evidence synthesis, proposed tradeoffs.
- **Human approval still required:** policy sign-off, interface usability and final pull request.

## V3 additive scoring engine — 2026-10-22

- Preserved V1 files and V2 ranking baseline; introduced `scoring_v3.py` as versioned decision-support assessment.
- Added separate qualification readiness, confidence, risk flags, next action and triage hints.
- Explicitly excluded current-clock stagnation based on historical CRM dates and unvalidated sector bonuses.
- Added tests for evidence handling, score stability, blockers, missing accounts, band boundaries and temporal integrity.
- See `SCORING_POLICY_V3.md` for design limitations and next steps.

## V3.1 — Execution Queue
- Additive SQLite migration: `opportunity_jobs` and `job_events`, preserving V1 qualification/activity history.
- Deterministic and idempotent job creation for missing account, explicit qualification blocker, incomplete qualification.
- State transition validation; `RESOLVED` is not `VERIFIED`. Verification requires persisted structured evidence; history retained; reopens on recurrence.
- Seller-filtered card queue and opportunity-level jobs; API `/api/jobs`, `POST /api/jobs/{id}`.
- Historical timestamps are never used to invent today's urgency. Baseline scoring weights unchanged.
- 19 automated tests pass. UI browser acceptance remains for the user to validate.


## V3.2 — UX & Workflow Stabilization
- Job cards display stable Job ID and Deal ID, with distinct status styling and larger spacing.
- START/RESOLVE updates only the selected card in place; no automatic reordering.
- Explicit Refresh / Reorder action, plus success/error feedback.
- Commercial and data-quality job filters; all jobs accessible.
- Scoring and backend transition semantics unchanged.


## V4.0 — Visual Identity / AppShell
Refatoração aditiva de layout, sem alterações no backend ou scoring.

## V4.0.1 — Layout Geometry Refinement
- Enlarged left Navbar and right Aside on desktop, reduced outer margins and inter-panel gaps.
- Main fills the center grid track, with symmetrical placement between the two side panels.
- Aside now occupies available viewport height and scrolls internally; no longer resembles a short card.
- Kept Dark/Light styling and all backend, scoring, jobs, and JS logic unchanged.

## V4.0.2 — Scoring policy contrast fix
- Corrigido contraste de textos e botão fechar no painel "Como calculamos o score" em Dark/Light.
- CSS restrito a `#policyOverlay`; sem alterações em JavaScript, APIs, scoring ou Closed-Loop.

### V4.2 — Decision & Execution Experience
- Movido o detalhe do deal para o Main com abas Inteligência, Qualificação, Execução e Histórico.
- Preservadas APIs, SQLite, scoring e verificação de jobs.
- Abertura de deal não inicia job; transições continuam explícitas.
- 21 testes automatizados aprovados e JavaScript verificado com `node --check`.
- Pendente: teste visual em navegador e posterior substituição da tabela por cards, além de reordenação automática contextual.


### V4.3
Substituição da tabela por cards e atualização contextual, sem alterações nas regras de scoring e verificação.
