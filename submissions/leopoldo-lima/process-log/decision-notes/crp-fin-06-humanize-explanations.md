# CRP-FIN-06 — Humanização das explicações do score

**Data:** 2026-03-21

## Objetivo
Substituir mensagens tipo motor («deal_stage X contribuiu +N») por linguagem comercial em PT, mantendo fidelidade ao sinal (sem inventar fatores novos).

## Implementação
- `src/api/explanation_narrative.py`: `humanize_score_explanations` + mapeamento linha a linha (`_map_line`, `_map_risk`) com `ctx.pick()` para variações.
- `build_explanation_view` e `build_detail_view` passam `opportunity_id` e `deal_stage`.
- `src/api/app.py`: `scoreExplanation` obtido a partir de `explanation` já humanizada no `build_detail_view`.

## Verificação
- `python -m pytest -q`
