---
project: ravenstack-churn-app
task: Refactor Veta to serve the RavenStack churn diagnosis (G4 AI Master challenge 001)
slug: ravenstack-churn-app
effort: E3
phase: build
progress: 14/27
mode: build
started: 2026-11-16
updated: 2026-11-16T17:55:00-03:00
---

# RavenStack churn app — ISA

> The contract for this app. The Criteria are the tests. Veta (a previous project) is the
> reference codebase only; nothing from its original dataset stays. Decisions live in
> `../../process-log/decisions.md` (D20–D26).

## Problem

The CEO of RavenStack (fictional B2B SaaS, synthetic dataset) says churn went up while CS says
satisfaction is fine and Product says usage grew. The challenge asks which causes, which
segments and accounts are at risk, and what to do, with verifiable numbers and a CEO-readable
surface. The trusted SQL layer (`../sql/`) already exists; the app is the visual and
conversational interface over it.

## Vision

An evaluator logs in from anywhere, sees the five screens of the dashboard design
(`../../process-log/dashboard/desenho-dashboard-v1.png`), and can ask any question in
Portuguese; every number traces to SQL they can inspect.

## Out of Scope

- Any data or framing from Veta's original dataset.
- Model-written "discovered stories" before the human-led analysis.
- Changing the LLM provider (DeepSeek stays; the agent loop is OpenAI-style — D25).

## Principles

- Grounded, never guessed: every number comes from a query result; no arithmetic in prose.
- Human definitions rule: D20 (churn = churn_events), D21 (unit, repetition, active month, alerts), D23 (each number on its own identifier).
- Simplicity: refactor Veta, do not rewrite it; remove rather than adapt what does not serve RavenStack.

## Constraints

- Database opened read-only; built only by `../sql/build_db.py`.
- Secrets only in `.env` (git-ignored); never printed.
- Develop locally (127.0.0.1); deploy later to Vercel or Railway with a default evaluator login.

## Goal

The five screens of the design run on the RavenStack views, the chat answers correctly under
D20–D24, and an evaluator can reach it with a username and password.

## Criteria

### Data layer (phase 1)
- [x] ISC-1: The app opens the RavenStack database read-only from `WAREHOUSE_PATH` (default `data/ravenstack.db`). Evidence: `src/engine/seed.ts`; home renders with live counts.
- [x] ISC-2: `schemaSnapshot()` returns the 8 typed tables and 7 views, without the `raw_*` copies. Evidence: probe listed accounts…support_tickets + vw_assinatura…vw_uso_detalhe.
- [x] ISC-3: The data clock reads `parametros` (2023-01-01 .. 2024-12-31). Evidence: `dataClock()` probe and dashboard-test.
- [x] ISC-4: 8 vetted metrics, each tied to a design block, all return rows. Evidence: `bun run dashboard-test` (8/8).
- [x] ISC-5: No reference to the previous dataset remains in `src/`. Evidence: `grep -ri aurelia src` → 0.

### Analyst (phase 1)
- [x] ISC-6: The system prompt carries D20, D21, D23 and the alert policy, and answers in Portuguese. Evidence: `src/engine/agent.ts`.
- [x] ISC-7: Date filters never drop rows at the day boundary (`substr` or `< next day`). Evidence: re-asked "contas e eventos em 2024" → 327 / 527 (first run gave 326 / 522; D26).
- [x] ISC-8: No arithmetic in prose; totals and percentages come from SQL. Evidence: re-test counts came from the GROUP BY query (D26).
- [ ] ISC-9: A fixed set of known-answer questions passes (2024 counts, Dec/2024 rate, reasons, alerts T06/T08).

### Overview (phase 1)
- [x] ISC-10: Four descriptive KPIs: 500 accounts, 352 accounts with event (600 events), MRR of subscriptions without end date, Dec/2024 rate 19.2%. Evidence: dashboard-test.
- [x] ISC-11: Monthly churn chart from vw_mes (accounts with event and events, 24 months, events sum to 600). Evidence: dashboard-test.
- [x] ISC-12: The discovery rail is off on the home page. Evidence: `src/app/page.tsx`.
- [x] ISC-13: The logged-in home renders the RavenStack overview. Evidence: session probe → 200, title and KPI labels present.
- [x] ISC-14: The evaluator user is seeded from `AUTH_USERNAME`/`AUTH_PASSWORD` (min 8 chars). Evidence: `avaliador@ravenstack.app` exists.

### Dashboard — five screens of the design (phase 2)
- [ ] ISC-15: Screen 1 — the three claims (B1.0–B1.3).
- [ ] ISC-16: Screen 2 — what causes churn (B2.1–B2.4).
- [ ] ISC-17: Screen 3 — segments and accounts at risk (B3.1–B3.4).
- [ ] ISC-18: Screen 4 — what to do (B4.1–B4.2).
- [ ] ISC-19: Screen 5 — base and trust in the numbers (B5.1–B5.4).
- [ ] ISC-20: Global filters (sector, country, source, plan, with/without alert records) apply on every screen.
- [ ] ISC-21: Where an alert changes a result, both numbers are shown (D21).

### Cleanup
- [ ] ISC-22: Test scripts tied to the previous dataset are removed or rewritten for RavenStack.
- [ ] ISC-23: Deck generation produces a RavenStack deck with no leftover framing.

### Deploy (phase 3)
- [ ] ISC-24: The RavenStack database ships with the deploy (`data/ravenstack.db`).
- [ ] ISC-25: Deployed on Vercel or Railway with HTTPS.
- [ ] ISC-26: The evaluator logs in with the default credentials given in the README.
- [ ] ISC-27: No secret or `node_modules` enters git (files added one by one under the ignored `submissions/` folder). Progress: commit 993fe1b staged 116 files one by one, no `.env`/`node_modules`/sqlite; privacy scan 0. Stays open until the deploy commit.

## Test Strategy

- `bun run typecheck` and `bun run dashboard-test` (needs `WAREHOUSE_PATH`).
- Known-answer questions through `scripts/ask.ts`, compared with direct SQL on the database.
- Logged-in page probe through a locally minted session.

## Decisions

- 2026-11-16: Veta copied into `solution/app` without git history; original dataset seed and demo video left out (D25).
- 2026-11-16: `.env` and `.env.example` rewritten from scratch (human correction, D26).
- 2026-11-16: The discovery rail is off until the human-led analysis produces conclusions (D26).
- 2026-11-16: Phase 1 committed (993fe1b). Kept out: the 7 test scripts tied to the previous dataset (ISC-22), Veta's `docs/`, and 3 deck textures over 2 MB that the G4 pre-commit blocks; the deck code still references them (ISC-23).

## Changelog

- 2026-11-16: ISA rewritten for RavenStack; phase 1 criteria ISC-1–8 and ISC-10–14 verified.
- 2026-11-16: Previous-dataset comments removed from Dockerfile, `.dockerignore`, `.gitignore` (now also ignores `/data/*.db`) and `data/.gitkeep`; README rewritten for RavenStack. Toward ISC-24 and ISC-27; neither closes before deploy.

## Verification

- ISC-1–5, 10, 11: `bun run dashboard-test` → DASHBOARD OK (18 checks).
- ISC-7, 8: `scripts/ask.ts` re-test → 527 events, 327 accounts in 2024.
- ISC-13: logged-in probe → status 200, "RavenStack · churn em números" present, previous dataset name absent.
