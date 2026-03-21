# Data dictionary

Gerado automaticamente de `metadata.csv` + schema real dos CSVs. Divergências ficam explícitas na seção de cobertura.

## accounts

| Campo | Descrição (metadata) | Tipo inferido | Nulável |
|---|---|---|---|
| account | Company name | string | False |
| sector | Industry | string | False |
| year_established | Year Established | int | False |
| revenue | Annual revenue (in millions of USD) | float | False |
| employees | Number of employees | int | False |
| office_location | Headquarters | string | False |
| subsidiary_of | Parent company | string | True |

## products

| Campo | Descrição (metadata) | Tipo inferido | Nulável |
|---|---|---|---|
| product | Product name | string | False |
| series | Product series | string | False |
| sales_price | Suggested retail price | int | False |

## sales_teams

| Campo | Descrição (metadata) | Tipo inferido | Nulável |
|---|---|---|---|
| sales_agent | Sales agent | string | False |
| manager | Respective sales manager | string | False |
| regional_office | Regional office | string | False |

## sales_pipeline

| Campo | Descrição (metadata) | Tipo inferido | Nulável |
|---|---|---|---|
| opportunity_id | Unique identifier | string | False |
| sales_agent | Sales agent | string | False |
| product | Product name | string | False |
| account | Company name | string | True |
| deal_stage | Sales pipeline stage (Prospecting > Engaging > Won / Lost) | string | False |
| engage_date | Date in which the "Engaging" deal stage was initiated | string | True |
| close_date | Date in which the deal was "Won" or "Lost" | string | True |
| close_value | Revenue from the deal | int | True |

## metadata

| Campo | Descrição (metadata) | Tipo inferido | Nulável |
|---|---|---|---|
| Table | MISSING_IN_METADATA | string | False |
| Field | MISSING_IN_METADATA | string | False |
| Description | MISSING_IN_METADATA | string | False |

## Cobertura metadata vs schema

### accounts
- missing_in_metadata: []
- extra_in_metadata: []

### products
- missing_in_metadata: []
- extra_in_metadata: []

### sales_teams
- missing_in_metadata: []
- extra_in_metadata: []

### sales_pipeline
- missing_in_metadata: []
- extra_in_metadata: []

### metadata
- missing_in_metadata: ['Description', 'Field', 'Table']
- extra_in_metadata: []
