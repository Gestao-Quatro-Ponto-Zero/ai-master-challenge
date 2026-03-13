# Deliverables

## Visão geral

O produto a ser entregue é um **dashboard analítico com atualização diária** e um **agente de diagnóstico integrado**. Juntos, respondem às perguntas da análise em tempo real e orientam o time de CS com planos de ação contextualizados.

---

## Deliverable 1 — Dashboard Analítico

### O que é

Interface visual que consolida os dados das cinco tabelas e apresenta os principais indicadores de churn da RavenStack.

### Atualização

Diária — os dados são processados e o dashboard é atualizado uma vez por dia.

### Seções do dashboard

| Seção | O que exibe |
|-------|-------------|
| **Visão geral de churn** | Churn rate atual, MRR perdido no período, evolução temporal |
| **Segmentação de risco** | Churn por indústria, país, canal de aquisição, plano e billing frequency |
| **Saúde financeira** | Distribuição de MRR/ARR das contas ativas vs. canceladas; downgrades recentes |
| **Engajamento com o produto** | Uso das features por segmento; features com maior correlação com retenção |
| **Experiência de suporte** | CSAT, tempo de resolução, escalações — comparativo entre contas ativas e churned |
| **Contas em risco** | Lista de contas ativas com score de risco calculado a partir de sinais múltiplos |

### Critérios de aceite

- Dados de todas as cinco tabelas representados
- Filtragem por segmento (indústria, país, plano, canal)
- Indicação clara do período de referência e da data da última atualização
- Legível por um executivo não-técnico

---

## Deliverable 2 — Agente de Diagnóstico

### O que é

Um agente de IA integrado ao dashboard, especializado em interpretar os dados exibidos e orientar o time de CS com diagnósticos e planos de ação.

### Capacidades

#### 2.1 Interpretação contextual dos números
- O agente explica o que os números do dashboard significam no contexto do negócio
- Exemplo: ao ver "churn de enterprise subiu 12% esse mês", o agente não apenas confirma o número — ele explica o que pode estar causando, com base nos dados disponíveis

#### 2.2 Análise histórica e identificação de padrões
- O agente compara o período atual com histórico para distinguir anomalias reais de variações normais
- Identifica tendências recorrentes (ex: sazonalidade, padrões por segmento)
- Detecta quebras de padrão que merecem atenção prioritária

#### 2.3 Diagnóstico de anomalias
- Quando um indicador sai do padrão esperado, o agente emite um alerta com:
  - Descrição da anomalia
  - Hipóteses prováveis baseadas nos dados cruzados
  - Urgência estimada (impacto financeiro potencial)

#### 2.4 Planos de ação contextualizados
- Para cada diagnóstico, o agente sugere planos de ação alinhados à lógica do negócio
- As sugestões são baseadas no playbook de CS da empresa (ver seção abaixo)
- Cada sugestão inclui exemplos concretos de execução

### Consulta ao playbook de CS

O agente tem acesso a uma base de conhecimento interna com as **estratégias de Customer Success da RavenStack**. Para cada tipo de problema identificado, o agente:

1. Recupera a estratégia de CS aplicável ao caso
2. Explica por que aquela estratégia é recomendada para o perfil da conta/problema
3. Fornece exemplos de como executar a ação (scripts de abordagem, ações no produto, etc.)

> Essa base de conhecimento é documentada em `/docs/02-product/04-playbook-cs.md` e deve ser mantida atualizada pelo time de CS.

### Interface de interação

- O agente é acessível via chat dentro do dashboard
- O usuário pode fazer perguntas em linguagem natural sobre qualquer número visível
- O agente pode ser invocado automaticamente quando uma anomalia é detectada

### Critérios de aceite

- O agente responde em português, com linguagem acessível ao CS e ao CEO
- As respostas citam os dados que sustentam o diagnóstico
- As sugestões de ação são específicas o suficiente para serem executadas sem ambiguidade
- O agente distingue o que é fato (dado) do que é hipótese (interpretação)
- O agente consulta o playbook de CS para toda sugestão de ação
