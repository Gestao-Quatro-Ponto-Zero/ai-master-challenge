# Arquitetura — Challenge 001 Diagnóstico de Churn

## Visão geral
Pipeline de 6 agents sequenciais orquestrados via Claude Code.

## Agents

| Agent | Arquivo | Responsabilidade |
|-------|---------|-----------------|
| 00 | orchestrator.md | Decomposição do problema e sequenciamento |
| 01 | 01_eda_agent.py | EDA e perfilamento das 5 tabelas |
| 02 | 02_cross_table_agent.py | Joins e análise cross-table via DuckDB |
| 03 | 03_hypothesis_agent.py | Geração e validação de hipóteses de churn |
| 04 | 04_predictive_agent.py | Modelo LightGBM + SHAP |
| 05 | 05_report_agent.py | Relatório executivo em Markdown/HTML |

## Fluxo de dados
```
accounts + subscriptions + feature_usage + support_tickets + churn_events
→ Agent 01 (EDA)
→ Agent 02 (Cross-table via DuckDB)
→ Agent 03 (Hipóteses validadas nos dados)
→ Agent 04 (Churn score por conta + feature importance)
→ Agent 05 (Relatório executivo + recomendações priorizadas)
```

## Stack técnica
- **DuckDB**: joins performáticos entre CSVs — nunca Pandas merge em datasets grandes
- **LightGBM**: modelo de churn (velocidade + acurácia + suporte nativo a categorias)
- **SHAP**: explainability do modelo — feature importance por predição individual
- **Plotly**: visualizações interativas (distribuições, feature importance, churn score)
- **Quarto**: relatório executivo HTML/PDF com visualizações embutidas

## Por que esta arquitetura
Cada agent tem responsabilidade única (SRP). O process log é gerado automaticamente
a cada execução. A separação em arquivos permite rastrear exatamente qual IA gerou
qual parte da solução — diferencial crítico no processo seletivo G4.

## Estrutura de dados (inputs)

| Arquivo | Chave | Registros estimados |
|---------|-------|-------------------|
| ravenstack_accounts.csv | account_id | ~500 |
| ravenstack_subscriptions.csv | subscription_id → account_id | ~5.000 |
| ravenstack_feature_usage.csv | subscription_id | ~25.000 |
| ravenstack_support_tickets.csv | account_id | ~2.000 |
| ravenstack_churn_events.csv | account_id | ~600 |

## Estrutura de outputs

| Output | Localização | Gerado por |
|--------|------------|-----------|
| Perfis EDA | process-log/entries/ | Agent 01 |
| Master DataFrame | solution/data/ | Agent 02 |
| Hipóteses validadas | process-log/entries/ | Agent 03 |
| Modelo + SHAP | solution/data/ | Agent 04 |
| Relatório executivo | docs/executive_report.md | Agent 05 |
| Dashboard | solution/dashboard/ | Agent 05 |
