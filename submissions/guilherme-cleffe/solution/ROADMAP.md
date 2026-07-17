# Roadmap — Lead Scorer (Challenge 003)

**Team:** Guilherme (Architect) · Claude (Builder/CTO)
**Method:** plan → build small → verify → commit. Every phase ends with something that runs.
**Budget:** 4–6h total. Phases sized accordingly.

## Phase 1 — Data foundation ✅ (done)

- [x] Profile the 4 raw CRM extracts (nulls, integrity, distributions, typos)
- [x] Centralized datalake: `src/build_datalake.py` → `data/lake/` (CSVs + SQLite)
- [x] Cleaning rules documented in `docs/DATA_DICTIONARY.md`
- [x] Validation gate inside the build (row counts, unique IDs, join coverage)

## Phase 2 — Scoring engine (~1.5h)

Explainable rules + heuristics, **no black-box ML**. Score 0–100 per open deal, decomposed into named factors so a seller sees *why*:

| Factor | Signal from the data |
|---|---|
| Value | Expected value (list price — validated: won deals close at ~list) |
| Momentum / staleness | Deal age vs. typical won-cycle for that product (lost deals die at median 14d; won take 57d) |
| Product win rate | Historical win rate varies by product |
| Sector / account fit | Win rate by sector; account size & known-account flag |
| Agent track record | Agent's historical win rate & cycle speed |

Deliverable: `src/scorer.py` — pure function `score(deals) -> deals + score + factor breakdown + recommended action` + unit-testable, CLI-runnable.

## Phase 3 — Seller interface (~2h)

Streamlit app (`app.py`): the "Monday morning" view.

- **My pipeline, ranked** — top deals to work today, score + plain-language reasons
- **Filters:** agent / manager / region (bonus criterion in the brief)
- **Deal detail:** factor-by-factor score breakdown, suggested next action
- Manager view: team pipeline health, stale-deal alerts

## Phase 4 — Docs & submission (~1h)

- README: setup, scoring logic rationale, limitations
- Process log (AI-built evidence, per `submission-guide.md`)
- PR from `guilherme-cleffe` branch

## Stretch (only if time remains)

- LLM-drafted next-step suggestion per deal
- Weekly digest export (CSV/email-ready)
- Simple backtest: score historical closed deals, check calibration vs. actual win rate

## Decisions log

| Decision | Rationale |
|---|---|
| SQLite + CSV lake, no warehouse | Zero infra, stdlib, queryable; scales to this dataset ×100 |
| Snapshot date = 2017-12-31 | Dataset is historical; real clock would make every deal "stale" |
| Rules over ML | Brief explicitly rewards explainability & usefulness over model sophistication |
| Keep account-less deals | 68% of Engaging deals have no account; dropping them hides most of the open pipeline |
