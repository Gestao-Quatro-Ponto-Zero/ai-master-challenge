# CRP-D05 — Modelos canônicos de domínio: raw, core e gold

## Objetivo
Parar de trafegar CSV cru pelo sistema.

## Modelo proposto

### Raw
- `RawAccount`
- `RawProduct`
- `RawSalesTeam`
- `RawOpportunity`
- `RawMetadataRow`

### Core
- `Account`
- `Product`
- `SalesAgent`
- `Opportunity`

### Gold
- `OpportunityFeatureSet`
- `OpportunityScore`
- `OpportunityDetailView`

## Saídas
- `docs/DOMAIN.md`
- `docs/DATA_CONTRACT.md`
- schemas/DTOs/tipos
- atualização de `ADR`

## Definition of Done
- nenhuma camada superior depende diretamente de nome cru de CSV
- os modelos canônicos estão tipados
- o mapeamento raw -> core está explícito

## Prompt para o Cursor
```text
Implemente o CRP-D05: modelos canônicos de domínio.

Tarefa:
1. Criar modelos de domínio em 3 camadas:
   - raw
   - core
   - gold
2. Definir modelos mínimos:
   - RawAccount, RawProduct, RawSalesTeam, RawOpportunity, RawMetadataRow
   - Account, Product, SalesAgent, Opportunity
   - OpportunityFeatureSet, OpportunityScore, OpportunityDetailView
3. Criar docs/DOMAIN.md e docs/DATA_CONTRACT.md.
4. Documentar claramente o mapeamento raw -> core.
5. Atualizar ADR e LOG.md.

Critérios:
- Modelos coesos
- Nada de CSV cru na camada de produto
- Tipagem forte e nomes de domínio legíveis
```
