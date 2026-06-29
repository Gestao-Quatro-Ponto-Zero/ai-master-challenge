# Analise

Esta pasta contem o analytics core reproduzivel do diagnostico RavenStack.

## Comando unico

Execute a partir da raiz do workspace que contem `data/raw/ravenstack` e `ai-master-challenge/`:

```powershell
python ai-master-challenge/submissions/kadug/solution/analysis/build_exports.py
```

Para validar exports ja gerados sem reconstruir:

```powershell
python ai-master-challenge/submissions/kadug/solution/analysis/build_exports.py --validate-only
```

## Entradas

- `data/raw/ravenstack/ravenstack_accounts.csv`
- `data/raw/ravenstack/ravenstack_subscriptions.csv`
- `data/raw/ravenstack/ravenstack_feature_usage.csv`
- `data/raw/ravenstack/ravenstack_support_tickets.csv`
- `data/raw/ravenstack/ravenstack_churn_events.csv`

Os CSVs brutos nao sao modificados.

## Saidas

- `clean/`: camada limpa tipada, com `feature_usage_row_id`, `usage_in_subscription_window_flag`, `account_churn_flag` e `has_churn_event` preservados no fluxo.
- `data_quality_report.md`: copia local do relatorio de qualidade usado pela submissao.
- `preflight_report.json`: runtime Python/Streamlit e pastas exigidas.
- `clean_validation_report.json`: schema, joins, duplicidade de usage id, uso fora da janela de assinatura e conflito de labels de churn.
- `export_validation_report.json`: contratos dos exports canonicos.
- `analysis_summary.json`: resumo de execucao.

## Exports gerados

Arquivos em `../exports/`:

- `account_health.csv` / `.json`
- `risk_segments.csv` / `.json`
- `priority_accounts.csv` / `.json`
- `action_backlog.csv` / `.json`
- `executive_findings.csv` / `.json`
- `churner_comparison.csv` / `.json` como artefato auxiliar de analise.
- `usage_growth_tests.csv` / `.json` como teste da contradicao "uso cresceu".
- `root_cause_candidates.csv` / `.json` como ranking de causas candidatas com caveat causal.
- `findings_summary.md` como sintese reproduzivel para o relatorio executivo.

## Regras analiticas

- Joins de muitos lados sao agregados antes de entrar em `account_health`.
- Uso de produto usa `usage_in_subscription_window_flag` para metricas validas.
- `usage_id` nao e tratado como chave unica; `feature_usage_row_id` e a chave de ingestao.
- `account_churn_flag` e `has_churn_event` ficam separados.
- Score de risco e deterministico, por bandas: Critical `>=80`, High `60-79`, Medium `35-59`, Low `<35`.
