# Process Log — AI Master Challenge

## Objetivo

Construir um Churn Intelligence System que combine analytics, machine learning, IA generativa e visão de produto para ajudar executivos a identificar risco de churn, priorizar contas e transformar insights em ação.

---

## Ferramentas Utilizadas

- **ChatGPT** — desenho de arquitetura, revisão de KPIs, debugging, definição de produto e apoio na documentação
- **VS Code** — desenvolvimento e implementação do backend
- **FastAPI** — camada de API
- **XGBoost** — modelo de previsão de churn
- **Gemini** — geração de insights e interpretação executiva
- **Lovable** — prototipação e construção do frontend
- **ngrok** — exposição temporária da API para integração com frontend

---

## Fluxo de Desenvolvimento

1. Revisão do desafio e reposicionamento da solução como um **sistema de decisão**, não apenas um dashboard.
2. Análise do dataset (RavenStack) e identificação de um problema crítico: churn histórico, status atual e churn preditivo não podem ser tratados da mesma forma.
3. Construção do backend em FastAPI, separando claramente:
   - ingestão
   - processamento
   - análise
   - modelo de ML
   - orquestração de IA
4. Treinamento do modelo XGBoost para geração de:
   - `churn_score`
   - `risk_level`
5. Correção de métricas financeiras que estavam distorcidas por uso de média ao invés de receita agregada.
6. Redefinição dos KPIs:
   - MRR total
   - MRR ativo
   - MRR inativo
   - receita em risco
   - variações de ARPU
   - LTV como proxy
7. Reestruturação da segmentação de receita para separar:
   - churn histórico por faixa
   - churn preditivo por faixa
   - MRR ativo vs inativo
8. Ajuste da tabela Top 10 para refletir apenas **contas ativas**, priorizando:
   - nível de risco
   - MRR
   - churn score
   - classificação ABC
9. Integração do Gemini para gerar insights e recomendações executivas.
10. Estruturação do produto em módulos:
   - Dashboard Executivo
   - Churn Risk
   - Recomendações
   - Kanban
   - Aprovação via WhatsApp (simulada)

---

## Onde a IA Errou e Como Corrigi

### 1. Lógica de receita
A IA sugeriu uso de média de MRR como base executiva. Corrigi para utilizar receita agregada por conta.

### 2. Contas ativas vs churnadas
O dataset não fornecia um status confiável. Defini uma lógica operacional baseada em histórico de churn e snapshot analítico.

### 3. ARPU e LTV
As fórmulas iniciais misturavam bases inconsistentes. Corrigi o ARPU e tratei o LTV como proxy transparente.

### 4. Ranking Top 10
Inicialmente misturava contas ativas e inativas. Corrigi para refletir apenas contas ativas com priorização executiva.

### 5. Consistência do dashboard
Havia inconsistência entre gráficos e tabelas. Padronizei todas as visualizações com a mesma base de cálculo.

---

## O Que Foi Além da IA

- Interpretação executiva dos KPIs
- Separação clara entre churn histórico e preditivo
- Priorização baseada em impacto financeiro
- Transformação de análise em fluxo operacional
- Consistência entre métricas, gráficos e tabelas

---

## Decisões de Design

- Uso de churn histórico como base conservadora para LTV
- Uso de churn preditivo apenas em contas ativas
- Foco em contas ativas para visão executiva
- Priorização do Top 10 baseada em impacto financeiro
- Enquadramento do sistema como plataforma de **proteção de receita**

---

## Evidências

- Screenshots da API
- Screenshots do dashboard
- Histórico do Git
- Fluxo de uso de IA (design e debugging)
- Estrutura final do código
