# Submissão — Fer Paes — Challenge Support Redesign

## Sobre mim

**Nome:** Fernando Paes  
**LinkedIn:** [(Fernando Paes)](https://www.linkedin.com/in/ferpaes/)

**Challenge escolhido:** Support Tickets System

**Resultado final:** https://tech-support-ticket-ufba.bolt.host/llm-models ( operador@gmail.com / Operador@123 )

**Video do processo:** https://drive.google.com/file/d/1I7u3XAVG-yoGOt51ddj0zwvzYR1hQoo8/view?usp=drive_link

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
User Input
↓
Ticket Orchestrator (LLM)
↓
Category Detection
↓
Routing Engine
↓
Specialized Agents
├ Technical Support Agent
├ Billing Agent
├ Refund Agent
└ Product Inquiry Agent


Além disso, foi proposto um **dashboard operacional**, permitindo visualizar:

- gargalos de atendimento
- tempo médio de resolução
- tickets por categoria
- tickets que exigem intervenção humana

---

# Abordagem

O processo seguiu quatro etapas principais.

## 1. Exploração do dataset

Foram analisados dois datasets:

### Dataset 1
Contém métricas operacionais:
- canal de atendimento
- prioridade
- status do ticket
- tempo de resolução
- satisfação do cliente

### Dataset 2
Contém dados textuais:

- 48.000 tickets
- descrição completa dos problemas
- classificação em oito categorias

Essa análise permitiu identificar padrões de problemas e distribuição dos tickets.

---

## 2. Identificação de padrões

Alguns padrões identificados:

Problemas técnicos recorrentes:

- falhas após atualização de software
- problemas de bateria
- falhas de conectividade
- perda de dados

Também foi identificado que muitos usuários:

- tentam resolver o problema antes de abrir ticket
- seguem manuais ou fóruns
- realizam reset de fábrica

---

## 3. Avaliação da qualidade dos dados

Foram identificadas algumas inconsistências importantes:

- tickets fechados sem solução clara
- satisfação do cliente inconsistente
- campo de resolução aparentemente com placeholders

Isso indica que o dataset é adequado para **classificação de problemas**, mas não para aprendizado direto de soluções.

---

## 4. Modelagem da solução

Com base nesses insights, foi proposta uma arquitetura baseada em:

- classificação automática de tickets
- orquestração via LLM
- agentes especializados
- integração com sistemas internos

O objetivo é reduzir triagem manual e acelerar resolução.

---

# Resultados / Findings

## Distribuição por canal

Grande parte dos tickets chega por:

- chat
- redes sociais

Seguidos por:

- telefone
- email

Isso indica que automação conversacional pode gerar impacto relevante na operação.

---

## Problemas técnicos dominam o volume

Grande parte dos tickets está relacionada a:

- hardware
- acesso a contas
- conectividade
- erros após atualização

Esses tipos de problema são bons candidatos para automação parcial.

---

## Inconsistência nas métricas de satisfação

Foi observado que alguns tickets não resolvidos receberam nota máxima de satisfação.

Isso sugere possível problema de coleta ou modelagem do indicador.

---

## Dataset ideal para classificação

O dataset textual com 48k tickets é adequado para:

- classificação automática
- roteamento inteligente
- triagem inicial

---

# Recomendações

## 1. Classificação automática de tickets

Utilizar modelos de NLP para classificar tickets automaticamente.

Benefícios:

- redução da triagem manual
- melhor distribuição de workload
- menor tempo de resposta

---

## 2. Implementar roteamento inteligente

Criar um orquestrador responsável por direcionar tickets para:

- agentes automáticos
- especialistas humanos

---

## 3. Automatizar problemas recorrentes

Automação recomendada para:

- reset de senha
- troubleshooting básico
- consultas de produto
- status de pedidos

---

## 4. Criar dashboards operacionais

Monitorar:

- gargalos de atendimento
- tempo médio de resolução
- distribuição por categoria
- taxa de automação

---

# Limitações

Algumas limitações foram identificadas durante a análise.

## Dataset incompleto

O dataset não contém:

- procedimentos realizados pelo suporte
- solução aplicada ao problema

Isso limita o treinamento de sistemas de resposta automática.

---

## Possível natureza sintética dos dados

Algumas distribuições parecem artificialmente balanceadas, o que pode não refletir uma operação real.

---

## Falta de contexto operacional

Não há informação sobre:

- SLA
- regras de atendimento
- estrutura organizacional do suporte

Esses fatores impactam diretamente o design do sistema.

---

# Process Log — Como usei IA

## Ferramentas usadas

| Ferramenta | Uso |
|---|---|
| ChatGPT | análise exploratória e estruturação da solução |
| NotebookLM | exploração inicial dos datasets |
| GPT | análise textual do dataset de tickets |
| Bolt.new | desenvolvimento do protótipo de sistema multiagente |

---

# Workflow

O processo foi conduzido em ciclos iterativos.

## 1. Análise exploratória

Os datasets foram analisados utilizando IA para identificar padrões nos tickets.

---

## 2. Identificação de padrões

A IA foi utilizada para:

- identificar padrões recorrentes
- agrupar problemas semelhantes
- gerar mapas mentais do dataset

---

## 3. Modelagem da solução

A partir dos insights obtidos, foi definida uma arquitetura baseada em:

- orquestrador de tickets
- agentes especializados
- classificação automática

---

## 4. Prototipação

A arquitetura foi transformada em escopo técnico e protótipo utilizando ferramentas de desenvolvimento assistido por IA.

---

# Onde a IA errou e como corrigi

Durante a análise inicial, a IA sugeriu utilizar o dataset para treinar respostas automáticas.

Após análise manual, foi identificado que o dataset não contém as soluções aplicadas pelo suporte, apenas descrições de problemas.

Por esse motivo, o dataset foi utilizado apenas para **classificação de tickets**.

---

# O que eu adicionei que a IA sozinha não faria

A principal contribuição humana foi:

- identificar limitações estruturais do dataset
- definir arquitetura de orquestração multiagente
- separar fluxos de suporte entre **produto e comercial**
- modelar agentes especializados

---

# Evidências

Evidências do processo incluem:

- screenshots das interações com IA
- transcrição do processo de análise
- histórico de desenvolvimento do protótipo
- registros de prompts utilizados

Arquivos disponíveis em:
process-log/

---

**Submissão enviada em:** 16/03/2026
