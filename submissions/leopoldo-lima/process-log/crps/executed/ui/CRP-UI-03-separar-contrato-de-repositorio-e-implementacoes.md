# CRP-UI-03 — Separar contrato de repositório e implementações

## Objetivo
Tirar o contrato OpportunityRepository do arquivo da implementação mock e preparar DI limpa.

## Escopo
- Extrair interface para src/application/contracts/OpportunityRepository.ts
- Criar MockOpportunityRepository em arquivo próprio
- Criar factory/provider para selecionar implementação
- Eliminar acoplamento ao singleton exportado diretamente

## Entregáveis
- src/application/contracts/OpportunityRepository.ts
- src/infrastructure/repositories/mock-opportunity-repository.ts
- src/infrastructure/repositories/repository-factory.ts
- docs/REPOSITORY_STRATEGY.md

## Critérios de aceite
- Presentation não importa implementação concreta
- Existe um ponto único para trocar mock por API
