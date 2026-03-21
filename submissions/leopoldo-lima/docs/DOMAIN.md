# DOMAIN

## Escopo deste repositório
Este repositório opera como challenge pack orientado por CRPs, com foco em execução auditável e submissão forte.

## Objetivo do domínio
Guiar a entrega de uma solução verificável para o challenge, com duas saídas obrigatórias:
- solução funcional (ou equivalente validado pelo challenge)
- process log robusto, com rastreabilidade do uso de IA e revisão humana

## Entidades principais
- `CRP`: unidade de trabalho incremental
- `Evidência`: prova verificável de execução (artefato, log, captura, diff)
- `Process Log`: registro de decisões, prompts, erros de IA, correções humanas e iterações
- `Submissão`: material final consolidado para PR

## Modelos canônicos de dados (raw/core/gold)

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

## Mapeamento entre camadas
- `raw_opportunity_to_core()`: aplica normalização semântica e converte representação raw para canônica.
- `core_opportunity_to_gold()`: gera feature set de consumo para score e detalhamento.

Implementação em `src/domain/models.py`.

## Regras de domínio
1. Nenhum CRP é concluído sem evidência de process log.
2. Nenhum CRP é concluído sem rastreabilidade do uso de IA.
3. Nenhum CRP é concluído com output genérico não verificado.
4. Toda saída deve ser reproduzível por avaliador externo.

## Fronteiras
- O domínio deste repo é governança de execução e submissão.
- Componentes técnicos do produto podem existir, mas precisam sempre de vínculo com evidência e validação humana.

## Resultado esperado
Uma trilha de execução que reduza risco de desclassificação e maximize auditabilidade da submissão.
