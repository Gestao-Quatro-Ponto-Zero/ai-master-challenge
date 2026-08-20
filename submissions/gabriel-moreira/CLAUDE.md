# Claude.md — Lead Scorer Challenge (003)

**Project:** AI Master Challenge — Build a sales pipeline prioritizer.

**Owner:** Gabriel Moreira

**Date:** 2026-08-19 (formula revised same day — see decisions-log.md)

---

## The problem

Sales team of 35 people, 8.800 open opportunities (~60 per person, but highly skewed). No prioritization logic — each rep guesses. RevOps Head: "Vendedor abre a ferramenta, vê o pipeline, sabe onde focar."

Budget: 4–6 hours. Deliverable must **run**. Explainability wins.

---

## The data finding (critical)

**8.800 deals closed (2016–2017), analyzed:**

- **Firmographic attributes: no signal.** AUC ≈ 0.50 on holdout. Permutation tests on agent/product/sector/account: p between 0.26–0.98 — all noise. Confirmed a second way: the hierarchical shrinkage levels account×product and product×sector have zero excess variance and collapse to weight zero automatically (`k = ∞`).
- **Value: strong signal.** Product alone explains 98.3% of closed-value variance. Products range $55–$26,768 (487×).
- **Conclusion:** don't build a categorical win-probability classifier. Build a **priority-in-dollars** score: `PRIORIDADE = p̂ × VALOR × URGÊNCIA`, where `p̂` barely moves (0.60–0.75) and the real differentiation comes from value and timing.

This is still the entire design decision tree — the formula got more rigorous, the conclusion didn't change.

---

## Solution shape

**2.089 open deals, every one scoreable — including the 1.425 without an account and the 500 in Prospecting.**

**Formula (revised 2026-08-19, see decisions-log.md for the full reasoning):**

```
p̂ = (n_produto × taxa_produto + k × 0,632) / (n_produto + k)     ← hierarchical shrinkage, k derived not chosen

  se Prospecting:  p̂ = p̂_produto (no age adjustment)
  se idade > 138:   p̂ = 0,632                                     ← censoring: revert to prior, never extrapolate
  senão:            p̂ = p̂_produto × p_ganho(min(idade,120)) / 0,632

VALOR = preço_tabela(produto) × mult_porte(porte, default 1,00)   ← default 1.00 makes no-account scoreable

  se Prospecting:  URGÊNCIA = 0,47
  se idade > 138:   URGÊNCIA = 0,15
  senão:            URGÊNCIA = risco_isotônico(min(idade,120))    ← P(resolves in 30 days), isotonic-smoothed

PRIORIDADE = p̂ × VALOR × URGÊNCIA                                  ← in dollars, "value at stake right now"
SCORE      = percentil(PRIORIDADE) × 100                           ← percentile against historical WON deals, not the open funnel
```

**SCORE's reference population is the 4,238 historically won deals** (PRIORIDADE computed for each using its real age-at-close), not the current open funnel. That population is fixed/historical — it only updates on the quarterly recalibration cycle. So SCORE = 82 literally means "this opportunity is worth more, at stake right now, than 82% of deals that historically became revenue" — and unlike a percentile against the open funnel, it never moves because some other deal entered or left the pipeline.

**Counter-intuitive finding baked into the formula:** `p_ganho(t)` **rises** with age (0.632 at day 0 → 0.751 at day 120) — it does not decay. What age consumes is the **window**: by day 57, half of all historical wins have already happened; by day 88, only 25% remain. That's why URGÊNCIA uses `risco(t)` (P of resolving in 30 days, isotonic-smoothed) instead of an age-decay proxy.

