# Submissão — Fer Paes — Challenge Support Redesign

## Sobre mim

**Nome:** Fernando Paes  
**LinkedIn:** [(adicione seu link)  ](https://www.linkedin.com/in/ferpaes/)
**Challenge escolhido:** Support System Redesign

---

# Executive Summary

A análise dos datasets de suporte revelou gargalos principalmente relacionados à triagem manual de tickets e à falta de classificação eficiente das solicitações. O dataset indica padrões recorrentes de problemas técnicos, especialmente após atualizações de software, além de inconsistências entre resolução registrada e satisfação do cliente.

Com base nesses insights, propus um sistema de suporte baseado em **orquestração de agentes de IA**, responsável por classificar automaticamente tickets, direcionar solicitações para especialistas e sugerir respostas baseadas em histórico de casos similares.

A solução inclui um **orquestrador de tickets, agentes especializados por categoria e dashboards operacionais**, permitindo reduzir tempo de triagem, acelerar resolução e melhorar a experiência do cliente.

---

# Solução

A solução proposta consiste em um **sistema de suporte baseado em arquitetura multiagente**, capaz de automatizar triagem, classificação e roteamento de tickets.

## Fluxo do sistema

1. Cliente abre ticket via canal (chat, email, telefone ou social)
2. Um **orquestrador de IA** analisa o conteúdo do ticket
3. O ticket é classificado automaticamente
4. O sistema direciona para um **agente especializado**
5. O agente pode:
   - sugerir resposta automática
   - executar automações
   - escalar para humano quando necessário

## Arquitetura proposta
