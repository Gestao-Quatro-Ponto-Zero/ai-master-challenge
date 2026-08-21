# Claude.md — Lead Scorer Challenge (003)

**Project:** AI Master Challenge — sales pipeline prioritizer.
**Owner:** Gabriel Moreira
**Timeline:** built 2026-08-19, redesigned 2026-08-20 (SCORE/CONFIANÇA/ESTADO), extended 2026-08-21 (200-day reclassification, workload/fit, `mult_setor`). Full history in [docs/decisions-log.md](docs/decisions-log.md).

This file is an orientation card for whoever (human or AI) picks this repo up next — not the source of truth. For the real content, go to:

- [docs/decisions-log.md](docs/decisions-log.md) — every decision and the reasoning. **Start here.**
- [docs/architecture.md](docs/architecture.md) — technical blueprint: data flow, formula, code layout, validation.
- [docs/analise-lead-scoring.md](docs/analise-lead-scoring.md) — the statistical analysis behind every number.
- [solution/report.md](solution/report.md) — the backtest's actual output.
- [roadmap.md](roadmap.md) — what's next and why.

---

## The problem

35-person sales team, 8,800 pipeline opportunities (~60/rep, highly skewed). No prioritization logic. Budget: 4-6 hours. Deliverable must run; explainability wins.

## The one finding that shapes everything

On 6,711 closed deals, **no firmographic attribute predicts win/loss** (AUC ≈ 0.50, permutation p between 0.26-0.98 across agent/product/sector/account). **Product alone explains ~98% of deal value** (range $55-$26,768, 487×). So the tool doesn't classify win probability — it ranks **value at risk**:

```
PRIORIDADE = p̂(produto, idade) × VALOR(produto, porte) × URGÊNCIA(idade)   [dollars, auditable]
SCORE      = percentile(PRIORIDADE vs. the 4,238 historically won deals) × 100   [0-100, the number shown]
CONFIANÇA  = min(completude, suporte)                                            [0-100, how much to trust it]
ESTADO     = decision tree(sem_precedente, SCORE≥95, CONFIANÇA<50)  →  Priorizar / Acompanhar / Qualificar / Revisão em lote
```

SCORE and CONFIANÇA never combine into one number — SCORE says what it's worth, CONFIANÇA says how much to trust that. PRIORIDADE in dollars is calculated and CSV-exported but never shown (sorting by it was, in practice, sorting by list price). Full derivation of every term in [docs/analise-lead-scoring.md](docs/analise-lead-scoring.md); why PRIORIDADE left the UI in [docs/decisions-log.md](docs/decisions-log.md) (2026-08-20 entry).

**1,436 open deals, every one scoreable** — including the 987 without an account (VALOR falls back to a neutral size prior) and the 500 in Prospecting (URGÊNCIA fixed at 0.47). Was 2,089 before 2026-08-21: 653 deals open ≥200 days were reclassified to `Lost` — see the decisions-log entry for that date.

## What's NOT in the model, and why

Sales agent, manager, office, sector, account revenue, employee count, company age — all tested, none significant (p > 0.26 on every permutation test). Adding them would be noise dressed as rigor.

## Stack

FastAPI (no auth — public demo data, documented limitation) · React + TypeScript + Tailwind · pandas in-memory · `scoring/` as a pure Python package imported by API, CSV export, and the validation script, so the number shown = the number exported = the number validated. Details in [docs/architecture.md](docs/architecture.md).

## Where to look for what

| Question | File |
|---|---|
| Why this design, not another one? | [docs/decisions-log.md](docs/decisions-log.md) |
| How does the formula work, end to end? | [docs/architecture.md](docs/architecture.md) |
| Where do the constants (k, curves, cutoffs) come from? | [docs/analise-lead-scoring.md](docs/analise-lead-scoring.md) |
| Does the backtest actually confirm this? | [solution/report.md](solution/report.md) |
| What's next? | [roadmap.md](roadmap.md) |

## If you're extending this

- **Don't reintroduce auth as a partial measure.** Removed by deletion, not a flag, on 2026-08-20 — see decisions-log. Sales agent/manager/office stay plain filters, same as product.
- **Don't recondition `p̂` by more attributes without cross-validating first.** Three refinement hypotheses (product×sector, per-product aging, per-product URGÊNCIA) were tested and all three made out-of-sample prediction worse — reproducible in `validation/backtest.py` sections 6-8.
- **`k` is derived, not frozen**, at every hierarchy level as of 2026-08-21 (`K_PRODUTO` was the last frozen constant, removed that day). If you add a new shrinkage level, derive its `k` the same way — don't hardcode one.
- **PRIORIDADE (dollars) stays an internal/auditable value.** SCORE is the number a seller sees; don't wire PRIORIDADE back into the UI or into ESTADO's routing.
