# Matriz de decisão: estratégia do Challenge 002

## Regra

Escala de 1 a 5. A nota ponderada ordena alternativas, mas não supera veto crítico de evidência, segurança ou conformidade.

| Critério | Peso |
|---|---:|
| Evidência verificável | 30% |
| Impacto operacional e econômico | 25% |
| Segurança e controle humano | 20% |
| Viabilidade no time budget | 15% |
| Diferenciação para a G4 | 10% |

## Alternativas

| Alternativa | Evidência | Impacto | Segurança | Viabilidade | Diferenciação | Nota | Veto |
|---|---:|---:|---:|---:|---:|---:|---|
| Resposta autônoma em produção | 1,0 | 4,0 | 1,0 | 2,0 | 3,0 | 2,1 | Sim |
| Roteamento automático por confiança | 4,0 | 4,0 | 3,0 | 4,0 | 4,0 | 3,8 | Não, se simulado |
| Copiloto de triagem em shadow mode | 5,0 | 3,5 | 5,0 | 5,0 | 4,5 | **4,6** | Não |
| Dashboard operacional isolado | 3,0 | 2,0 | 5,0 | 5,0 | 2,0 | 3,4 | Não |

## Decisão

Construir um **copiloto de triagem em shadow mode**, com:

1. classificação e confiança calibrada;
2. abstenção abaixo do threshold;
3. decisão humana como padrão;
4. modo de automação apenas simulado;
5. categorias sensíveis sempre humanas;
6. mascaramento de PII antes da inferência;
7. log de auditoria sem texto bruto;
8. kill switch determinístico.

O Dataset 2 sustenta a prova técnica. O Dataset 1 sustenta apenas data audit, volumetria e limitações. Nenhum resultado é apresentado como validação para a G4.

## Critério de threshold

O threshold foi escolhido na validação:

| Threshold | Cobertura | Acurácia no subconjunto coberto |
|---:|---:|---:|
| 0,70 | 74,9% | 94,9% |
| 0,75 | 70,1% | 96,0% |
| 0,80 | 64,5% | 97,1% |

O protótipo usa **0,75 como referência inicial de shadow mode**. No teste final independente, a cobertura foi 69,7% e a acurácia nos cobertos foi 96,6%. A decisão produtiva ainda exige dados do domínio alvo, custo por erro, calibração externa e aprovação operacional.
