# Data sources (raw)

## Fonte oficial
Os arquivos abaixo em `data/` sao a **source of truth** do projeto neste estagio:

- `accounts.csv`
- `products.csv`
- `sales_teams.csv`
- `sales_pipeline.csv`
- `metadata.csv`

## Regras
- Nao renomear colunas na camada raw.
- Nao corrigir valores nesta etapa; apenas ler e descrever.
- Qualquer normalizacao ocorre em camada posterior e deve ser rastreada.

## Inspecao reproduzivel

```powershell
python .\scripts\inspect_data.py
```

Artefatos gerados:
- `artifacts/data-validation/raw-schema-summary.json`
- `artifacts/data-validation/raw-schema-summary.md`
