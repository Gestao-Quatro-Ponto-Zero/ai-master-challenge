# Solução JourneyGraph

## Propósito

Esta pasta concentrará a implementação reproduzível do JourneyGraph. Na Fase 0, contém somente a estrutura de trabalho, a documentação operacional e a declaração da stack planejada.

## Arquitetura planejada

A solução seguirá um fluxo auditável: fontes brutas imutáveis → auditoria e contrato validado → event log temporal → análises descritivas e temporais → journey mining → grafo NetworkX → watchlist → aplicação com revisão humana. A arquitetura está planejada e ainda não foi implementada.

## Ambiente-alvo

- Python 3.11 ou superior;
- dependências abertas e executáveis localmente;
- nenhuma API paga como requisito do núcleo;
- artefatos derivados gerados por scripts rastreáveis.

A execução ainda não está disponível. As versões das dependências serão fixadas somente após a validação do ambiente na fase técnica apropriada.

## Pré-requisito de dados

A implementação futura dependerá da presença e validação conjunta dos cinco datasets oficiais:

- `ravenstack_accounts.csv`;
- `ravenstack_subscriptions.csv`;
- `ravenstack_feature_usage.csv`;
- `ravenstack_support_tickets.csv`;
- `ravenstack_churn_events.csv`.

Nenhuma etapa analítica será iniciada com fonte ausente ou substituída silenciosamente.

## Ordem planejada de construção

1. auditoria;
2. event log;
3. diagnóstico;
4. survival;
5. journey mining;
6. grafo;
7. watchlist;
8. aplicação.

## Política de reprodutibilidade

Cada transformação futura deverá ter entrada, saída e parâmetros explícitos; logs, testes e reconciliações deverão permitir repetir o resultado a partir das fontes oficiais. Dados brutos não serão sobrescritos, e artefatos derivados deverão registrar sua linhagem.

## Estado atual

Não há código analítico, scripts executáveis, modelos, grafos ou aplicação nesta fase.
