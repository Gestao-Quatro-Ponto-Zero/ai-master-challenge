Claude’s Plan
DealSignal - Plano de Implementação
Contexto
Construir o DealSignal: um deal rating engine baseado em regressão logística com WoE, inspirado em modelos de risco de crédito bancário. O sistema processa ~8.800 oportunidades de CRM, enriquece dados de contas via APIs externas (com fallback mock), treina um modelo interpretável e apresenta priorização de deals em uma interface Streamlit.

Dados existentes: /Users/jessicacastro/claudecode/submissions/jessica-castro/archive-g4-lead-scorer/
Destino do projeto: /Users/jessicacastro/claudecode/submissions/jessica-castro/dealsignal/

Observações Críticas sobre os Dados
Coluna no CSV	Coluna no Spec	Resolução
sector	industry	Usar como sector
year_established	—	Derivar company_age = 2017 - year_established
office_location	location	Usar como office_location
subsidiary_of	parent_company	Usar como subsidiary_of
regional_office	office	Filtrar Streamlit por regional_office
GTXPro no pipeline	GTX Pro nos products	Normalizar antes de qualquer join
Data de referência por deal (snapshot_date):

Deals fechados (Won/Lost): snapshot_date = close_date
Deals abertos (Engaging/Prospecting): snapshot_date = max(close_date) do dataset = 2017-12-27
days_since_engage = snapshot_date − engage_date
Para deals fechados, isso captura o ciclo de vendas real. Para abertos, captura quanto tempo o deal está ativo. Não usar a data atual (2026), que destruiria a variância.
APIs externas: As empresas são fictícias (Acme Corporation, etc.) — BrasilAPI não retornará dados. A arquitetura faz chamadas reais mas faz fallback automático para dados mock determinísticos (hash MD5 do nome da empresa como seed), garantindo reprodutibilidade.

Estrutura do Projeto

dealsignal/
├── data/
│   ├── accounts.csv
│   ├── products.csv
│   ├── sales_pipeline.csv
│   ├── sales_teams.csv
│   └── enriched_accounts.csv     ← gerado pelo enrichment
├── enrichment/
│   ├── __init__.py
│   ├── api_clients.py            ← BrasilAPI, BuiltWith, Similarweb (com retry/tenacity)
│   ├── company_enrichment.py     ← company_age_score, fallback mock
│   └── digital_enrichment.py    ← digital_maturity_index, digital_presence_score, fallback mock
├── features/
│   ├── __init__.py
│   ├── feature_engineering.py   ← 18 features + normalização + leakage-safe split
│   └── feature_store.py          ← save/load parquet
├── model/
│   ├── __init__.py
│   ├── artifacts/                ← pkl dos objetos fitados
│   ├── woe_transformer.py        ← WoETransformer sklearn-compatible + contribuições
│   ├── feature_selection_iv.py   ← select_features_by_iv(threshold=0.02)
│   ├── logistic_model.py         ← LogisticRegressionCV + calibração isotônica
│   └── rating_engine.py          ← assign_rating() + score_pipeline()
├── app/
│   ├── __init__.py
│   └── streamlit_app.py          ← UI completa
├── utils/
│   ├── __init__.py
│   ├── cache.py                  ← joblib.Memory + pickle artifacts
│   ├── explainability.py         ← contribuições por feature (woe × coeficiente)
│   └── logger.py                 ← logging file + console
├── run_pipeline.py               ← orquestrador completo
├── requirements.txt
└── README.md
Pipeline Analítico

CSVs brutos
    ↓
enrichment/digital_enrichment.py
    (tenta API real → fallback mock determinístico por hash)
    → data/enriched_accounts.csv
    ↓
features/feature_engineering.py
    → 18 features para todos os 8.800 deals
    ↓
Split: Won/Lost (treino) | Engaging/Prospecting (scoring)
    ↓
model/woe_transformer.py  [fit no treino]
    → WoE maps + IV scores por feature
    ↓
model/feature_selection_iv.py
    → manter features com IV > 0.02
    ↓
model/logistic_model.py  [fit no treino]
    → LogisticRegressionCV (C auto) + calibração isotônica
    ↓
model/rating_engine.py  [score nos deals abertos]
    → win_probability, deal_rating, expected_revenue
    ↓
