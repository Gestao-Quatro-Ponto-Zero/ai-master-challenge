# CRP-FIN-04 — Features e penalidades para pipeline aberto

**Data:** 2026-03-21

## Alterações (`config/scoring-rules.json`)
| Bloco | Mudança |
|--------|---------|
| `pipeline_age.weights` | `fresh` +6, `active` +3, `stale` -8, `unknown` -5 (mais separação recência vs. estagnação). |
| `data_quality.missing_engage_date_penalty` | 0 → **-5** (abertos sem engage fiável). |
| `open_operational` (novo) | `low_value_threshold` 2000 + `prospecting_no_traction_penalty` -4 quando `Prospecting` + valor baixo + bucket `active`/`stale`. |

## Código
- `src/scoring/engine.py`: `_apply_open_operational_signals` aplicado após `_apply_data_quality` (só `version >= 2`).

## Trade-offs
- Penalidade “ticket baixo + tempo no pipeline” pode baixar prospecções fracas sem desqualificar todas as pequenas contas (só com maturidade `active`/`stale`).

## Verificação
- `python -m pytest -q`
