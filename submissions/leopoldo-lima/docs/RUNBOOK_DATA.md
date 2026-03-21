# Runbook de dados

Este runbook documenta como um avaliador reproduz ingestao, validacao e score sem passos magicos.

## Pre-requisitos
- Python 3.11+
- Dependencias instaladas:

```powershell
python -m pip install -e .[dev]
```

## Localizacao dos datasets
Arquivos esperados em `data/`:
- `accounts.csv`
- `products.csv`
- `sales_teams.csv`
- `sales_pipeline.csv`
- `metadata.csv`

## Passo a passo (ordem recomendada)

1) Inspecionar schema raw:

```powershell
python scripts/inspect_data.py
```

Saidas:
- `artifacts/data-validation/raw-schema-summary.json`
- `artifacts/data-validation/raw-schema-summary.md`

2) Validar contrato estrutural:

```powershell
python scripts/validate_data_contract.py
```

3) Validar regras de qualidade:

```powershell
python scripts/validate_data_quality.py
```

4) Validar integridade referencial:

```powershell
python scripts/validate_referential_integrity.py
```

Saida:
- `artifacts/data-validation/referential-integrity-report.json`

5) Gerar dicionario vivo de dados:

```powershell
python scripts/generate_data_dictionary.py
```

Saidas:
- `docs/DATA_DICTIONARY.md`
- `artifacts/data-validation/metadata-coverage-report.json`

6) Executar smoke de normalizacao e features:

```powershell
python -m pytest -q tests/test_normalization.py tests/test_features.py
```

7) Gerar evidencia consolidada raw -> core -> gold -> score:

```powershell
python scripts/run_data_runbook.py
```

Saidas:
- `artifacts/data-validation/runbook-data-evidence.json`
- `artifacts/data-validation/runbook-data-evidence.md`

## Atalho unico via task runner

```powershell
python scripts/tasks.py runbook-data
```

Para executar o fluxo completo com gates:

```powershell
python scripts/tasks.py build
```

## Como interpretar warnings
- Warnings de integridade referencial (ex.: valores em dimensao nao usados no fato) **nao** bloqueiam automaticamente.
- Erros de contrato/qualidade/integridade bloqueante devem falhar o pipeline e ser corrigidos antes da demo.
- Alias de normalizacao (ex.: `GTXPro -> GTX Pro`) sao esperados e auditaveis em `config/normalization-map.json`.

## Limitacoes conhecidas do dataset
- `account` pode vir vazio em parte do pipeline (tratado como opcional no contrato).
- A normalizacao semantica depende do mapa de aliases; novos aliases exigem atualizacao de configuracao.
- Sem historico temporal completo, o scoring permanece heuristico.

## Troubleshooting
- `ModuleNotFoundError: No module named 'src'`:
  - execute comandos a partir da raiz do repo.
- Falha em `validate_data_contract.py`:
  - revisar colunas obrigatorias e mapa de normalizacao.
- Falha em `validate_referential_integrity.py`:
  - verificar se houve quebra de join em `account`, `product` ou `sales_agent`.
