# Dashboard Streamlit

Este dashboard e minimo e deve funcionar como camada de apresentacao dos achados principais. Ele nao deve conter a logica analitica principal.

## Como executar

Execute a partir da raiz do repositorio:

```powershell
python -m streamlit run ai-master-challenge/submissions/kadug/solution/dashboard/streamlit_app.py
```

Se os exports ainda nao existirem, gere primeiro:

```powershell
python ai-master-challenge/submissions/kadug/solution/analysis/build_exports.py
```

## Entradas

O app le apenas arquivos em `solution/exports/`:

- `executive_findings.csv`
- `risk_segments.csv`
- `priority_accounts.csv`
- `action_backlog.csv`
- `account_health.csv`
- `usage_growth_tests.csv` opcional, para mostrar crescimento bruto vs valid-window por segmento
- `root_cause_candidates.csv` opcional, para o grafico de causa raiz e impacto financeiro
- `churner_comparison.csv` opcional, mantido como evidencia auxiliar dos labels de churn

Ele nao acessa os CSVs brutos e nao recalcula joins, score de risco ou regras de negocio.

## Escopo de UX

- Visao CEO na primeira dobra: MRR/ARR em risco, churn label gap e top 10 contas criticas.
- Titulos "so what" que contam a conclusao antes da tabela.
- Grafico interativo de causa raiz candidata com impacto financeiro.
- Segmentos em risco com evidencia de uso valid-window.
- Mesa CS com filtros por risco, tier/plano, motivo, owner, due bucket, MRR minimo e busca.
- Watchlist de contas com `Next Best Action` operacional.
- Drill-down por conta com timeline de signup, subscription, suporte, uso e sinal de churn.
- Backlog de acoes por owner, prioridade, impacto esperado e status.
- Notas de data quality visiveis, com caminho para `solution/analysis/data_quality_report.md`.

## Modelo Atomic Design aplicado

- Atoms: labels, valores KPI, chips de risco/owner/status, dividers e celulas de tabela.
- Molecules: KPI card, finding block, action card, filter row e timeline item.
- Organisms: executive header, KPI grid, root-cause impact panel, risk segment explorer, CS watchlist, account drill-down, action backlog e data-quality notes.
- Template: single-page dashboard com progressive disclosure: Resumo Executivo -> Segmentos -> Mesa CS -> Backlog -> Confianca.

## Limitacao operacional

O dashboard e um presentation adapter. Se Streamlit nao estiver disponivel, a solucao principal continua verificavel via README, exports e `solution/analysis/findings_summary.md`.
