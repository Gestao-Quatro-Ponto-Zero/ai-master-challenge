---
project: ravenstack-churn-app
task: Refactor Veta to serve the RavenStack churn diagnosis (G4 AI Master challenge 001)
slug: ravenstack-churn-app
effort: E3
phase: build
progress: 34/44
mode: build
started: 2026-11-16
updated: 2026-11-17T00:30:00-03:00
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

### Dashboard — executive overview (D28)
- [x] ISC-28: The first screen (`/`) is an executive overview with no block chrome: six headline numbers (accounts, subscriptions, accounts with churn, churn rate of the last month, MRR ativo, revenue at risk) and eight bar/column/donut charts (churn by month, churn reasons, revenue by industry, plan, country; churn by industry, plan, source), all filtered. Evidence: `bun run visao-test` → VISÃO GERAL OK (15 checks: 500, 5,000, 352, 600, 19.2%, MRR ativo, revenue at risk, breakdowns add up, FinTech filter); screenshot 1440×900.
- [x] ISC-30: Every number shows the table it comes from (D29). The overview groups its headline numbers by `accounts`, `churn_events` and `subscriptions`. Every chart and block carries colored source chips, and numbers that cross tables name both. The analyst prompt has the same rule. Evidence: screenshot; `visao-test` checks 110 (`accounts.churn_flag`) and 486 subscriptions with `end_date` in 312 accounts.
- [x] ISC-31: Executive wording (D30). No table names, column names or decision codes appear on screen. Headline numbers use plain labels in three groups (Contas, Eventos de churn, Assinaturas e receita), with at most one short note each. The monthly churn chart is replaced by month-on-month growth lines (active accounts against accounts with a churn event, % over the previous month, from Apr/2023 on). Evidence: `visao-test` (starts 2023-04; Dec/2024 +5.3% / +60%; Feb/2024 −44.4%); screenshot 1440×900.
- [x] ISC-32: New vs lost revenue (D31). A monthly line chart sits in the overview's second slot: MRR from new accounts against MRR of subscriptions cancelled in the month, for the last 12 months of data. Each series has a linear trend projected forward, with the projection shaded and the crossing month marked. A plain sentence states when the loss catches up with acquisition. Evidence: `visao-test` (2024 totals match independent queries; trends match a TypeScript fit; crossing 2026-03, 15 months); screenshot.
- [ ] ISC-33: The human confirms the D31 definitions: new revenue is the first subscription of a new account, lost revenue is the subscriptions with `end_date` in the month, and the trend is linear over 2024.
- [ ] ISC-29: The human confirms the churn rate definition (D28): last month's account rate. Revenue at risk was removed by the human (D32): the MRR of accounts with an event was not a valid measure.
- [x] ISC-34: One screen, no scroll (D32). A single header row holds eight headline numbers, with no revenue at risk. A paid vs trial accounts donut takes the industry revenue chart's former slot. Lists of five or more are columns with the value on top, shorter lists stay as bars, and there are four panels per row in the lower two rows. Every chart draws at its panel's pixel size. Evidence: browser probe at 1440×900 and 1280×800 shows main scrollHeight = clientHeight with no panel overflowing; `visao-test` checks paid + trial = 500 (403 / 97); screenshots.

