# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

This is Pedro Lorenzoni's submission for the **AI Master Challenge**, specifically challenge `data-001-churn` — a churn diagnostics analysis for RavenStack, a fictional SaaS B2B platform. The work is primarily analytical (data analysis, reporting, possibly a dashboard or predictive model), not a traditional software project.

The submission must be delivered via PR to the `main` branch of the parent repo at `ai-master-challenge/submissions/pedrolorenzoni/`.

## Challenge context

**Challenge:** `data-001-churn` — Diagnóstico de Churn (RavenStack)

The core question: *why is churn rising when usage is growing and CS says satisfaction is OK?*

Required deliverables:
1. Diagnostic report answering: root cause of churn, at-risk segments with specific accounts, actionable recommendations with estimated impact
2. Process log documenting how AI was used (mandatory — submission is disqualified without it)

The challenge datasets (from Kaggle — "SaaS Subscription & Churn Analytics") must be joined across 5 tables:
- `ravenstack_accounts.csv` — ~500 accounts
- `ravenstack_subscriptions.csv` — ~5,000 subscriptions (linked via `account_id`)
- `ravenstack_feature_usage.csv` — ~25,000 rows of daily usage by feature (linked via `subscription_id`)
- `ravenstack_support_tickets.csv` — ~2,000 tickets (linked via `account_id`)
- `ravenstack_churn_events.csv` — ~600 churn events with reason codes and text feedback (linked via `account_id`)

**Key analytical angles to pursue:**
- Cross-reference feature usage with churn events — are low-usage accounts churning more?
- Compare support ticket patterns (resolution time, escalations, satisfaction) for churned vs. retained accounts
- Segment by MRR value — not all churn is equal
- Test the CEO's claim that "usage grew" — is it true across all segments?
- Distinguish correlation from causation

## Data files in this repo

The `Datas/` folder contains a separate sales pipeline dataset (CSV format) with 4 related tables: `sales_pipeline.csv`, `accounts.csv`, `products.csv`, `sales_teams.csv`. These are linked by account name and sales agent fields. **These are NOT the challenge datasets** — they appear to be supplementary data for backend/metrics work (Deal Smell and Killer Score scores).

## Custom agents

Four Claude sub-agents are configured in `.claude/agents/`:

| Agent | Model | Purpose |
|-------|-------|---------|
| `backend-skeleton-builder` | sonnet | Reads spreadsheets/CSVs and scaffolds backend skeleton (models, routes, services with TODO stubs) |
| `backend-architect` | opus | Implements full business logic into a skeleton — calculations, service layers, integrations |
| `back-metrics-reviewer` | opus | Reviews backend implementations of Deal Smell and Killer Score metrics against the `Datas/` spreadsheets |
| `frontend-builder` | sonnet | All frontend work — must read `id-visual.md` and `analise-portfolio.md` before implementing |

**Agent pipeline for building a backend:** `backend-skeleton-builder` → `backend-architect` → `back-metrics-reviewer`

## Design system files

- `id-visual.md` — visual identity: colors, typography, spacing, design tokens
- `analise-portfolio.md` — portfolio analysis: content requirements, page structure, design decisions

The `frontend-builder` agent is hardcoded to always read both files before writing any UI code.

## Submission structure

`README.md` is the submission template. It must be filled with:
- Executive Summary (3–5 sentences)
- Solution: Approach, Results/Findings, Recommendations, Limitations
- Process Log: tools used, workflow, where AI erred, what Pedro added beyond AI
- Evidências (screenshots, recordings, git history)

The Process Log block is mandatory — its absence disqualifies the submission.
