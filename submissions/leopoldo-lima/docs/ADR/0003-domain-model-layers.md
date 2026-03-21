# ADR-0003 — Modelagem canônica em camadas raw/core/gold

## Status
Aceito

## Contexto
O fluxo de dados estava tipado, mas sem separação explícita entre representação raw, modelo de negócio e modelo para consumo analítico/produto.

## Decisão
Adotar três camadas de modelo:
- **Raw**: espelha CSV sem semântica adicional (`RawAccount`, `RawProduct`, `RawSalesTeam`, `RawOpportunity`, `RawMetadataRow`)
- **Core**: entidades canônicas de negócio (`Account`, `Product`, `SalesAgent`, `Opportunity`)
- **Gold**: visão pronta para feature/score/detalhe (`OpportunityFeatureSet`, `OpportunityScore`, `OpportunityDetailView`)

Também foi formalizado o mapeamento:
- `raw_opportunity_to_core()`
- `core_opportunity_to_gold()`

## Consequências
### Positivas
- reduz acoplamento de camadas superiores ao CSV cru
- explicita transformação raw -> core -> gold
- melhora legibilidade para API/scoring e auditoria de submissão

### Negativas
- mais código de manutenção entre camadas
- exige testes para evitar regressão de mapeamento

## Guardrails
- não consumir CSV diretamente fora da camada raw
- qualquer novo campo deve declarar em qual camada entra e como é transformado
