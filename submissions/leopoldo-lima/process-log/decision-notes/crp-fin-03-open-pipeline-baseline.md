# CRP-FIN-03 — Baseline de score para oportunidades abertas

**Data:** 2026-03-21

## Problema
`Won` tinha peso estrutural **+25**, dominando o topo do ranking e reduzindo utilidade para **priorização do pipeline aberto**.

## Hipótese
Reduzir o bónus de `Won` e subir ligeiramente `Prospecting` / `Engaging` para que deals **abertos fortes** disputem o topo com critério operacional.

## Alteração em `config/scoring-rules.json`
| Estágio | Antes | Depois |
|---------|-------|--------|
| Prospecting | -5 | +2 |
| Engaging | +5 | +10 |
| Won | +25 | +10 |
| Lost | -30 | -30 |

## Efeito esperado
- Menos domínio artificial de `Won` no top N.
- Oportunidades `Engaging` bem preenchidas continuam banda alta (validado por `tests/test_scoring_v2_features.py`).

## Verificação
- `python -m pytest -q tests/test_scoring_v2_features.py tests/test_scoring_engine.py`
