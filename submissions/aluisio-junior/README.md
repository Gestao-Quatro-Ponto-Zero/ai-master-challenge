# Churn Intelligence System (CIS)

## Sobre Mim

- **Nome:** Aluísio Junior  
- **LinkedIn:** https://www.linkedin.com/in/aluisio-riveiro-fagundes-junior-37610522/  
- **Challenge:** data-001-churn  



## Acesso

- **API (Swagger):** https://postoral-stan-salamandrine.ngrok-free.dev/docs  
- **Frontend (Lovable):** https://fivvecis.lovable.app


## Executive Summary

O sistema Churn Intelligence System (CIS) vai além de dashboards tradicionais, ele traz insights para tomada de decisão baseado em dados, combinando:

- Machine Learning (XGBoost)
- IA Generativa (LLM)
- Backend em FastAPI
- Frontend orientado a produto (Lovable)

Com o objetivo de transformar risco de churn em decisões executivas e ações práticas para equipe.

## Proposta de Valor

O CIS conecta:

- Predição (ML)
- Impacto financeiro (MRR em risco)
- Priorização (IA)
- Decisão (Executivos)
- Execução (Kanban)
- Aprovação (WhatsApp)

De dados → decisão → execução


## Arquitetura (Visão Geral)

Dados → Engenharia de Features → Modelo ML → Score de Risco → Insights com IA → Recomendações → Aprovação → Execução


## Estrutura do Backend (FastAPI)

Construi o backend em Python, rodando no VS Code, onde:
- data_service → ingestão  
- data_processing → construção do dataset  
- analysis → KPIs  
- ml_model → modelo preditivo  
- ai_engine → geração de insights  

### Endpoints

- `/kpis`
- `/churn-risk`
- `/dashboard-validation`
- `/insights`
- `/recommendations`
- `/kanban/projects`
- `/whatsapp/notify`
- `/whatsapp/webhook`
- `/ask-ai`


## Modelo de Machine Learning

- Modelo: XGBoost Classifier  

### Saídas:
- churn_score
- risk_level


## Decisão Importante: ML vs churn_30d

Durante o desenvolvimento, foi considerada a utilização de uma regra simples:

> churn = cliente sem atividade nos últimos 30 dias

### Problemas identificados:

- Distorção relevante nos indicadores de churn  
- Alto número de falsos positivos  
- Incapacidade de capturar comportamento real dos clientes  
- Regra rígida para um problema dinâmico  

### Decisão tomada:

Utilizar modelo de Machine Learning (XGBoost)

### Impacto:

- Maior precisão nas previsões  
- Redução de distorções  
- Melhor aderência ao comportamento real  
- Base mais confiável para decisão executiva  

## KPIs Executivos

- MRR Total  
- MRR Ativo  
- Receita em risco  
- ARPU  
- LTV (proxy)  

### Métrica principal:

MRR em risco = Receita em risco / Receita ativa


## Fluxo do Produto

1. Identificação de risco (ML)  
2. Cálculo de impacto financeiro  
3. Geração de insights (IA)  
4. Recomendações  
5. Aprovação (WhatsApp)  
6. Execução (Kanban)  


## Screenshots

### Telas do Produto
Local:
```
docs/screenshots/
```

- dashboard-overview.png  
- revenue-segmentation-shap.png  
- churn-risk-table.png  
- ai-insights.png  
- recommendations.png  
- kanban-execution.png  
- whatsapp-approval.png  
- chat-ai.png  
- settings-module.png  


### API
- api-docs-overview.png  
- api-docs-kpis.png  
- api-docs-ask-ai.png  


##  Process Log (Decisões Reais + Correções)

Este projeto foi desenvolvido com apoio de IA (ChatGPT, Gemini e Lovable), mas exigiu diversas decisões críticas e correções manuais.

### 1. Definição de churn

A IA inicialmente tratava o churn de forma simplificada, considerando todos como ativos e totalizando todo o MRR e total de clientes.

Problema:
Mistura entre churn histórico e churn preditivo.

Correção:
Separação clara entre:
- churn histórico  
- churn preditivo  

### 2. Uso de churn_30d (erro conceitual)

A abordagem baseada em regra (30 dias sem atividade) foi considerada.

Problema:
- Distorção dos números  
- Classificação incorreta de clientes  
- Baixa confiabilidade  

Decisão:
Substituir por modelo de Machine Learning, porém os dados são estaticos e não há uma variação para treino da ML, pois a db é "pequena".


### 3. Segmentação de receita

A IA não priorizava impacto financeiro. Tem um disclaimer informando que deve tratar com pesos diferentes clientes com faturamento de R$ 50 de clientes com faturamento de R$ 5.000.

Problema:
Clientes com baixo valor sendo priorizados e igualando ações para tomada de decisão e prioridades.

Correção:
Implementação de classificação ABC (Pareto) baseada em MRR. Identificando quais são os clientes que geram 70% da receita e estão com probabilidade de churn.


### 4. Cálculo de LTV

A IA sugeriu cálculo completo, considerando os totais, sendo que aquele cliente que já churnou não pode ser mais considerado e gera um distorção nos dados de LTV.

Problema:
Dataset sintético não suporta cálculo real.

Correção:
Uso de LTV como proxy simplificado.


### 5. SHAP (explicabilidade)

A IA apresentou todos os fatores de churn.

Problema:
Excesso de informação para o usuário final.

