# Documentacao — Dados

## Fonte

**Dataset:** [CRM Sales Predictive Analytics](https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics)
**Licenca:** CC0 (dominio publico)
**Acesso:** API Kaggle (`kagglehub`) ou CSVs locais em `solution/data/`

---

## Tabelas

### sales_pipeline.csv (8.800 registros)

Tabela central. Cada linha e uma oportunidade de venda.

| Campo | Tipo | Descricao |
|-------|------|-----------|
| opportunity_id | string | ID unico do deal |
| sales_agent | string | Nome do vendedor |
| product | string | Produto sendo vendido |
| account | string | Nome da conta cliente (VAZIO em 1.425 deals ativos) |
| deal_stage | string | Prospecting, Engaging, Won, Lost |
| engage_date | date | Data de inicio da negociacao (vazio se Prospecting) |
| close_date | date | Data de fechamento (vazio se ativo) |
| close_value | number | Valor de fechamento (0 se Lost, vazio se ativo) |

**Distribuicao por stage:**
- Won: 4.238 (48%)
- Lost: 2.473 (28%)
- Engaging: 1.749 (20%)
- Prospecting: 340 (4%)

**Deals ativos (Engaging + Prospecting):** 2.089

### accounts.csv (~85 registros)

| Campo | Tipo | Descricao |
|-------|------|-----------|
| account | string | Nome da conta |
| sector | string | Setor (technology, retail, medical, etc.) |
| year_established | number | Ano de fundacao |
| revenue | number | Receita anual |
| employees | number | Numero de funcionarios |
| office_location | string | Localizacao |
| subsidiary_of | string | Empresa-mae |

### products.csv (7 registros)

| Campo | Tipo | Descricao |
|-------|------|-----------|
| product | string | Nome do produto |
| series | string | Linha (GTK, GTX, MG) |
| sales_price | number | Preco de venda |

**Produtos e precos:**
| Produto | Preco |
|---------|-------|
| MG Special | $55 |
| GTX Basic | $550 |
| GTX Pro | $4,821 |
| MG Advanced | $3,393 |
| GTX Plus Basic | $1,096 |
| GTX Plus Pro | $5,482 |
| GTK 500 | $26,768 |

### sales_teams.csv (35 registros)

| Campo | Tipo | Descricao |
|-------|------|-----------|
| sales_agent | string | Nome do vendedor |
| manager | string | Gestor |
| regional_office | string | Escritorio regional |

**Escritorios:** Central, West, East, Southeast, Northeast, Midwest, Southwest, South, Northwest, Pacific

---

## Dados derivados (scored_deals.json)

Gerado pelo `scoring_engine.py`. Contem:

| Secao | Conteudo |
|-------|----------|
| `active_deals` | 2.089 deals ativos com scores, sinais e acoes |
| `closed_deals` | 6.711 deals fechados (Won + Lost) para referencia |
| `agent_stats` | Estatisticas por vendedor (taxa, deals, valor) |
| `refs` | Taxas de referencia (global, por produto, por vendedor) |
| `deciles` | Resultado do backtest por decis |

Tamanho: ~7.5 MB. Tempo de geracao: ~5 segundos.

---

## Observacoes sobre qualidade dos dados

1. **68% dos deals ativos nao tem conta** — Campo `account` vazio em 1.425 de 2.089 deals. Isso limita sinais de relacionamento.

2. **Deals em Prospecting nao tem engage_date** — 340 deals sem data de inicio. Urgencia recebe score fixo 0.4.

3. **close_value nem sempre corresponde ao preco do produto** — Alguns deals Won tem close_value diferente do sales_price. O motor usa sales_price (disponivel para todos) como proxy de valor.

4. **Sem dados de interacao** — Nao ha registro de emails, ligacoes ou reunioes. O motor trabalha apenas com dados de pipeline.
