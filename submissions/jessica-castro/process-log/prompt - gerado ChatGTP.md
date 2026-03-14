Prompt para Claude Code

Quero que você me ajude a construir um projeto chamado DealSignal.

DealSignal é um AI-powered deal rating engine que ajuda times de vendas a priorizar oportunidades com base em probabilidade de fechamento e impacto financeiro esperado.

A solução deve ser software funcional, não apenas análise exploratória.

O objetivo é que um vendedor abra a aplicação e consiga ver claramente:

quais oportunidades priorizar hoje.

Dataset

Estou utilizando o dataset:

CRM Sales Predictive Analytics

Arquivos CSV disponíveis:

accounts.csv

account

industry

revenue

employees

location

parent_company

products.csv

product

series

sales_price

sales_teams.csv

sales_agent

manager

office

sales_pipeline.csv

opportunity_id

account

product

sales_agent

deal_stage

engage_date

close_date

close_value

A tabela central é sales_pipeline, que se conecta às demais.

Objetivo do sistema

Para cada oportunidade o sistema deve calcular:

win_probability

deal_rating

expected_revenue

Fórmula principal:

Expected Revenue = win_probability × close_value

Isso permitirá priorizar oportunidades por impacto financeiro esperado.

Metodologia analítica

O modelo deve seguir uma abordagem inspirada em modelos de risco de crédito utilizados por fintechs.

Pipeline analítico:

1 data enrichment
2 feature engineering
3 Weight of Evidence (WoE)
4 Information Value (IV)
5 logistic regression
6 rating engine

A prioridade é interpretabilidade e robustez, não complexidade de modelo.

Data enrichment via APIs externas (V1)

O DealSignal deve enriquecer os dados do CRM utilizando APIs públicas externas.

Integrações principais:

BrasilAPI

BuiltWith

Similarweb

Essas APIs devem ser usadas para enriquecer dados de contas.

Enriquecimento esperado
Dados empresariais

Via BrasilAPI:

company_age
company_status
primary_industry_code

Derived feature:

company_age_score

Maturidade digital

Via BuiltWith ou Wappalyzer-like detection:

tech_stack_count
uses_modern_stack

Derived feature:

digital_maturity_index

Presença digital

Via Similarweb:

website_traffic_estimate

Derived feature:

digital_presence_score

Requisitos do módulo de enrichment

Criar um pipeline de enriquecimento robusto:

chamadas de API com retry

caching local dos resultados

fallback caso API falhe

logs de enriquecimento

Os dados enriquecidos devem ser salvos em:

data/enriched_accounts.csv

Para evitar chamadas repetidas.

Features principais do MVP
Deal Momentum

Calcular:

days_since_engage
deal_age

pipeline_velocity:

pipeline_velocity = days_since_engage / stage_index

Stage mapping:

Prospecting = 1
Engaging = 2
Won = 3
Lost = 3

Deal Size Signal

close_value
deal_value_percentile

Seller Performance

agent_win_rate
agent_avg_deal_value

Product Performance

product_win_rate
product_avg_deal_value

Account Strength

revenue
employees
revenue_per_employee

company_age_score
digital_maturity_index
digital_presence_score

Feature pipeline

Pipeline esperado:

raw data
↓
API enrichment
↓
feature engineering
↓
WoE transformation
↓
feature selection (IV)
↓
model training

Modelo

Treinar Logistic Regression para prever:

Won vs Lost

Target:

deal_stage == "Won"

Treinar apenas com deals com resultado final:

Won ou Lost.

Rating Engine

Converter probabilidade em rating.

Tabela:

AAA → probability > 0.90
AA → 0.80 – 0.90
A → 0.70 – 0.80
BBB → 0.60 – 0.70
BB → 0.50 – 0.60
B → 0.40 – 0.50
CCC → < 0.40

Explainability

Cada deal deve retornar:

top_positive_factors
top_negative_factors

Baseado em:

model coefficients
feature contributions

O vendedor deve entender por que o deal recebeu determinado rating.

Interface

Criar uma aplicação simples em Streamlit.

A interface deve permitir:

visualizar pipeline completo
ordenar oportunidades por expected_revenue
filtrar por sales_agent
filtrar por manager
filtrar por office

Para cada deal mostrar:

account
product
sales_agent
win_probability
deal_rating
expected_revenue
top_contributing_factors

Também mostrar:

Top 10 Deals to Prioritize

Estrutura do projeto

Quero o projeto organizado desta forma:

dealsignal/

data/
accounts.csv
products.csv
sales_pipeline.csv
sales_teams.csv
enriched_accounts.csv

enrichment/
api_clients.py
company_enrichment.py
digital_enrichment.py

features/
feature_engineering.py
feature_store.py

model/
woe_transformer.py
feature_selection_iv.py
logistic_model.py
rating_engine.py

app/
streamlit_app.py

utils/
cache.py
explainability.py
logger.py

README.md
Requisitos de engenharia

O código deve incluir:

caching de respostas das APIs

tratamento de erros

logs

modularidade clara

facilidade para adicionar novas features

Entregáveis

A solução final deve incluir:

pipeline completo de dados

enriquecimento com APIs externas

modelo treinável

cálculo de rating

ranking de oportunidades

aplicação Streamlit funcional

Documentação

Gerar README contendo:

setup do ambiente
dependências
como executar enrichment
como treinar modelo
como rodar aplicação

Prioridades

Priorizar:

interpretabilidade

arquitetura clara

facilidade de manutenção

integração com APIs

Não priorizar:

modelos complexos como XGBoost ou deep learning.