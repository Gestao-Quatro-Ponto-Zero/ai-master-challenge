# Raw contract

## Escopo
Contrato raw dos CSVs oficiais sem renomeacao de coluna na ingestao.

## Arquivos cobertos
- `accounts.csv`
- `products.csv`
- `sales_teams.csv`
- `sales_pipeline.csv`
- `metadata.csv`

## O que o contrato registra
Para cada arquivo:
- coluna
- tipo inferido
- nulabilidade
- cardinalidade aproximada
- observacoes

## Camada raw no codigo
- `src/raw/reader.py`
  - `load_raw_rows(filename)`
  - `inspect_raw_file(filename)`
  - `OFFICIAL_RAW_FILES`

## Snapshot atual
Gerado por:

```powershell
python .\scripts\inspect_data.py
```

Saidas:
- `artifacts/data-validation/raw-schema-summary.json`
- `artifacts/data-validation/raw-schema-summary.md`

## Nota de submissao
Este contrato sustenta reprodutibilidade da trilha de dados e evita interpretacao criativa precoce antes das fases de qualidade/normalizacao/modelagem.