### Dashboard — five screens of the design (phase 2)
- [x] ISC-15: Screen 1 — the three claims (B1.0–B1.3). Evidence: `bun run tela1-test` → TELA 1 OK (19 checks); logged-in screenshot at 1440×900 with and without the chat panel.
  - [x] ISC-15a: ~~B1.0 claim cards~~ removed by the human (D28): they took space and gave the user nothing. Screen 1 keeps B1.1–B1.3 at `/tela/1`.
  - [x] ISC-15b: B1.1 — monthly accounts with event and events (one chart), the two rates with and without accounts outside the base (second chart, one axis each), and lost MRR as a separate number: the subscriptions' total of the accounts with an event, no event date (D23, D27). Evidence: 600 events; 352 accounts, US$ 7,990,982; rates differ in 14 months.
  - [x] ISC-15c: B1.2 — tickets by quarter, stacked by score 3, 4, 5 and "no score"; totals with and without the T08 records. Evidence: 2,000 / 825 no score; without T08 923 / 372.
  - [x] ISC-15d: B1.3 — monthly usage records, with and without the alert records (T06, E13), plus small multiples by sector. Evidence: 25,000 with, 5,554 without; T06 = 19,432 = vw_dq_ocorrencias; sectors add to the total.
  - [x] ISC-15e: Unfiltered B1.1 equals `vw_mes` month by month (test; the view's 4-decimal rates allow half a 0.1 step).
- [x] ISC-15f: Navigation — the overview and the five screens in the side menu (`/` = overview, `/tela/1..5`; changed by D28), chat in a side panel that opens on any screen (D27). Evidence: probe → `/`, `/tela/2`, `/tela/5` 200, `/tela/9` 404; screenshot with the panel open. Screens 2–5 list their blocks as "not built yet". Changed by D44: three screens; `/tela/4` and `/tela/5` answer 404.
- [x] ISC-16: Screen 2 shows churn broken down by every attribute (D34): industry, source and country as % of accounts with `churn_flag = 1` (D36; DevTools 31%, FinTech 22.3%), shaded one orange from dim (lowest) to bright (highest) (D35); events by reason; and three donuts showing how the churn splits (D37): plan and trial vs paid over the 110 accounts with `churn_flag = 1`, billing frequency over the 486 subscriptions with `churn_flag = 1`. Seven charts, one screen, no scroll. Global filters reach every chart. Evidence: `bun run tela2-test` → TELA 2 OK (16 checks, each against an independent query); screenshots at 1440×900 and 1280×800 with no scroll. Human review pending.
- [x] ISC-17: Screen 3 shows support and product usage (D34, D43), one screen, no scroll: a header of ticket and usage numbers; tickets, satisfaction and uses month by month; tickets by priority and score (donuts) and by resolution and first-response bands; uses × error rate per feature (stable and beta apart) and the ten most used features. Tickets follow the account filters, usage the subscription filters (D27); the alert filter drops T08 tickets and T06/E13 usage. Evidence: `bun run tela3-test` → TELA 3 OK (23 checks against independent queries; 923 tickets without alerts); screenshots at 1440×900 and 1280×800 with no scroll and no console errors. Human review pending. The earlier Tela 3 content (accounts ranked by exposure) still needs a screen; the average-age line went to the overview (ISC-36).
- [x] ISC-35: The overview no longer breaks churn down by attribute (D34). Its four churn charts moved to screen 2, leaving three bands: header, the time lines and the revenue row.
- [ ] ISC-37: The chat panel scrolls, so a long answer can be read to the end. Reported by the human on 2026-11-17: an answer with items 1, 2 and 3 could not be scrolled, so it was unclear whether more followed. To fix before the project closes (human: "não é para resolver isso agora"). Check: a long answer in the side panel, at 1440×900 and 1280×800, scrolls to its last line, with wheel and trackpad.
- [x] ISC-36: The overview shows the average age of the base month by month, jan/2023–dez/2024 (D40): active accounts from signup and subscriptions in force from start, in months at each month end. Evidence: `bun run visao-test` → VISÃO GERAL OK (24 months; Dec 2024 accounts 11.16 and subscriptions 5.44 against independent queries; the sector filter reaches both lines); screenshots at 1440×900 and 1280×800 with no scroll. Evidence: `src/app/page.tsx` has no churn-by-attribute panel; screenshots at 1440×900 and 1280×800 with no scroll; `bun run visao-test` → VISÃO GERAL OK.
- [x] ISC-18: Only the overview and three screens remain (D44, human decision): screens 4 (what to do) and 5 (base and trust) leave the app, and their content goes into the written diagnosis report. Evidence: the side menu lists Visão geral and screens 1–3; probe → `/`, `/tela/1..3` 200, `/tela/4` and `/tela/5` 404.
- [x] ISC-19: Dropped by D44. Screen 5 (base and trust in the numbers) is not built; its blocks B5.1–B5.4 become sections of the written report.
- [ ] ISC-20: Global filters (sector, country, source, plan, with/without alert records) apply on every screen. Plan follows the identifier (D27): account numbers use the account's plan, subscription numbers the subscription's plan. Filter values are checked against the database before entering SQL. Progress: done on screen 1 (`src/engine/filtros.ts`; test: sectors add to 600 events, plan per identifier, injected value dropped); stays open until screens 2–3 use it (screens 4–5 dropped, D44).
- [ ] ISC-21: Where an alert changes a result, both numbers are shown (D21).
- [x] ISC-39: The marked charts become a presentation built as a Minto pyramid (D45, human request: "não é só colocar o gráfico num slide"), the structure of Veta’s deck arranger: cover with the governing thought, executive summary (the pyramid on one page), SCQA context, one divider per key-line section (2–4, MECE, titled as assertions), one slide per chart with its action title, supporting lines and the faithful image, and the recommended actions. The app’s LLM writes the narrative; the code re-runs each chart’s SQL and checks every written number against those rows (a percentage only against percentages or composition shares, so a count of 85 cannot become 85%); what fails is dropped or replaced and listed. Every marked chart lands on a slide; without an LLM a plain arrangement (one section per screen) still builds. The pyramid is shown for review before the .pptx downloads; a change in the marks requires rebuilding. Evidence: `bun run deck-marcados-test` → DECK MARCADOS OK (28 checks); three live builds with 10 charts (7–8 s each), the last with zero number adjustments. Variable-length slide text boxes shrink to fit (`fit: "shrink"`, 11 boxes) as a guard against overflow. Not yet seen rendered: no LibreOffice here, and Keynote’s scripted export failed.
- [x] ISC-38: Any chart on the overview and screens 1–3 can be marked for the deck (D44). The mark keeps a faithful copy (SVG, and a 3× PNG drawn from it) of the chart as it is on screen, with the screen, the filters in force, the title and the note; the same chart under another filter is another mark. "Gráficos marcados" lists them with PNG and SVG downloads (unmark in red, human request); the .pptx is the Minto deck of ISC-39 (D45). Evidence: `bun run marcados-test` → MARCADOS OK (17 checks: active SVG refused, re-marking refreshes, order, origin, per-user, one slide per mark, 4:1 image stays 4:1); browser run marking 6 charts across the 4 pages, all pressed, list and .pptx (6 slides, image centred, aspect kept) checked; screens still fit at 1440×900 and 1280×800.

### Work tool (D46, human request 2026-11-17: "estamos criando uma ferramenta de trabalho")
- [x] ISC-40: Drill-down. Clicking a bar or slice of a screen chart opens that slice (for example "motivo = Recursos", 114 events): its size, the slice broken down by every other attribute, the records behind it, and a cross of two attributes picked by the user. A click inside the drill goes one level deeper (breadcrumbs back). Every number comes from SQL shown beside it; filter values are checked against the database before entering SQL. Each drill chart can be marked for the deck; "ask the analyst" sends the slice to the chat. Check: the reasons chart on screen 2, click "Recursos", 114 events, breakdowns sum to 114. Evidence: `bun run recorte-test` → RECORTE OK (28 checks: totals against independent SQL, every breakdown sums to the slice, second level = the bar clicked, injected value refused, cross sums to the slice, global filter applied, tickets and usage universes); browser: screen 2 reasons → Recursos (114 events, 104 accounts) → month, screen 3 priority and top features, overview with a country filter, no console errors. Five universes (events, accounts, subscriptions, tickets, usage). Limit: drill breakdowns follow the account/subscription filters and the alert filter, like the screens.
- [x] ISC-41: Custom screens. The user creates a screen, asks the analyst (DeepSeek) for an analysis in plain language, and the charts the analyst makes land on that screen as panels with their SQL; follow-up requests see the screen's earlier analyses; panels can be removed and marked for the deck. Check: create a screen, ask two questions, two or more panels persist after reload, one marked and listed in "Gráficos marcados". Evidence: `bun run telas-test` → TELAS OK (15 checks, scripted analyst); live with DeepSeek in the browser: screen "Recursos e churn", two chained requests (13 s, 6 s), three panels with their SQL, one marked and listed, all kept after reload, no console errors. The chat side panel now also sends earlier turns to the analyst.
- [x] ISC-42: The presentation follows the context, not a fixed template: it is built from the marked charts, the conversations with the analyst the user picks, and the user's briefing (goal, audience); numbers in the narrative are checked against the charts' SQL and the conversations' SQL. Two builds with different briefings or conversations give different governing thoughts. Each build is kept, so earlier decks can still be downloaded. Evidence: `bun run deck-marcados-test` → DECK MARCADOS OK (35 checks: the arranger receives the picked screen, a number from that screen's SQL is kept and the same number without that context is dropped, another user's screen is refused, history per user); two live DeepSeek builds over the same 10 charts gave different governing thoughts, sections and actions (Diretoria vs Produto + the screen "Recursos e churn").
- [x] ISC-43: Charts made by the analyst in the chat can be marked for the deck or sent to a custom screen. Evidence: browser run: a column chart from the chat marked (POST 201, route `/chat`, with its SQL) and sent to a new screen; Veta's old deck-draft pins hidden in the chat.

### Cleanup
- [ ] ISC-22: Test scripts tied to the previous dataset are removed or rewritten for RavenStack.
- [ ] ISC-23: Deck generation produces a RavenStack deck with no leftover framing. Progress: the marked-charts .pptx (ISC-38) is the RavenStack deck path; Veta’s pin-and-AI deck code (`deck.ts`, `/decks`) is off the menu but still in the code. The Minto arranger now lives in `deckMarcados.ts` for the marked charts (ISC-39).

### Deploy (phase 3)
- [x] ISC-24: The RavenStack database ships with the deploy (`data/ravenstack.db`). Evidence: `outputFileTracingIncludes` puts it in every function; `/api/health` on the deploy → `{"warehouse":"ok"}`; every screen renders from it.
- [x] ISC-25: Deployed on Vercel or Railway with HTTPS. Evidence: https://ravenstack-churn.vercel.app (Vercel, region gru1; D46.4). The app DB is an encrypted SQLite snapshot in a private Vercel Blob, loaded when another instance wrote a newer one (conditional GET) and uploaded before a writing route responds. Browser run on production: evaluator login, six pages 200, drill, mark, custom screen with DeepSeek kept after reopening, no console errors.
- [ ] ISC-26: The evaluator logs in with the default credentials given in the README. Progress: the deploy has its own evaluator login (`avaliador@ravenstack.app`, a new password kept in the git-ignored `.env.deploy`), verified on production; the README names the user but not the password, because whoever has it spends the DeepSeek key. Open until the human decides how the password reaches the evaluators.
- [ ] ISC-27: No secret or `node_modules` enters git (files added one by one under the ignored `submissions/` folder). Progress: commit 993fe1b staged 116 files one by one, no `.env`/`node_modules`/sqlite; privacy scan 0. Commit 7213f7e (screens, D30–D43) staged 40 files one by one with the same checks; privacy scan 0; pushed to `submission/ronaldo-tkotz`. Stays open until the deploy commit.

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

- 2026-11-17: Contextual deck and chat charts (D46.3, D46.5): `montarDeck` takes the audience and the conversations and custom screens the user picks (`carregarContexto`, `valoresDeSql` re-runs their SQL for the number check), keeps every build (`decks_historico`, `pptx?id=`); chat charts get "Marcar para a apresentação" (route `/chat`) and "Enviar para uma tela"; Veta's deck-draft pins hidden. ISC-42 and ISC-43 met.
- 2026-11-17: Deployed on Vercel (D46.4): https://ravenstack-churn.vercel.app. `engine/estado.ts` keeps the app DB as an encrypted snapshot in a private Blob (conditional-GET freshness check, upload before a writing route responds via `gravando()`), `vercel.json` (gru1), `.vercelignore`, warehouse traced into every function. `estado-test` passes locally and against a test Blob. ISC-24 and ISC-25 met; ISC-26 waits on the human (publish the evaluator password in the README or not).
- 2026-11-17: Custom screens built (D46.2): `engine/telasUsuario.ts`, `api/telas/*`, `/telas`, `/telas/[id]`, `TelaPropria.tsx`, "Minhas telas" in the menu; marking accepts `/telas/<id>`; `ask()` takes earlier turns and extra instructions, and the chat sends its history. `telas-test` 15 checks. ISC-41 met.
- 2026-11-17: Drill-down built (D46.1): `engine/recorte.ts` (five universes, fixed dimension catalogue, path values checked against the database), `api/recorte`, `components/telas/Recorte.tsx` (slice size, profile against the rest of the base, breakdowns that go one level deeper on click, cross of two attributes, records, ask the analyst); click targets on screen 2, screen 3 and the overview. `recorte-test` 28 checks. ISC-40 met. ISC-41 to ISC-43 opened (D46).
- 2026-11-17: Minto deck from the marked charts (D45): `engine/deckMarcados.ts` (grounding, number check, LLM and plain arrangers, .pptx), `api/marcados/deck`, `Apresentacao.tsx`; marks store their SQL; unmark button in red. `deck-marcados-test` 28 checks. ISC-39 met.

- 2026-11-17: Screens 4 and 5 removed (D44, human: the diagnosis goes in a written report); chart marking for the deck built (`engine/marcados.ts`, `api/marcados/*`, `components/telas/captura.ts`, `Marcados.tsx`, `ListaMarcados.tsx`, `/marcados`; toggle in `Painel` and `Bloco`; menu "Gráficos marcados" replaces "Decks"). `marcados-test` 17 checks. ISC-18, ISC-19 (dropped), ISC-38 met.

- 2026-11-17: ISC-37 opened: the chat panel does not scroll (human report). Deferred by the human to before the project closes; nothing changed in code.

- 2026-11-17: Screen 3 built (D43): `src/engine/tela3.ts` rewritten (indicadores3, mensal3, compositions, bands, top features, recursosErros), `src/app/tela/3/page.tsx`, shared `Indicador.tsx`, `LinhasMensais`, `LineChart.yMax`, 4th donut colour (validated), leftover `height="auto"` removed, sidebar renamed. `tela3-test` 23 checks. ISC-17 met.

- 2026-11-17: Line-chart y axis hugs the data (D42): `tightScale` picks the smallest round step (1, 2, 2.5, 3, 5 × 10ⁿ) covering the max (trends included) in ≤4 intervals. Age axis 0–12 months (was 0–20); revenue 0–800 mil. Signed axes unchanged.

- 2026-11-17: Overview in four bands (D41): header; growth and revenue lines side by side; average age full width; the four revenue/account charts. Bare line charts trimmed to 12/24px outer margins. ISC-34 and ISC-36 re-verified at 1440×900 and 1280×800 with no scroll.

- 2026-11-17: Average age of the base on the overview (D40): `idadeMedia` in `visaoGeral.ts` (`MESES_CTE` exported from `tela1.ts`), `IdadeMedia` line chart, overview row 2 now three columns. ISC-36 added and met.

- 2026-11-17: Donut legend sized from measured text (D39): name and figure columns never overlap; the count drops before the donut gets too small; the group is centred. Fixes overlap in panels 420–520 wide that the 1440/1280 screenshots missed. ISC-34 re-verified at 1280, 1440, 1512 and 1728 widths.

- 2026-11-17: Column labels (D38). In `fit` mode, category labels are all horizontal at 10px or all rotated to −45° (stagger removed), with their own bottom room and left gutter; value labels share one size per chart sized to the longest value; the invalid `height="auto"` SVG attribute was removed. ISC-34 (one screen, no scroll) re-verified at 1440×900 and 1280×800 on the overview and screen 2.

- 2026-11-17: Screen 2 bottom row shows the churn composition (D37): `composicaoPlano`, `composicaoTrial` (accounts with churn_flag) and `composicaoCobranca` (subscriptions with churn_flag), drawn with the overview donut. The rate rings (`Aneis`) were removed. ISC-16 restated.

- 2026-11-17: The account churn rate by attribute is now `churn_flag` (D36, human decision after asking where 73.5% came from: it was "has any churn event", D20). `churnPor` changed; monthly series, the event cards and screen 1 counts stay on events. Centred column labels are nudged inside the chart edge. `tela2-test` 17 checks. ISC-16 restated.

- 2026-11-16: Screen 2 restyled (D35). `Colunas` gained `gradiente` (one-hue ordinal ramp, min→max per chart); new `Aneis` component draws one donut ring per group; the churn series now return each group's base `n`. Bottom row split 3:2:2 so every ring is the same size. ISC-16 restated.

- 2026-11-16: Screen 2 rebuilt on the human's review (D34). The overview's four churn charts moved to screen 2, which gained churn by country, by billing frequency and trial vs paid. The dumbbell and the reasons table were removed (`Comparativos.tsx` deleted); support and feature usage moved to `src/engine/tela3.ts` for screen 3, now about tickets and product usage, with `tela3-test`. ISC-16 restated.

- 2026-11-16: The human set the plan for screens 2–5 (D33): executive style, risk ranked by exposure plus a subscription-age line, and screen 4 deferred until the human's analysis. Screen 2 built (`src/engine/tela2.ts`, `src/app/tela/2/page.tsx`, HTML comparisons in `Comparativos.tsx`); ScatterChart gained `viewWidth`; churn reasons are shown in Portuguese on the overview too. Next: screen 3, and screen 1 in the executive style.

- 2026-11-16: Fit-to-screen overview (D32). Charts take a `viewWidth` prop, and `Ajustado` measures each panel. Vertical bars gained `fit`, value labels, staggered category labels and a max-based scale. The donut gained a narrow layout. TelaShell gained an `ajustar` mode. Revenue at risk was removed from the engine, the screen and the test. ISC-34 met; ISC-29 reworded.

- 2026-11-16: Added the new vs lost revenue chart (D31) in the slot of the churn-reasons chart, which moved to the end. The line chart now accepts gaps (null values), a shaded projection, a marker, and a y gutter sized to its labels. ISC-32 met; ISC-33 is open for the human's confirmation of the definitions.

- 2026-11-16: The human asked for linear trend lines on the month-on-month growth chart, in the same color and dashed. The least-squares fit is in the chart's SQL, and the line chart now takes optional dashed trend series. Serves ISC-31. Evidence: `visao-test` checks the SQL fit against a TypeScript fit (accounts 37.6 → −3.1, churn 12.3 → 30.3); screenshot.

- 2026-11-16: The human asked for an executive look (D30). The source chips from D29 are gone; the grouping stays, worded plainly. Decision codes are off the screen. The line chart now draws values below zero. The unused monthly column chart is removed. ISC-31 added and met; ISC-30 now holds through the grouping and the SQL rather than the chips.

- 2026-11-16: ISA rewritten for RavenStack; phase 1 criteria ISC-1–8 and ISC-10–14 verified.
- 2026-11-16: Human asked to move the SQL link to the top-right corner. Panels (overview) and blocks (screen 1) now have a small "SQL" switch in the header, and the query opens between the header and the chart. The footer link is gone. Evidence: browser probe found 8 switches on `/` and 3 on `/tela/1`; one click opened the query (screenshot).
- 2026-11-16: Human asked for square bar ends and a tighter layout. Horizontal bars now have square ends with a 3-unit corner radius, like the columns. Bar gutters fit the labels and the bar height follows the bar count. Panel, tile and gap spacing reduced, and the donut's centre text fits the hole. Evidence: screenshot (page about 300 px shorter); axis, visão and tela1 tests pass.
- 2026-11-16: Screen 1 built (D27). Also: the Veta "Analyses" accordion (sales-pipeline questions) removed from the menu; chat starters, placeholder and labels in Portuguese about RavenStack; x-axis drops the stepped label that collided with the last month (axis-test 11/11). Palettes checked with the dataviz validator (dark, all pass). Open: TopBar still in English; Chat has other English strings (pin/deck).
- 2026-11-16: Dev server broke on `globals.css` (Tailwind's automatic scan read `.next/dev` logs holding a garbled class). Fix: `@import "tailwindcss" source("..")`, scan limited to `src/`. Evidence: `/login` 200, compiled CSS has utilities. Serves ISC-13.
- 2026-11-16: Previous-dataset comments removed from Dockerfile, `.dockerignore`, `.gitignore` (now also ignores `/data/*.db`) and `data/.gitkeep`; README rewritten for RavenStack. Toward ISC-24 and ISC-27; neither closes before deploy.

## Verification

- ISC-1–5, 10, 11: `bun run dashboard-test` → DASHBOARD OK (18 checks).
- ISC-7, 8: `scripts/ask.ts` re-test → 527 events, 327 accounts in 2024.
- ISC-13: logged-in probe → status 200, "RavenStack · churn em números" present, previous dataset name absent.