**Censoring:** nothing in the 6.711 closed deals took more than 138 days. Above that, revert to the prior instead of extrapolating — forward-filling would give `p̂ = 0.751` (the curve's highest value) to a 377-day-old deal, rewarding abandonment.

**CONFIANÇA (A–D)** — separate from PRIORIDADE, never combined into one number: how much is actually known about the deal.

| Nível | Regra | % funil | % prioridade |
|---|---|---:|---:|
| A | conta conhecida + Engaging + idade ≤138 | 4.3% | 11.3% |
| B | conta OU Engaging (um dos dois) | 17.8% | 39.2% |
| C | sem conta e Prospecting | 16.1% | 20.2% |
| D | idade > 138 (censurado) | 61.8% | 29.3% |

**ESTADO** — 5 values, replacing Diamante/Ouro/Prata/Bronze *and* absorbing the old 3 lanes (Prioridades/Novos/Zumbis). **CONFIANÇA ≠ ESTADO**: CONFIANÇA is how much to trust the score (the foundation); ESTADO is the recommended action, and the right action depends on *both* SCORE and CONFIANÇA crossed — not CONFIANÇA alone with SCORE only as a tiebreaker within the top bucket (that was the first draft, and it was wrong — corrected 2026-08-19).

| CONFIANÇA | SCORE ≥ 50 | SCORE < 50 |
|---|---|---|
| A | Foco urgente | Acompanhar |
| B | Acompanhar | Engajar |
| C | Engajar | Qualificar |
| D | Desistir | Desistir |

The SCORE cutoff is 50 — the median of the reference distribution itself (won deals), not a separate constant to derive and freeze. The diagonal is the point: a high SCORE with weak CONFIANÇA (B) doesn't become Foco urgente — it becomes Acompanhar, because acting with urgency on a number you don't fully trust is the exact risk CONFIANÇA exists to flag. A low SCORE with CONFIANÇA C isn't Desistir — it's Qualificar, because what's missing is information, not necessarily value. CONFIANÇA D is the one one-way rule: outside the data's historical support, no SCORE is trustworthy enough to justify anything but batch review.

Each opportunity gets a deterministic-template explanation + action plan, not just a number.

**Access control:** Sales Agent / Supervisor / Manager, mapped 1:1 onto the real hierarchy already in `sales_teams.csv` (35 `sales_agent` → 6 `manager` → 3 `regional_office`). No password — an identity picker issues a server-signed token with scope already resolved; every data endpoint enforces that scope server-side (a client filter can only narrow it, never widen it — out-of-scope requests get 403). This is identity selection, not real authentication; documented as a limitation.

**CSV export:** every data load writes a full processed dataset (all 2.089 open opportunities + every derived field) to disk for offline consultation. Separate from the existing "export filtered IDs" button on the Desistir tab.

**Validation:** standalone Python script runs on the 6.711 closed deals — permutation tests, reproduces the `k` derivation and the account×product/product×sector collapse, checks `risco(t)` monotonicity, confirms no closed deal exceeds 138 days, reports PRIORIDADE concentration (top 10% ≈ 50% of total).

---

## Stack

- **Backend:** FastAPI, Python 3.10+, lightweight token signing for sessions
- **Frontend:** React 18+, TypeScript
- **Data:** Pandas in-memory, behind a clean repository module
- **Scoring:** Pure Python package in `scoring/`, imported by API, export, and validation script
- **No password auth** (documented limitation) — identity-based RBAC with server-enforced scope IS in scope
- **Theme:** G4 Business palette (navy #001F35, gold #B9915B, light bg #FAFBFC, alert #AF4332 exclusive to Desistir)

**Testing (part of Definition of Done, not optional):**
- Unit: scoring engine (shrinkage incl. `k=∞` collapse, aging curves, censoring, CONFIANÇA branches, ESTADO assignment, explanation generation) + scope resolution
- E2E: full API cycle — identify → token → scoped listing → out-of-scope request (403) → no-token request (401) → role-restricted rollup → Manager-only CSV download

---

## Files and their roles

**Key decision documents:**
- [`docs/decisions-log.md`](docs/decisions-log.md) — all decisions and the reasoning, including the 2026-08-19 formula revision. See this first.
- [`docs/architecture.md`](docs/architecture.md) — technical blueprint, data flow, component layout.
- [`analise-lead-scoring.md`](analise-lead-scoring.md) — full statistical analysis. Answers "why is AUC 0.50?" with evidence.
- [`../../openspec/changes/add-lead-scorer/`](../../openspec/changes/add-lead-scorer/) — formal proposal/design/specs; source of truth for exact requirement wording.

**Submission structure:**
- `solution/` — code (will have `scoring/`, `api/`, `web/`, `validation/`)
- `process-log/` — chat exports and screenshots showing Claude Code usage
- `data/` — CSVs (accounts, products, sales_pipeline, sales_teams, metadata)

---

## Decisions

**Design decisions made via grilling session (32 questions) + a 2026-08-19 formula revision pass. Full reasoning in `docs/decisions-log.md`.**

Still holding from the original session:
1. Score on value/timing, not a win-probability classifier — AUC evidence killed the predictive path
2. Rank open deals (not score new leads) — 2.089 open is the real problem
3. Product coverage as account potential, not deal signal — 39.6% effort on 5.4% revenue
4. FastAPI + React (not Streamlit) — now also required by RBAC: isolation must be server-side
5. Validate with permutation tests, ship the evidence

**Revised 2026-08-19 (reversing earlier calls, with the new evidence that justified it):**
- `MULT_PORTE` is **back in** VALOR — variance decomposition shows product+porte explains 98.7% vs. 98.3% product-alone, a real 0.4pp gain I hadn't measured before. Default 1.00 when account unknown is what makes "score even without account" literal.
- Percentile normalization is **back** for the display SCORE — matching the new spec's `SCORE = percentil(PRIORIDADE) × 100` — but against the fixed historical population of won deals, not the live open funnel. That's strictly more stable than the original percentile-scoring rejection was worried about: the reference never depends on what's currently in the pipeline.
- Tiers (Diamante/Ouro/Prata/Bronze) + lanes (Prioridades/Novos/Zumbis) collapsed into 5 ESTADO values — a 4×2 decision table crossing CONFIANÇA with SCORE (≥50 or not), not CONFIANÇA alone. First draft had SCORE only mattering within CONFIANÇA A; corrected same-day after review — CONFIANÇA is the trust in the score, ESTADO is the action, and the action genuinely depends on both.
- Auth is no longer fully out of scope — identity-based RBAC with server-enforced isolation is now required (still no password).

Still true / unchanged:
- Win-rate by agent/product/sector: no signal (confirmed twice now — permutation tests AND the hierarchical `k=∞` collapse).
- Smooth exponential decay on age: still wrong, and now more clearly wrong — `p_ganho(t)` actually *rises* with age, doesn't just plateau.

---

## Known limitations and evolution path

**Doesn't do:**
- Categorical win-probability forecasting (`p̂` varies only 0.60–0.75; real differentiation is value+timing).
- Real password authentication — identity selection with server-enforced scope, not SSO.
- Behavioral intent (no email opens, call logs, page visits).
- Automatic portfolio rebalancing — insight surfaces in Gestão, policy stays off-system.
- Real persistence. All in-memory; CSV export is the closest thing to a durable artifact.
- Write-back to CRM.

**Evolution (MVP → production):**
1. **Database** (Supabase) + auto-score + auto-regenerate the processed CSV on new deal
2. **Real auth** (SSO/OIDC) on top of the same three roles
3. **Behavioral signal** (CRM webhook + speed-to-lead model) to recalibrate `p̂`
4. **A/B test:** half the reps on score, half on gut; track revenue
5. **Mobile** (React Native)

---

## To run the solution

```bash
# Backend
cd solution/api
pip install -r requirements.txt
python -m uvicorn main:app --reload

# Frontend (another terminal)
cd solution/web
npm install && npm run dev

# Validation
cd solution/validation
python backtest.py

# Tests
cd solution/scoring && pytest            # unit
cd solution/api && pytest tests/e2e      # e2e, incl. RBAC isolation
```

Or via Docker:
```bash
docker compose up
```

---

## For the next person

- **Start here:** [`decisions-log.md`](docs/decisions-log.md), especially the 2026-08-19 entry — it explains every reversal from the earlier design.
- **Then:** [`architecture.md`](docs/architecture.md) for the implementation blueprint.
- **Then:** [`analise-lead-scoring.md`](analise-lead-scoring.md) for the evidence behind every number.
- **Code:** `scoring/` is the core; `api/`, `web/`, `validation/`, and the CSV export are all consumers. Keep that separation — it's what makes "the number shown = the number validated = the number exported" true.
- **Watch for:** PRIORIDADE is deterministic and auditable; SCORE (the percentile) is only stable between dataset generations, not between requests — that distinction is load-bearing, don't collapse it back into a single always-live percentile.
- **RBAC:** scope enforcement lives server-side in the API, not the UI. If you're extending an endpoint, the scope check goes in first, before the query.

---

## Questions?

- **Why not ML?** AUC ≈ 0.50 on the best available attributes. Permutation tests and the hierarchical `k=∞` collapse both say the same thing two different ways.
- **Why does age *raise* `p̂` instead of lowering it?** That's what the data shows (`p_ganho(0)=0.632` → `p_ganho(120)=0.751`). What age actually costs is the decision window (`janela(t)`), which is what URGÊNCIA tracks.
- **Why revert to the prior above 138 days instead of extrapolating?** Forward-filling would reward the most abandoned deal in the funnel with the curve's highest score. No closed deal in the data ever took that long — there's no precedent to extrapolate from.
- **Why 5 estados instead of 4 tiers?** They're not a relabeling — they fold in both the old tiers and the old lanes, and they cross CONFIANÇA with SCORE in a 4×2 table, not CONFIANÇA alone. CONFIANÇA answers "how much should I trust this number"; ESTADO answers "what do I do about it" — and that answer genuinely depends on both how much the deal is worth and how solid that number is. A high score you don't fully trust gets "keep watching," not "drop everything."
- **Why no real login?** Time budget for a 4–6h challenge. What's real is server-side scope enforcement once identity is picked — documented explicitly as a limitation, not hidden.
