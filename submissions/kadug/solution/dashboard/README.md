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

Ele nao acessa os CSVs brutos e nao recalcula joins, score de risco ou regras de negocio.

## Escopo minimo

- Header executivo com escopo e caveats.
- KPIs de MRR/ARR em risco, contas priorizadas e causa candidata.
- Top 3 findings executivos.
- Segmentos em risco com evidencia de uso valid-window.
- Contas prioritarias com filtros de risco, owner e MRR minimo.
- Backlog de acoes por owner.
- Notas de data quality visiveis, com caminho para `solution/analysis/data_quality_report.md`.

## Limitacao operacional

O dashboard e um presentation adapter. Se Streamlit nao estiver disponivel, a solucao principal continua verificavel via README, exports e `solution/analysis/findings_summary.md`.
