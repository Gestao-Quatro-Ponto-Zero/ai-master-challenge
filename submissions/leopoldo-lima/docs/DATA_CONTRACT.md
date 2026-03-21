# Contrato de dados do challenge pack

## Objetivo
Este contrato descreve os datasets CSV presentes em `data/`, suas colunas obrigatórias, chaves e validações estruturais mínimas para manter o repositório auditável.

Fonte de verdade do contrato: `contracts/repository-data-contract.json`.

## Datasets cobertos
- `accounts.csv`
- `products.csv`
- `sales_teams.csv`
- `sales_pipeline.csv`
- `metadata.csv`

## Chaves e relacionamentos
- Chaves primárias:
  - `accounts.csv.account`
  - `products.csv.product`
  - `sales_teams.csv.sales_agent`
  - `sales_pipeline.csv.opportunity_id`
- Chaves estrangeiras em `sales_pipeline.csv`:
  - `sales_agent -> sales_teams.csv.sales_agent`
  - `product -> products.csv.product`
  - `account -> accounts.csv.account`

## Regras de validação mínimas
- Presença de todos os arquivos listados no contrato.
- Presença de colunas obrigatórias por dataset.
- PK sem vazio e sem duplicidade onde definida.
- Integridade referencial das FKs de `sales_pipeline.csv`.
- Não vazio para campos críticos de pipeline:
  - `opportunity_id`
  - `sales_agent`
  - `product`
  - `deal_stage`

### Anomalias conhecidas no snapshot
- `sales_pipeline.csv.account` possui valores vazios em parte das linhas e por isso é tratado como campo opcional no modelo atual (`Optional[str]`).
- A validação de integridade referencial para `account` só é aplicada quando o valor está preenchido.
- `sales_pipeline.csv.product` contém alias `GTXPro`; a validação aplica normalização para `GTX Pro` antes de checar FK em `products.csv`.

## Modelo de domínio Python (snapshot atual)
Tipos definidos em `src/domain/models.py` por camada:
- **Raw**: `RawAccount`, `RawProduct`, `RawSalesTeam`, `RawOpportunity`, `RawMetadataRow`
- **Core**: `Account`, `Product`, `SalesAgent`, `Opportunity`
- **Gold**: `OpportunityFeatureSet`, `OpportunityScore`, `OpportunityDetailView`

Mapeamento explícito:
- `raw_opportunity_to_core()`
- `core_opportunity_to_gold()`

## Execução da validação

```powershell
python .\scripts\validate_data_contract.py
```

Ou via task runner:

```powershell
python .\scripts\tasks.py contract
python .\scripts\tasks.py build
```

## Limitações atuais
- O contrato cobre estrutura e relacionamentos básicos; validações de regra de negócio (ex.: consistência temporal por `deal_stage`) ficam para CRPs de qualidade/dados seguintes.
- Tipos estão representados como strings no snapshot atual para evitar inferência incorreta sem normalização explícita.
