# Narrativa das explicações do score (CRP-FIN-07)

## Objetivo
Evitar que todos os detalhes pareçam gerados pelo mesmo template: variações controladas por **hash do id** da oportunidade e por **tipo de linha** (estágio, valor, idade de pipeline, qualidade de dados).

## Matriz de cenários (UI detalhe)

| Cenário | Sinais típicos | Comportamento da narrativa |
|---------|----------------|----------------------------|
| Aberto forte | `Engaging`, valor alto, pipeline `fresh` | Frases de reforço de momentum e valor. |
| Aberto estagnado | `stale`, score médio/baixo | Ênfase em tempo no pipeline e urgência. |
| Ganho | `Won` | Várias variantes de «negócio ganho» sem mudar o número (+N). |
| Perdido | `Lost` | Duas variantes de perda / prioridade baixa. |
| Dados fracos | engage ausente, sem conta | Riscos e penalidades em linguagem de cadastro/CRM. |

## Onde está no código
- `src/api/explanation_narrative.py` — `humanize_score_explanations`, `ctx.pick(...)`.
- `src/api/view_models.py` — `build_explanation_view(..., opportunity_id, deal_stage)`.

## Limitações
- Linhas do motor ainda não mapeadas caem no texto original (auditabilidade).
- Não se inventam fatores: só reformulação do que o motor já escreveu.
