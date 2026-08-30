# Claude.md — Lead Scorer Challenge (003)

**Project:** AI Master Challenge — sales pipeline prioritizer.
**Owner:** Gabriel Moreira

This file is an orientation card for whoever (human or AI) picks this repo up next — not the source of truth. It describes the system as it stands today; every change and the reasoning behind it lives in [process-log/decisions-log.md](process-log/decisions-log.md).

| Question | File |
|---|---|
| Why this design, not another one? (full history) | [process-log/decisions-log.md](process-log/decisions-log.md) |
| How does the formula work, end to end? | [docs/architecture.md](docs/architecture.md) |
| Where do the constants (k, curves, cutoffs) come from? | [docs/analise-lead-scoring.md](docs/analise-lead-scoring.md) |
| Does the backtest actually confirm this? | [docs/report.md](docs/report.md) |
| What's next? | [docs/roadmap.md](docs/roadmap.md) |
| How was AI used along the way? | [process-log/narrative.md](process-log/narrative.md) |

---

## The problem

35-person sales team, 8,800 pipeline opportunities (~60/rep, highly skewed). No prioritization logic. Budget: 4-6 hours. Deliverable must run; explainability wins.

## The one finding that shapes everything

On the 6,711 closed deals, **no firmographic attribute predicts win/loss** — product, sector, account and `sales_agent` alike (AUC 0.475-0.523 isolated and 0.500 combined; permutation p between 0.262 and 0.965; see [docs/report.md](docs/report.md) §1, §2 and §12). The shrinkage hierarchy says the same thing a second way: all three levels below global collapse (`k = ∞`), so **`p̂` is 0.632 for every product** — 0.00pp of spread. **Product alone explains ~98% of deal value** (range $55-$26,768, 487×). So the tool doesn't classify win probability — it ranks **value at risk**:

```
PRIORIDADE = p̂(produto, idade) × VALOR(produto, porte) × URGÊNCIA(idade)   [dollars, auditable]
SCORE      = percentile(PRIORIDADE vs. the 4,238 historically won deals) × 100   [0-100, the number shown]
CONFIANÇA  = min(completude, suporte)                                            [0-100, how much to trust it]
ESTADO     = decision tree(sem_precedente, SCORE≥95, CONFIANÇA<50)  →  Priorizar / Acompanhar / Qualificar / Revisão em lote
```

SCORE and CONFIANÇA never combine into one number — SCORE says what it's worth, CONFIANÇA says how much to trust that. PRIORIDADE in dollars is calculated and CSV-exported but never shown: `log(PRIORIDADE)` puts 87.3% of its variance on VALOR and 0.1% on `p̂`, so sorting by it is sorting by list price. Full derivation of every term in [docs/analise-lead-scoring.md](docs/analise-lead-scoring.md).

**2,089 open deals, every one scoreable** — including the 1,425 without an account (VALOR falls back to a neutral size prior) and the 500 in Prospecting (URGÊNCIA fixed at 0.47). That is every row the CSV marks Prospecting or Engaging: nothing is dropped, and nothing is relabelled on load. The 653 open ≥200 days (up to 423) are scored like any other — past the 138-day censoring boundary `p̂` reverts to the prior and URGÊNCIA hits its floor, so they sink on arithmetic rather than on a verdict we authored.

## What's NOT in the model, and why

Manager, office, sector, account revenue, employee count, company age, **and sales agent** — all tested, none significant (permutation p ≥ 0.262 on every one). Adding any of these to `p̂` would be noise dressed as rigor.

**Sector** is the one that gets proposed most often, because product×sector shows 4-5pp of raw spread. Two checks reject it and neither has ever flipped: the product×sector level collapses (`k = ∞`, backtest §3) and 5-fold CV says conditioning on it predicts *worse* than not conditioning (§6). Sector still feeds completude, the agent×sector fit, and the UI filters — never the score. **Don't reintroduce it** without new data that flips both checks.

**Agent fit** feeds the separate workload-redistribution suggestion only, never `p̂`/SCORE, and ships with its statistical caveat attached to every number it produces — precisely because there is no signal underneath. Two nulls are run (§12): shuffling agent labels answers "does the rep matter at all?" (p=0.588 product, 0.545 sector); a parametric bootstrap that preserves both main effects and denies only the interaction answers what the word *fit* actually claims (p=0.874 and 0.877, observed dispersion *below* simulated).

Permutation p-values use the add-one estimator `(1+c)/(B+1)` — floor 0.0005 at B=2000 — so the suite reports `p < 0.001` and never `p = 0.000`, which is impossible as a probability. Multiplicity is reported over the real family (the suite's 6 permutation tests) under Holm and Benjamini-Hochberg; none of the six comes close to the cut, with or without correction.

**Two historical numbers still circulate** — `sales_agent p=0.000` and `agent×product p=0.041`, reported between 2026-08-21 and 2026-08-29, when the load reclassified 653 stale deals as lost. Neither describes the current population, and neither was valid then: the purge only adds losses and lands concentrated (χ²=576.4, df=29, p<0.0001; −0.794 correlation between the share of a book purged and its resulting win rate — pipeline age read as closing skill), `0.000` is impossible as a probability, `0.041` came from the wrong null (see the two nulls above) and would not have survived Holm. Current values: **0.262** and **0.874**. Full account in `docs/analise-lead-scoring.md` §1.1.2 and the two 2026-08-29 entries in `process-log/decisions-log.md`. High p here means the data do not support putting the attribute in the score — not proof that no effect exists.

## Stack

FastAPI (no auth — public demo data, documented limitation) · React + TypeScript + Tailwind · pandas in-memory · `scoring/` as a pure Python package imported by API, CSV export, and the validation script, so the number shown = the number exported = the number validated. Details in [docs/architecture.md](docs/architecture.md).

## If you're extending this

- **Don't reintroduce auth as a partial measure.** It was removed by deletion, not a flag — see decisions-log. Sales agent/manager/office stay plain filters, same as product.
- **Don't recondition `p̂` by more attributes without cross-validating first.** Three refinement hypotheses (product×sector, per-product aging, per-product URGÊNCIA) were tested and all three made out-of-sample prediction worse — reproducible in `validation/backtest.py` sections 6-8.
- **`k` is derived, not frozen**, at every hierarchy level. If you add a new shrinkage level, derive its `k` the same way — don't hardcode one.
- **Never label an outcome the CRM didn't record.** `load_dataset` reads `deal_stage` and never writes it. Converting the 653 deals open ≥200 days to `Lost` and feeding them into calibration manufactures a 16.66pp spread in `p̂` across products (real: 0.00pp) and flips `sales_agent` from p=0.262 to p<0.001, because stalled deals cluster in a few books — 13 reps would take none of them. Backtest §10 measures that scenario on every run and §11 asserts it is not applied. If the business wants an abandonment rule, it belongs in the CRM as a recorded event, not in the loader.
- **PRIORIDADE (dollars) stays an internal/auditable value.** SCORE is the number a seller sees; don't wire PRIORIDADE back into the UI or into ESTADO's routing.