Correção:
Foco nos principais drivers de churn para entendimento da causa e direcionar para ações efetivas.


### 6. Insights com IA

A IA gerava respostas genéricas sem considerar as features estabelecidas.

Correção:
Ajuste de prompts incluindo:
- impacto financeiro  
- risco  
- segmentação  

## Limitações (MVP)

- Dataset sintético com poucos dadso para treno da ML 
- LTV simplificado  
- WhatsApp simulado  
- Sem autenticação  
- SHAP com instabilidade visual  

## Ferramentas usadas

Ferramenta	Para que usou
ChatGPT 	Construção do banckend
Gemini	    Configuração da API Google e integração com frontend (conversa com IA)
Lovable 	Construção e disponibilidade do frontend
VS Code     Ambiente de desenvolvimento para backend e scripts Python
FastAPI     Construção da API REST e endpoints do sistema
Ngrok       Exposição da API local para acesso externo (frontend e testes)
GitHub      Hospedagem do repositório e submissão do challenge |
Kaggle API  Download e integração do dataset

## Próximos Passos

- Integrar DB real  
- Integração por webhook com WhatsApp  
- Autenticação  
- Pipeline em tempo real  
- Retreinamento do modelo  

## Evidências

- Código  
- Screenshots  
- API  
- Logs  
- Conversas com IA

## Screenshots — Process Log

- 01_business_understanding_churn_problem.png  
Definição do problema de churn e entendimento do contexto de negócio.

- 02_solution_architecture_definition.png  
Definição da arquitetura da solução em alto nível.

- 03_revenue_segmentation_strategy_abc.png  
Estratégia de segmentação de receita baseada no modelo ABC.

- 04_dashboard_kpi_definition.png  
Definição dos KPIs para o dashboard executivo.

- 05_data_modeling_and_feature_strategy.png  
Estratégia de modelagem de dados e engenharia de features.

- 06_churn_definition_discussion_bias.png  
Discussão sobre definição de churn e possíveis vieses.

- 09_api_data_integration_strategy.png  
Estratégia de integração de dados via API.

- 10_dashboard_chart_design_mockup.png  
Definição visual e estrutural dos gráficos do dashboard.

- 11_backend_main_api_structure.png  
Estrutura do backend utilizando FastAPI.

- 12_data_pipeline_raw_dataset.png  
Pipeline inicial com dataset bruto e estrutura de dados.

- 13_ai_engine_prompt_design.png  
Engenharia de prompts para geração de insights com IA.

- 14_analysis_churn_segmentation_logic.png  
Lógica analítica para segmentação de churn.

- 15_data_processing_pipeline.png  
Pipeline de processamento e transformação dos dados.

- 16_data_service_kaggle_integration.png  
Integração com dataset externo via Kaggle.

- 17_ml_model_training_pipeline.png  
Pipeline de treinamento do modelo de Machine Learning.

- 18_shap_explainability_analysis.png  
Análise de explicabilidade utilizando SHAP.

- 19_shap_output_visualization.png  
Visualização dos resultados de explicabilidade do modelo.

- 20_gemini_integration_test.png  
Testes de integração com IA generativa (Gemini).

## Screenshots — Produto/Docs

- 01_dashboard_overview_kpis.png  
Visão geral do dashboard com KPIs executivos.

- 02_dashboard_revenue_segmentation_shap.png  
Segmentação de receita combinada com explicabilidade (SHAP).

- 03_churn_risk_accounts_table.png  
Tabela de clientes com maior risco de churn e impacto financeiro.

- 04_insights_ai_executive_summary.png  
Insights gerados por IA com foco em decisão.

- 05_insights_features_importance_kpis.png
Visualização dos principais indicadores e da importância das variáveis que influenciam o modelo preditivo.

- 06_recommendations_list.png
Recomendações acionáveis baseadas em risco e impacto.

- 07_kanban_execution_board
Execução das ações em formato Kanban.

- 08_whatsapp_approval_flow.png 
Fluxo de aprovação de ações via WhatsApp.

- 09_ai_chat_assistant.png  
Interface de interação com IA para análise adicional.

- 10_settings_executives_management.png 
Módulo de configurações (usuários e integrações).

- 11_api_docs_overview.png  
Visão geral da documentação da API no Swagger, com todos os endpoints disponíveis para auditoria e integração.

- 12_api_kpis_endpoint.png  
Execução do endpoint de KPIs, exibindo as métricas executivas consolidadas do sistema.

- 13_api_ask_ai_request.png  
Exemplo de requisição ao endpoint de IA, demonstrando como perguntas executivas são enviadas ao sistema.

- 14_api_ask_ai_response.png  
Resposta gerada pelo endpoint de IA com interpretação executiva baseada nos dados reais do sistema.

- 15_api_ask_ai_response.png  
Exemplo adicional de resposta do endpoint de IA, evidenciando a capacidade de análise contextual e suporte à decisão.


## Conversas com IA

https://chatgpt.com/share/69c4a259-fa40-83e9-a2cc-845e26df9c85  
https://chatgpt.com/share/69c73346-aa2c-83e9-ae31-eff17f27097c  


## Conclusão

A IA acelerou o desenvolvimento, mas não substituiu decisões técnicas e insights que adquiri ao longo da carreira, temos que direcionar para ter o resultado real.

Os principais ganhos vieram de:

- Correção de distorções  
- Foco em impacto financeiro  
- Transformação de análise em ação  
