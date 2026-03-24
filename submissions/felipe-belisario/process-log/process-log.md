# Process Log — Felipe Belisário — Challenge 003

## Ferramentas usadas

| Ferramenta | Para que |
|---|---|
| Claude.ai | Análise exploratória, decisões metodológicas, planejamento das 5 etapas |
| Claude Code | Build completo do backend e frontend, iterações de UX, debugging |
| Gemini API (gemini-2.5-flash) | Copilot integrado no produto final |

## Conversa completa com a IA

Link público da sessão de trabalho no Claude.ai — contém todas as decisões metodológicas, erros identificados e correções aplicadas ao longo do projeto:

https://claude.ai/share/b63a4dfa-68a4-4c5c-966e-bd7f74b7caeb

## Onde a IA errou — e como corrigi

| Erro da IA | Correção aplicada |
|---|---|
| P25 como limiar de urgência (9 dias) | Corrigi para P50 — temperatura mede desvio do ciclo esperado, não velocidade relativa |
| CRM Health Score de 61,3% | Corrigi para 83,8% — separando problemas reais de comportamentos estruturalmente corretos |
| Fabricava wr_sector quando ausente | Removi — dado inventado é pior que ausência de informação |
| Scores concentrados entre 5.5–7.5 | Corrigi normalizando por percentil dentro do pipeline |
| Redistribuições usando tier atual | Corrigi para usar WR histórico real dos combos Agente x Produto |

## O que eu adicionei que a IA sozinha não faria

- Mapear impacto financeiro (\,2M) antes de qualquer modelo
- Questionar sistematicamente as features óbvias — produto, manager e região são ruído
- Identificar que o problema é também de alocação de deals, não só priorização
- Não fabricar sector WR — honestidade estatística que a IA não priorizou
- Separar problemas reais de dados de comportamentos estruturalmente corretos
