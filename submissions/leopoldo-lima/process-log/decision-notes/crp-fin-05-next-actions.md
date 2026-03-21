# CRP-FIN-05 — Próximas ações diversificadas

**Data:** 2026-03-21

## Problema
Uma única frase por banda (`high` / `medium` / `low`) repetia-se no ranking.

## Solução
- `actions_by_context` em `config/scoring-rules.json`: listas por **won**, **lost**, **open_stale**, **open_high**, **open_medium**, **open_low**.
- `src/scoring/engine.py`: `_pick_contextual_next_action` escolhe com `hash(opportunity_id) % len(lista)` para variar por oportunidade; mantém fallback para `actions` legados.

## Regras de seleção
1. `Won` / `Lost` → listas dedicadas.  
2. Aberto com `pipeline_age_bucket == stale` → `open_stale` (se existir).  
3. Caso contrário → banda pelo score (`open_high` / `open_medium` / `open_low`).

## Verificação
- `python -m pytest -q`