utils/explainability.py
    → top_positive_factors, top_negative_factors (woe × coef)
    ↓
data/results.csv
    ↓
app/streamlit_app.py
Features (18 numéricas → WoE)
Deal Momentum

snapshot_date = close_date (se fechado) ou max(dataset) para abertos
days_since_engage = snapshot_date − engage_date
stage_index: Prospecting=1, Engaging=2, Won/Lost=3
pipeline_velocity = days_since_engage / stage_index
deal_age é eliminado — torna-se idêntico a days_since_engage para deals fechados.

Deal Size Signal

effective_value = close_value se fechado, senão sales_price do produto
deal_value_percentile = percentile rank entre todos os deals
Seller Performance (calculado APENAS no treino, depois join global)

agent_win_rate
agent_avg_deal_value
Product Performance (idem)

product_win_rate
product_avg_deal_value
Account Strength

revenue, employees, revenue_per_employee
company_age = 2017 − year_established
company_age_score = min-max normalizado
Enrichment

digital_maturity_index (0–1, Beta(2,5) mock)
digital_presence_score (0–1, Beta(2,5) mock)
tech_stack_count (int, randint mock)
Nota: stage_index terá variância zero no treino (Won/Lost são todos =3) → IV≈0 → excluído pelo IV selector. Permanece útil no cálculo de pipeline_velocity.

Modelo
Algoritmo: LogisticRegressionCV (Cs=[0.01, 0.1, 1, 10], cv=5, scoring='roc_auc', class_weight='balanced')
Calibração: CalibratedClassifierCV(method='isotonic') pós-treino
Validação: AUC-ROC com cross_val_score(cv=5), logado como INFO
Rating Engine

AAA  → prob > 0.90
AA   → 0.80 – 0.90
A    → 0.70 – 0.80
BBB  → 0.60 – 0.70
BB   → 0.50 – 0.60
B    → 0.40 – 0.50
CCC  → < 0.40
expected_revenue = win_probability × effective_value

Explainability
Por deal: contribution_i = woe_value_i × coefficient_i

top_positive_factors: top 3 contribuições positivas
top_negative_factors: top 3 contribuições negativas
Renderizado como string no Streamlit: "+agent_win_rate(+0.42), -pipeline_velocity(-0.18)"
Interface Streamlit
Sidebar: Filtros por sales_agent, manager, regional_office

Main:

KPI cards: Total Expected Revenue | Top 10 Expected Revenue | Model AUC
"Top 10 Deals to Prioritize" — gráfico de barras horizontal (plotly) por expected_revenue
Tabela completa do pipeline com colunas: account, product, sales_agent, win_probability, deal_rating, expected_revenue, top_contributing_factors
Ordenada por expected_revenue desc (padrão)
deal_rating com color coding (AAA=verde escuro → CCC=vermelho escuro)
Orquestrador: run_pipeline.py

python run_pipeline.py                # usa cache se existir
python run_pipeline.py --force-enrich # re-roda enrichment
python run_pipeline.py --force-train  # re-treina modelo
Salva artefatos em model/artifacts/: woe_transformer.pkl, model.pkl, feature_cols.pkl, metadata.json (AUC, n_features, data de treino).

Dependências (requirements.txt)

pandas>=2.0
scikit-learn>=1.3
streamlit>=1.30
tenacity>=8.2
joblib>=1.3
requests>=2.31
numpy>=1.24
plotly>=5.18
Verificação End-to-End
cd dealsignal && pip install -r requirements.txt
python run_pipeline.py → deve logar AUC ~0.70+, salvar data/results.csv
streamlit run app/streamlit_app.py → abrir no browser, verificar filtros e Top 10
Inspecionar data/enriched_accounts.csv → confirmar colunas de enriquecimento
Testar --force-enrich e --force-train para confirmar flags funcionando
User approved the plan
Update Todos

Criar estrutura de diretórios e copiar CSVs

Criar utils/ (logger, cache, explainability)

Criar enrichment/ (api_clients, company_enrichment, digital_enrichment)

Criar features/ (feature_engineering, feature_store)

Criar model/ (woe_transformer, feature_selection_iv, logistic_model, rating_engine)

Criar run_pipeline.py (orquestrador)

Criar app/streamlit_app.py

Criar requirements.txt e README.md

Testar pipeline completo (run_pipeline.py)

Testar Streamlit app