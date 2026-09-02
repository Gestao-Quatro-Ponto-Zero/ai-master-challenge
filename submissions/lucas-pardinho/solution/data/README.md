# Dados

## Origem e licenca

- Dataset: [CRM Sales Predictive Analytics](https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics)
- Licenca declarada: CC0 1.0
- Pacote recebido para o challenge: `Predictive Analytics CRM Sales.zip`
- SHA-256 do ZIP: `74d535826330b616758ebb6bb393abf701a5126364a72fbe71003cb6a7a87a9c`
- Snapshot analitico: `2017-12-31`

## Arquivos brutos

Os arquivos de `raw/` sao preservados byte a byte. Seus hashes SHA-256 sao:

| Arquivo | Linhas | SHA-256 |
|---|---:|---|
| `accounts.csv` | 85 | `e5242324768a563fc632cddfed49a29acbbf2892b8a3c6453cc9650de9ae0358` |
| `metadata.csv` | 21 | `22b34e498d07e3d7f322afdbf81d70a5dc0a389792944e50ca2af86a3597f0af` |
| `products.csv` | 7 | `7c1c8cbbdb6d4c286902e1985eeb529a36366d6a43f43cd4a93c4b1da2a6eb84` |
| `sales_pipeline.csv` | 8.800 | `825ce8f6c32d4009548b468df3173d55a46fd73f2531f532c5459371dc52adf2` |
| `sales_teams.csv` | 35 | `aeff1272ebe196f5a27e3fc0578aa27abf48ed9ae461aa344fb95990e5ad8bd1` |

## Camada normalizada

`normalized/` e regenerada pelo pipeline. Ela corrige `GTXPro` para `GTX Pro`,
permitindo o join com o catalogo, e corrige `technolgy`/`Philipines` apenas para
exibicao. Cada transformacao e contada em `generated/data-quality.json`.

