

# Pipeline Coach AI — MVP Build Plan

## Overview
A B2B sales pipeline assistant with CSV-based data, client-side processing, dark theme, and three modules: Upload, Rep Dashboard (mobile-first), and Manager Dashboard (desktop).

## Design System
- **Theme**: Dark mode — bg `#0a0d12`, surface `#11151c`, border `#222832`
- **Semantic colors**: Won `#00e5a0`, Lost `#ef4444`, Engaging `#3b82f6`, Prospecting `#f59e0b`
- **Typography**: Syne (headings 700/800), DM Mono (body/data 400/500) via Google Fonts
- **Score badges**: Crítico (red), Alto (orange), Médio (amber), Baixo (gray)

## Routes & Navigation

| Route | Purpose |
|-------|---------|
| `/` | Role selector → redirect to `/rep` or `/manager` |
| `/upload` | CSV upload with drag-and-drop, validation, anomaly banner |
| `/rep` | Rep dashboard (mobile-first) with agent selector |
| `/manager` | Manager dashboard (desktop) with manager selector + filters |

## State Management
- Zustand store holding parsed CSV data in memory (no backend, no persistence across reloads)
- Session persistence via store (survives route changes within session)
- PapaParse for client-side CSV parsing

## Module 1 — Upload Page (`/upload`)
- Drag-and-drop zone for 5 expected CSV files with status indicators (waiting → processing → loaded → error)
- Header validation per file (exact column checks)
- Row count display after successful parse
- Auto-normalize `GTX Pro` → `GTXPro` on pipeline data
- Post-upload anomaly banner: total deals, % empty accounts, normalization confirmation
- "Go to Dashboard" button enabled only when `sales_pipeline.csv` is loaded

## Module 2 — Rep Dashboard (`/rep`)
- **Agent selector** dropdown at top, persisted in session
- **Block 1 — Day Priorities**: Top 5 deals by score (scoring engine), each with account, product, score badge, context_reason, stage badge, estimated value, and 3 action buttons (Executed → bottom sheet, Reschedule, Ignore)
- **Bottom sheet**: 2-step action registration (action type → result), auto-submit, toast, fade animation, score update — max 5 seconds, no text fields
- **Block 2 — At-Risk Accounts**: Deals where `days_in_stage > team_avg × 1.2`, show top 3 + "See all" link
- **Block 3 — No Contact Ranking**: Deals sorted by days since engage_date, top 3 + info disclaimer about proxy data
- **Block 4 — Execution Score**: Session-based score (actions/recommended × 100), large number, progress bar, contextual message
- *Below fold / tabs*: Block 5 (Benchmark vs team/company with actionable suggestions) and Block 6 (Full pipeline table with sorting and stage filter)
- **Max 4 blocks above the fold** (P0 risk)

## Module 3 — Manager Dashboard (`/manager`)
- **Manager selector** + filters (office, product, period)
- **M1 — Team Execution Ranking**: Table with rep name, simulated score (win rate proxy), open deals, stale deals. Click → read-only rep view
- **M2 — Avg Aging by Rep**: Horizontal bars, worst first, delta vs team avg
- **M3 — No Contact Ranking**: Table per rep with count and avg days
- **M4 — Pipeline Coverage**: Open pipeline value per rep, color-coded vs team avg
- **M5 — Product Conversion**: Matrix (reps × products) with win rate, red→green color scale
- **Copy tone**: "Support the team" — never surveillance language

## Scoring Engine
- TypeScript function `calcPriorityScore()` with 5 dimensions: D1 contact time (max 25), D2 aging (max 25), D3 value (max 20), D4 stage (max 20), D5 benchmark (max 10)
- Reference date: `2017-12-27` (historical dataset)
- Tiebreaker: value → oldest engage_date → alphabetical account
- Labels: Crítico 85-100, Alto 70-84, Médio 55-69, Baixo 0-54

## Data Processing Rules
- Normalize product names (remove spaces) for joins
- `safeFloat()` for all numeric parsing (empty strings in open deals)
- Never discard deals with empty `account` — display as "Conta não identificada"
- Only score deals in `Prospecting` or `Engaging` stages

## Charts
- Recharts for benchmark bars, aging bars, and pipeline coverage visualizations

