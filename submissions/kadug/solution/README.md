# Solucao

Esta pasta concentra os artefatos da solucao do Challenge 001.

## Estrutura

- `analysis/`: analytics core reproduzivel, camada limpa, relatorios de validacao e copia local do DQ report.
- `exports/`: contratos canonicos em CSV/JSON usados pelo relatorio e pelo dashboard.
- `dashboard/`: dashboard minimo em Streamlit que consome apenas os exports.
- `requirements.txt`: dependencias Python.

## Como reproduzir

Execute a partir da raiz do repositorio:

```powershell
python ai-master-challenge/submissions/kadug/solution/analysis/build_exports.py
```

Validacao sem rebuild:

```powershell
python ai-master-challenge/submissions/kadug/solution/analysis/build_exports.py --validate-only
```

## Contratos principais

- `exports/account_health.csv`: uma linha por `account_id`.
- `exports/risk_segments.csv`: agregacao por banda de risco.
- `exports/priority_accounts.csv`: fila priorizada de contas acionaveis.
- `exports/action_backlog.csv`: acoes por dono, prioridade, gatilho, impacto e confianca.
- `exports/executive_findings.json`: achados executivos com evidencia e rastreabilidade.

O dashboard e o README final nao recalculam joins nem score de risco; eles leem esses contratos.
