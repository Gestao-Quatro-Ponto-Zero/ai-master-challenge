# Dados

Fonte: [CRM Sales Predictive Analytics](https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics) (Kaggle, CC0).

```
data/
├── raw/      os 5 arquivos originais, sem alteração (accounts, products, sales_teams, sales_pipeline, metadata)
├── clean/    saída de clean.py — nunca editar à mão
├── scored/   saída do score (outra etapa)
└── clean.py  limpeza reproduzível
```

Rodar (Python 3.10+, `pandas` e `numpy`):

```bash
python solution/data/clean.py
```

O script falha com erro se alguma checagem de integridade quebrar (ex.: a origem mudar).

## Regras de limpeza

| # | Problema na origem | Regra aplicada | Linhas afetadas |
|---|---|---|---|
| 1 | Produto `GTXPro` no pipeline não existe no catálogo (lá é `GTX Pro`) | Renomeado para `GTX Pro` | 1.480 deals |
| 2 | Setor `technolgy` (erro de digitação) | Renomeado para `technology` | 12 contas |
| 3 | Espaços nas pontas dos textos | Removidos em todas as colunas de texto | — |
| 4 | Deals abertos sem conta (`account` vazio) | Mantidos como vazio + coluna `has_account`. Não se inventa conta | 1.425 dos 2.089 abertos (68%): 1.088 Engaging e 337 Prospecting. Nenhum deal fechado está sem conta |
| 5 | Prospecting sem `engage_date` | Mantido vazio: o deal ainda não foi engajado. Sem idade calculável | 500 deals (todos os Prospecting) |
| 6 | `close_date` e `close_value` vazios nos abertos | Mantidos vazios (o deal não fechou) | 2.089 deals |
| 7 | 5 vendedores do time sem nenhum deal (Carl Lin, Carol Thompson, Elizabeth Anderson, Mei-Mei Johns, Natalya Ivanova) | Mantidos em `sales_teams.csv`; não aparecem em `deals.csv` | 5 vendedores |
| 8 | `subsidiary_of` vazio para contas independentes | `parent_company` = empresa-mãe ou a própria conta | 70 contas |

Checagens que o script garante: `opportunity_id` único; todo produto, vendedor e conta do pipeline existe no cadastro (após a regra 1); todo deal fechado tem conta, `engage_date` e `close_date`; `close_date >= engage_date`; Won tem `close_value > 0` e Lost tem `close_value = 0`; nenhuma data passa da data de referência.

## Data de referência ("hoje")

**2017-12-31** — o último dia com qualquer registro no dataset (último `close_date`; o último `engage_date` é 2017-12-27). Toda idade de deal aberto é contada a partir daí. Justificativa em `analysis/findings.md`.

## Arquivos em `clean/`

- `accounts.csv`, `products.csv`, `sales_teams.csv`, `sales_pipeline.csv`: tabelas originais limpas.
- `deals.csv`: uma linha por oportunidade, já com vendedor, manager, escritório, produto, preço de tabela e dados da conta. Colunas derivadas:
  - `is_open` (Prospecting/Engaging), `won` (1 Won, 0 Lost, vazio se aberto), `has_account`
  - `cycle_days` = `close_date − engage_date` (só fechados)
  - `days_since_engage` = data de referência − `engage_date` (só Engaging)
  - `list_price` (preço de tabela do produto), `price_ratio` = `close_value / list_price` (só Won)
  - `revenue_band`, `employees_band`: tercis calculados sobre as 85 contas (receita: até 692,19 / até 2.173,98 / acima, em milhões de USD; funcionários: até 1.428 / até 4.540 / acima)
  - `parent_company`, `close_quarter`
- `cleaning_report.json`: contagens, cortes dos tercis e período coberto.
