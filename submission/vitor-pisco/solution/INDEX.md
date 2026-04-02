# AGENT CONTEXT INDEX — Pipeline Coach AI

## PURPOSE
This directory contains machine-optimized context files for AI agents working on the Pipeline Coach AI product. All files are structured for fast, unambiguous consumption. No prose padding.

## FILE MANIFEST

| File | Content | Tokens (est.) | Load When |
|------|---------|--------------|-----------|
| `INDEX.md` | This file. Navigation map. | ~300 | Always |
| `PRODUCT_SPEC.md` | Full PRD: objectives, users, features, KPIs | ~900 | Building features, writing specs |
| `USER_JOURNEYS.md` | All user flows with decision trees | ~700 | UX work, flow design, onboarding |
| `SCORING_ENGINE.md` | AI scoring formula, weights, logic | ~500 | Backend work, ML, scoring changes |
| `UX_RISKS.md` | 7 adoption risks with severity + mitigations | ~600 | Design review, UX audit, QA |
| `DASHBOARD_SPEC.md` | All dashboard blocks, hierarchy, filters | ~700 | Frontend work, dashboard builds |
| `DATA_SCHEMA.md` | CRM data model, fields, relationships | ~800 | DB work, API design, integrations |
| `DIAGRAMS.md` | All Mermaid diagrams (reference) | ~400 | Visualization, documentation |

## QUICK REFERENCE

### Product in One Sentence
> AI-powered daily action assistant for B2B sales reps — prioritizes Top 5 pipeline actions, tracks execution, benchmarks performance.

### Primary User
> B2B Sales Rep. Wants: "what do I do NOW?" Not analytics. Not dashboards. Actionable daily list.

### Core Loop
> Email 08:00 → Open Dashboard → See Top 5 → Execute → Register (1-click) → Score Updates → Performance Improves

### Critical Constraint
> Registration must cost ≤5 seconds or adoption collapses. 1-click + 1-select. No forms.

### Stack of Users
1. **Vendedor** (primary) — daily action executor
2. **Gestor** (secondary) — team performance overview
3. **RevOps** (tertiary) — pipeline analytics and forecasting

## AGENT INSTRUCTIONS

- Load `INDEX.md` first, then load only files relevant to the task
- All diagrams are in `DIAGRAMS.md` — reference by ID (e.g., `DIAG-01`)
- Scoring logic is fully specified in `SCORING_ENGINE.md` — do not invent weights
- UX constraints in `UX_RISKS.md` are non-negotiable design requirements
- Dashboard block order in `DASHBOARD_SPEC.md` reflects priority hierarchy — do not reorder
