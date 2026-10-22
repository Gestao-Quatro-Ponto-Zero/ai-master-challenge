# Diagnóstico de Churn — RavenStack (Challenge 001)

Diagnóstico do aumento de churn de uma plataforma SaaS B2B fictícia (RavenStack), com as 5 tabelas cruzadas, um modelo preditivo e uma ferramenta de priorização para o time de Customer Success.

> A submissão completa, com resumo executivo, achados, recomendações, limitações e process log, está em **[SUBMISSION.md](SUBMISSION.md)**.

## Principais achados

- **O churn subiu:** a taxa trimestral de primeiro churn foi de 18,5% para 32,2% (4T23 → 4T24), em todos os segmentos, com US$ 2,91 mi de MRR perdido.
- **Nenhum comportamento separa quem sai de quem fica:** satisfação, tickets, uso, erros e downgrades são iguais entre os grupos.
- **Só a idade da conta prevê churn:** AUC de 0,645 num período que o modelo não viu. Contas novas saem mais.
- **A medição está quebrada:** três fontes dão 22%, 62% e 70% de churn, e 52,9% do uso registrado é anterior ao cadastro da conta.
- **Ads retém mais:** 41% das contas seguem sem churn em 365 dias, contra 26% nos demais canais.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `data/` | Os 5 CSVs do dataset (ver `data/README.md`) |
| `sql/` | `build_accounts_master.sql`: tabelas brutas e tabela mestre em PostgreSQL/Supabase |
| `src/` | Scripts Python do pipeline |
| `outputs/` | Tabela mestre, evidências, modelo, previsões e fila de CS |
| `docs/` | Relatório para o CEO, painel executivo e dicionário de dados |

## Como rodar

```bash
pip install -r requirements.txt
bash run_all.sh
```

O `run_all.sh` roda, em ordem:

| Script | Gera |
|---|---|
| `src/evidence.py` | `evidence.csv` (números do relatório, com fonte e teste) e `at_risk_accounts.csv` |
| `src/build_monthly_trend.py` | `monthly_trend.csv` |
| `src/feature_channel_analysis.py` | `feature_trends.csv` e `channel_churn_analysis.csv` |
| `src/churn_model.py` | `model_*.csv` e `model_scores_2025-01-01.csv` |
| `src/cs_risk_tool.py` | `cs_fila_acoes.csv`, `cs_gatilhos.csv`, `cs_tickets_contexto.csv` e `cs_regras.csv` |

A tabela mestre (`outputs/accounts_master.csv`) é gerada por `sql/build_accounts_master.sql` no PostgreSQL/Supabase. Uma cópia já vem no repositório, para que os scripts rodem sem banco de dados.

## Painel interativo

O diagnóstico fase a fase (Fases 0 a 10, incluindo o modelo e a ferramenta de CS) está em: https://claude.ai/artifact/HNmaQcLqcSEXyxg6wfyKgA

## Dados

Dataset **RavenStack: Synthetic SaaS Dataset (Multi-Table)**, de **River @ Rivalytics**, licença MIT-like. Os dados são totalmente sintéticos.
