# Process Log — AI-Assisted Development

Este documento detalha como a IA foi utilizada durante o desenvolvimento e quais decisões foram tomadas manualmente.


##  Uso de IA

A IA foi utilizada para:

- Estruturação inicial do backend
- Sugestões de arquitetura
- Apoio na modelagem do churn
- Geração de insights (Gemini)


##  Principais erros e correções

### 1. Definição de churn

Erro:
Uso de regra simplificada (churn_30d)

Correção:
Substituição por modelo de Machine Learning


### 2. Kaggle hardcoded

Erro:
Caminho fixo no código

Correção:
Uso de variável de ambiente


### 3. Insights genéricos

Erro:
IA gerava respostas vagas

Correção:
Refinamento de prompts com foco em impacto financeiro


### 4. SHAP pouco utilizável

Erro:
Excesso de informação

Correção:
Foco nos principais drivers


### 5. Frontend não auditável

Erro:
Dependência apenas do Lovable

Correção:
Inclusão do frontend no repositório


## Evolução do sistema

O sistema evoluiu de:

- Modelo analítico simples  
→ para  
- Sistema completo de decisão com execução


## Conclusão

A IA acelerou o desenvolvimento, mas as decisões críticas foram tomadas manualmente com base em:

- coerência de negócio  
- qualidade dos dados  
- impacto financeiro  