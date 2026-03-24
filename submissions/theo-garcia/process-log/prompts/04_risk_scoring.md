# Fase 4 — Risk Scoring (por que rule-based > ML)

## O que aconteceu com o ML
Random Forest com 34 features cross-table. F1 Score (5-fold CV): 0.098.

A tentação: tunar hiperparâmetros, testar XGBoost, SMOTE, feature selection — até o modelo "parecer bom".

## Minha decisão: não forçar
F1 = 0.098 não é um bug. É um dado. As features comportamentais (uso, tickets, satisfação) são quase idênticas entre churned e retidos. O churn neste dataset é driven por fatores exógenos — budget, competitive pressure, pricing decisions — que não aparecem nas features.

## A alternativa: risk scoring baseado nos achados
Se os segmentos (indústria, canal, MRR tier) TÊM poder discriminativo comprovado na Parte 3, posso construir um score BASEADO NELES:

| Fator | Peso | Justificativa |
|---|---|---|
| Indústria | 25% | DevTools = 31% vs Cyber = 16% (2x) |
| Canal aquisição | 25% | Eventos = 30% vs Partners = 15% (2x) |
| MRR tier | 25% | Mid-market = 26%, 55% da base |
| Escalações | 15% | Sinal de problemas graves |
| Histórico churn | 10% | Já cancelou = pode cancelar de novo |

## Validação
| Nível | Churn real | Contas |
|---|---|---|
| Baixo | 11% | — |
| Moderado | 18% | — |
| Alto | 44% | — |
| Crítico | **50%** | — |

**4.5x de separação** (Baixo vs Crítico). Muito superior ao RF (F1=0.098).

## Por que isso importa
Rule-based > ML quando: (a) ML não funciona nas features disponíveis, (b) a análise segmentada revela drivers claros, (c) o score precisa ser explicável pro CEO. Checou as três caixas.
