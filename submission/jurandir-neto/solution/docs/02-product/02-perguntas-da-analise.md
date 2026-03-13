# Perguntas da Análise

Estas são as perguntas que o produto deve ser capaz de responder. Elas guiam tanto a análise exploratória quanto o comportamento do agente de diagnóstico.

---

## Perguntas primárias (obrigatórias)

### 1. O que está causando o churn?

- Quais reason codes dominam os eventos de churn?
- O feedback textual dos clientes confirma ou contradiz os reason codes?
- Existe correlação entre alta taxa de erros em features e posterior cancelamento?
- Contas que fizeram downgrade antes de cancelar têm padrão diferente das que cancelaram diretamente?
- O suporte tem papel no churn? Tickets escalados ou com baixo CSAT precedem cancelamentos?

### 2. Quais segmentos estão mais em risco?

- O churn se concentra em alguma indústria específica?
- Há países ou regiões com churn desproporcional?
- Contas adquiridas por determinado canal têm maior tendência de cancelamento?
- Contas mensais churnam mais do que contas anuais?
- Contas que vieram de trial têm comportamento diferente das que entraram direto?
- Qual faixa de MRR concentra mais churn em volume? E em valor financeiro?

### 3. O que a empresa deveria fazer?

- Quais ações têm maior potencial de impacto na retenção, considerando o MRR em risco?
- Existem contas ativas com perfil similar ao das que já churnearam? (identificação de risco futuro)
- Quais features, quando adotadas, estão associadas à retenção? (product-led retention)
- Há gargalos no suporte que, se resolvidos, reduziriam o churn?

---

## Perguntas secundárias (aprofundamento)

- O CEO disse que "o uso da plataforma cresceu" — isso é verdade para todos os segmentos ou é uma média que esconde heterogeneidade?
- Existe um padrão temporal no churn? (sazonalidade, aceleração recente)
- Features beta têm maior taxa de erros? Isso está correlacionado com churn?
- Qual é o tempo médio entre o primeiro sinal de risco (downgrade, ticket escalado, queda de uso) e o churn efetivo? Há uma janela de intervenção?

---

## Critérios de qualidade das respostas

Cada resposta deve:

- Ser baseada em dados cruzados entre pelo menos duas tabelas
- Apresentar o número que sustenta a afirmação
- Distinguir correlação de causalidade quando relevante
- Ser compreensível para o CEO (sem jargão técnico desnecessário)
- Considerar o peso financeiro (MRR/ARR) — não apenas volume de contas
