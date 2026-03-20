# Agent 00 — Orchestrator

## Papel
Decomposição do problema de churn e sequenciamento dos agents 01–05.

## Contexto do problema
A RavenStack reporta churn crescente. Temos 5 datasets interconectados:
- `ravenstack_accounts.csv` — perfil das contas
- `ravenstack_subscriptions.csv` — histórico de planos
- `ravenstack_feature_usage.csv` — uso de features por subscription
- `ravenstack_support_tickets.csv` — chamados de suporte
- `ravenstack_churn_events.csv` — eventos de cancelamento confirmados

## Sequência de execução

1. **Agent 01 — EDA**: Perfilar cada tabela individualmente (shape, dtypes, missing, distribuições)
2. **Agent 02 — Cross-table**: Joins via DuckDB para construir visão unificada por conta
3. **Agent 03 — Hypothesis**: Gerar e validar hipóteses de churn com dados cruzados
4. **Agent 04 — Predictive**: Treinar LightGBM, calcular SHAP values, gerar churn score
5. **Agent 05 — Report**: Consolidar findings em relatório executivo com recomendações priorizadas

## Questões-chave a responder

- Qual segmento de conta tem maior taxa de churn?
- Qual padrão de uso de features prediz churn?
- O suporte (tickets) tem correlação com churn?
- Qual é o churn score por conta hoje?
- Quais as 3 ações com maior ROI para reduzir churn?

## Critérios de sucesso

- AUC-ROC ≥ 0.80 no modelo preditivo
- Top-3 hipóteses validadas com dados
- Relatório executivo com recomendações priorizadas por impacto
