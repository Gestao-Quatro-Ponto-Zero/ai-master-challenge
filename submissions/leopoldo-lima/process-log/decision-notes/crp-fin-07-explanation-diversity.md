# CRP-FIN-07 — Diversidade contextual das explicações

**Data:** 2026-03-21

## Padrão anterior
Frases técnicas repetidas e pouca rotação por oportunidade.

## Implementado
- `ctx.pick` com múltiplas variantes; escolha estável por `hash(opportunity_id)`.
- Matriz em `docs/EXPLANATION_NARRATIVE.md`.
- Terceira variante explícita para mensagens `Won` na narrativa.

## Verificação
- Revisão manual em detalhes com ids diferentes; `pytest` sem regressão.
