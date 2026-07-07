# SKILL: Análise de Churn Ravenstack com Modelagem Preditiva

**Versão**: 1.0  
**Modelo**: Claude Sonnet 4  
**IDE**: VS Code com Extensão Claude Code  
**Dados**: 5 datasets interconectados (accounts, subscriptions, churn_events, feature_usage, support_tickets)

---

## 1. VISÃO GERAL DA SKILL

Framework abrangente de análise de churn combinando análise de dados cruzados, identificação de causa raiz, segmentação de risco e modelagem preditiva. Gera insights acionáveis, dashboards interativos e código de predição pronto para produção.

**Fluxo de Execução**:
1. Análise de perfil de dados e correlações
2. Análise de causa raiz (junções entre tabelas)
3. Pontuação de risco de segmento
4. Desenvolvimento de modelo preditivo (XGBoost/LightGBM)
5. Geração de dashboard interativo
6. Relatório em PDF com recomendações acionáveis

---

## 2. ESTRUTURA DE DADOS E RELACIONAMENTOS

```
accounts (500 linhas) ───┐
                         ├──→ JOIN account_id → churn_events (600 contas churned)
subscriptions (5000)─────┤                    + support_tickets (2000 tickets)
                         └──→ subscription_id → feature_usage (25000 registros)
```

**Campos Principais**:
- `account_id`: Chave primária entre accounts, subscriptions, churn_events, support_tickets
- `subscription_id`: Liga subscriptions → feature_usage
- `churn_flag`: Variável alvo (booleano)
- `reason_code`: Categórico {pricing, support, budget, features, competitor, unknown}
- Uso de features: indicador de adoção (alta correlação com retenção)
- Tickets de suporte: métrica de saúde (tempo resolução, satisfaction_score)

---

## 3. ANÁLISE DE CAUSA RAIZ (Questão 1)

### Prompt para Claude Sonnet:

```
Analise as causas raiz do churn usando consultas SQL:

1. GAP DE ADOÇÃO DE FEATURES:
   - Calcule avg usage_count para contas churned vs retidas
   - Identifique features com <30% adoção entre churned
   - Cruzamento: feature_usage + subscriptions.churn_flag

2. MÉTRICAS DE QUALIDADE DE SUPORTE:
   - Razão tempo resolução: churned vs retidas
   - Distribuição de scores de satisfação
   - Taxa de escalação por status de churn
   - Cruzamento: support_tickets + churn_events

3. DESALINHAMENTO DE PREÇO-PLANO:
   - Padrões de upgrade/downgrade precedendo churn
   - Declínio de MRR 60 dias antes do churn
   - Falha de conversão trial→pago
   - Cruzamento: subscriptions (upgrade_flag, downgrade_flag) + churn_flag

4. ANÁLISE DE TEMPO PARA VALOR:
   - Dias do signup até primeiro uso de feature
   - Latência signup→primeiro ticket de suporte
   - Curva de adoção de plano por tier
   - Cruzamento: accounts.signup_date + feature_usage.usage_date + subscriptions.start_date

5. PADRÕES INDÚSTRIA-GEOGRAFIA:
   - Taxa de churn por indústria, país, plan_tier
   - Correlação: status trial → churn
```

**Saída Esperada**: Causas raiz classificadas por significância estatística (V de Cramér, coef. correlação)

---

## 4. SEGMENTAÇÃO DE RISCO (Questão 2)

### Prompt para Claude Sonnet:

```
Identifique segmentos em risco com account_ids específicas:

1. MODELO DE PONTUAÇÃO DE ALTO RISCO:
   Fatores (ponderados):
   - Adoção de features < 3 features ativas: +40pts
   - Tickets de suporte (não resolvidos >96h OU satisfação <3.0): +35pts
   - Declínio de MRR >20% últimos 60 dias: +30pts
   - Downgrade de plano últimos 30 dias: +25pts
   - Indústria=FinTech/EdTech (historicamente alta rotatividade): +15pts
   - Conta trial com <5 interações de suporte: +20pts
   
   Score > 80: Risco Crítico
   Score 60-79: Risco Alto
   Score 40-59: Risco Médio

2. BREAKDOWN POR SEGMENTO (Contas Específicas):
   Para cada nível de risco:
   - Listar top 10 contas por score de risco
   - Incluir account_name, indústria, plan_tier, MRR
   - Status atual: ativo/churned
   - Dias até churn previsto (se ativo)
   - Principal driver de risco

3. ANÁLISE DE COORTE:
   - Novo vs Maduro (signup < 90 dias vs >90 dias)
   - Upgrade vs Clientes Estáveis
   - Engajamento de suporte (taxa alta/baixa de tickets)
```

**Saída**: Registro de risco com scores com lista de contas acionável

---

## 5. RECOMENDAÇÕES ACIONÁVEIS (Questão 3)

### Prompt para Claude Sonnet:

```
Gere estratégia de intervenção priorizada:

NÍVEL 1 - IMEDIATO (Semana 1):
- Outreach para contas Risco Crítico (score >80)
  * Chamadas proativas de suporte
  * Workshops de ativação de features
  * Oferta de desconto de retenção (<$500 contas ARR excluídas)
  Impacto estimado: Salvar 15-20% do nível Crítico

- Pausar contas trial no caminho do downgrade
  * Auto-trigger "Você está prestes a perder X" email
  * Oferecer call de suporte onboarding
  Impacto estimado: +5% conversão trial→pago

NÍVEL 2 - CURTO PRAZO (Semana 2-4):
- Fechamento de gap de produto (análise de features faltantes)
  * Top 3 features faltantes para contas churned
  * Comunicação roadmap para Risco Alto
  Impacto estimado: Reduz churn "features" em 25%

- Melhoria de SLA de suporte
  * Target <24h primeira resposta (atualmente 74min méd.)
  * <72h resolução (atualmente maior)
  Impacto estimado: Reduz churn relacionado a suporte 20%

NÍVEL 3 - MÉDIO PRAZO (Mês 2-3):
- Otimização de modelo de preços
  * Analise objeções de preço no feedback de churn
  * A/B test tier de entrada mais baixo
  Impacto estimado: Reduz churn budget/pricing em 30%

- Onboarding expandido para tier Enterprise
  * Atribuição de success manager
  * Reviews de negócio mensais
  Impacto estimado: Retenção Enterprise +10%

MÉTRICAS DE MONITORAMENTO:
- Recomputação semanal de score de risco
- Taxa de churn por segmento
- Taxa de resposta de intervenção (% resposta call, taxa abertura email)
```

---

## 6. DESENVOLVIMENTO DE MODELO PREDITIVO

### Estrutura Python (Auto-gerada por Sonnet):

```
/churn-model/
├── 01_data_preprocessing.py
│   ├── Load & merge datasets por account_id/subscription_id
│   ├── Feature engineering (adoção, qualidade suporte, trends preço)
│   ├── Handle valores ausentes, scaling
│   └── Train/test split (baseado em tempo: 80% histórico, 20% recente)
│
├── 02_feature_engineering.py
│   ├── Adoption Features: features_used, avg_usage_count, feature_diversity
│   ├── Support Features: ticket_count, avg_resolution_time, satisfaction_score
│   ├── Financial Features: mrr_change, arr_amount, upgrade_downgrade_flags
│   ├── Temporal Features: days_since_signup, days_since_last_activity
│   └── Industry Features: one-hot encode industry/country/plan_tier
│
├── 03_model_training.py
│   ├── XGBoost + LightGBM ensemble
│   ├── Hyperparameter tuning (GridSearchCV)
│   ├── SHAP feature importance
│   ├── Cross-validation metrics (AUC, precision, recall, F1)
│   └── Model serialization (pickle/joblib)
│
├── 04_risk_scoring.py
│   ├── Predict probabilidade churn para todas contas ativas
│   ├── Atribuição de nível de risco (crítico/alto/médio/baixo)
│   ├── Gerar registro de risco por conta
│   └── Export top N contas em risco
│
├── 05_dashboard_app.py (Streamlit)
│   ├── Heatmap de risco de conta
│   ├── Breakdown de driver de churn (SHAP)
│   ├── Métricas de performance de segmento
│   ├── Série temporal: trend de taxa de churn
│   └── Export: relatórios PDF, CSV
│
└── requirements.txt
    (pandas, scikit-learn, xgboost, lightgbm, shap, streamlit)
```

### Prompt do Sonnet para Geração de Código:

```
Gere código Python pronto para produção para modelo de predição de churn:

Requisitos:
1. Load 5 arquivos CSV, merge em account_id/subscription_id
2. Engenheirice features: gaps adoção, qualidade suporte, mudanças preço
3. Treine XGBoost + LightGBM com cross-validation
4. Output plot SHAP de feature importance
5. Gere risk_register.csv com colunas:
   account_id, account_name, risk_score, risk_tier, primary_driver, 
   prediction_confidence, recommended_action

Código deve ser:
- Pronto para produção (error handling, logging)
- Reproduzível (set random seeds)
- Documentado (docstrings)
- Eficiente (operações vetorizadas, sem loops)

Use arquitetura orientada a classes para reutilização.
```

---

## 7. DASHBOARD INTERATIVO COM SIMULAÇÃO DE CENÁRIOS

### Tecnologia: Streamlit (auto-gerado por Sonnet)

### Seções Principais:

```python
# 05_dashboard_app.py estrutura:

import streamlit as st
import plotly.express as px
import pandas as pd
from churn_model import ChurnPredictor

st.set_page_config(layout="wide")
st.title("Dashboard de Inteligência de Churn Ravenstack")

# SEÇÃO 1: Visão Geral de Risco
col1, col2, col3 = st.columns(3)
col1.metric("Contas em Risco Crítico", df[df['risk_tier']=='critical'].shape[0])
col2.metric("Taxa de Churn Prevista (30d)", "18.3%")
col3.metric("Receita em Risco", "$1.2M ARR")

# SEÇÃO 2: Heatmap de Risco
fig = px.scatter(df, x='mrr_amount', y='risk_score', 
                 color='industry', size='seats',
                 hover_data=['account_name', 'plan_tier'])
st.plotly_chart(fig)

# SEÇÃO 3: Feature Importance (SHAP)
st.subheader("Drivers de Churn por Importância")
st.bar_chart(shap_importance_df)

# SEÇÃO 4: Detalhes de Contas em Risco
st.subheader("Top 20 Contas Requerendo Ação")
st.dataframe(risk_register.head(20), use_container_width=True)

# SEÇÃO 5: Análise de Segmento
industry_churn = df.groupby('industry')['churn_flag'].agg(['sum', 'count'])
st.bar_chart(industry_churn)

# SEÇÃO 6: SIMULAÇÃO DE CENÁRIOS COM MODELO PREDITIVO (NOVO)
st.divider()
st.subheader("🔮 Simulador de Cenários - Modelo Preditivo de Churn")

with st.expander("Teste diferentes cenários para prever risco de churn", expanded=True):
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Parametros de Engajamento:**")
        
        adoption_rate = st.slider(
            "Taxa de Adoção de Features (%)",
            min_value=0, max_value=100, value=50, step=5,
            help="Percentual de features únicas usadas (0-40)"
        )
        
        support_tickets = st.number_input(
            "Quantidade de Tickets de Suporte",
            min_value=0, max_value=50, value=5
        )
        
        avg_resolution_time = st.slider(
            "Tempo Médio Resolução (horas)",
            min_value=0, max_value=240, value=48, step=12
        )
        
        satisfaction_score = st.slider(
            "Score de Satisfação (1-5)",
            min_value=1.0, max_value=5.0, value=3.5, step=0.5
        )
    
    with col2:
        st.write("**Parametros Financeiros e Conta:**")
        
        mrr_amount = st.number_input(
            "MRR ($)",
            min_value=0, max_value=50000, value=2500, step=100
        )
        
        days_since_signup = st.slider(
            "Dias desde Signup",
            min_value=0, max_value=1000, value=180, step=30
        )
        
        plan_tier = st.selectbox(
            "Plano",
            ["Basic", "Pro", "Enterprise"]
        )
        
        industry = st.selectbox(
            "Indústria",
            ["EdTech", "FinTech", "DevTools", "HealthTech", "Cybersecurity"]
        )
    
    # Botão para prever
    if st.button("🔮 Prever Risco de Churn com Modelo", use_container_width=True):
        
        # Preparar dados para modelo
        scenario_data = {
            'adoption_rate': adoption_rate / 100,
            'support_quality_score': satisfaction_score * (1 - min(avg_resolution_time, 100)/100),
            'support_ticket_count': support_tickets,
            'avg_resolution_time': avg_resolution_time,
            'avg_satisfaction': satisfaction_score,
            'mrr_amount': mrr_amount,
            'days_since_signup': days_since_signup,
            'plan_tier': plan_tier,
            'industry': industry
        }
        
        # Prever com modelo XGBoost
        predictor = ChurnPredictor()
        prediction = predictor.predict(scenario_data)
        
        # Mostrar resultado
        st.divider()
        st.subheader("📊 Resultado da Simulação")
        
        col_result1, col_result2, col_result3 = st.columns(3)
        
        with col_result1:
            st.metric(
                "Probabilidade de Churn",
                f"{prediction['churn_probability']*100:.1f}%",
                delta=f"{prediction['churn_probability']*100 - 18.3:.1f}% vs baseline"
            )
        
        with col_result2:
            risk_tier = prediction['risk_tier']
            tier_colors = {
                'Critical': '🔴',
                'High': '🟠',
                'Medium': '🟡',
                'Low': '🟢'
            }
            st.metric(
                "Nível de Risco",
                f"{tier_colors.get(risk_tier, '⚪')} {risk_tier}"
            )
        
        with col_result3:
            score = prediction['risk_score']
            st.metric(
                "Score de Risco (0-100)",
                f"{score:.0f}"
            )
        
        # Explicação dos drivers
        st.write("**Top 3 Fatores de Risco (por importância SHAP):**")
        drivers_df = pd.DataFrame({
            'Fator': prediction['top_drivers'].keys(),
            'Impacto': prediction['top_drivers'].values()
        })
        st.dataframe(drivers_df, use_container_width=True)
        
        # Recomendações
        st.write("**Ações Recomendadas:**")
        for i, rec in enumerate(prediction['recommendations'], 1):
            st.info(f"{i}. {rec}")
        
        # O que mudaria o resultado? (Análise de Cenários)
        st.write("**Cenários de Intervenção (O que mudaria o resultado?):**")
        
        intervention_col1, intervention_col2 = st.columns(2)
        
        with intervention_col1:
            st.write("**Se aumentasse adoção para 80%:**")
            improved_scenario = scenario_data.copy()
            improved_scenario['adoption_rate'] = 0.8
            improved_pred = predictor.predict(improved_scenario)
            improvement = (prediction['churn_probability'] - improved_pred['churn_probability']) * 100
            st.success(f"Risco cairia para {improved_pred['churn_probability']*100:.1f}% (-{improvement:.1f}pp)")
        
        with intervention_col2:
            st.write("**Se reduzisse tempo resolução para <24h:**")
            improved_scenario = scenario_data.copy()
            improved_scenario['avg_resolution_time'] = 24
            improved_pred = predictor.predict(improved_scenario)
            improvement = (prediction['churn_probability'] - improved_pred['churn_probability']) * 100
            st.success(f"Risco cairia para {improved_pred['churn_probability']*100:.1f}% (-{improvement:.1f}pp)")

# OPÇÕES DE EXPORT
if st.button("Gerar Relatório PDF"):
    generate_pdf_report(df, shap_importance)
    st.success("Relatório salvo: churn_analysis_report.pdf")
```

### Funcionalidades da Simulação de Cenários:

1. **Inputs Interativos para Teste:**
   - Sliders para taxa de adoção, tempo resolução, satisfação
   - Number inputs para MRR, tickets de suporte
   - Selectboxes para plan_tier e indústria

2. **Previsão em Tempo Real com Modelo:**
   - Modelo XGBoost prediz probabilidade de churn
   - Risk score (0-100)
   - Risk tier (Critical/High/Medium/Low)

3. **Explicabilidade SHAP:**
   - Top 3 fatores impactando cada predição
   - SHAP values mostrando contribuição de cada feature
   - Drivers ordenados por importância relativa

4. **Análise de Intervenção Automática:**
   - "O que mudaria o resultado?"
   - Simulação de múltiplos cenários de melhoria
   - Impacto estimado de cada ação (ex: aumentar adoção, reduzir tempo resolução)
   - Comparação antes/depois para cada cenário

5. **Recomendações Acionáveis:**
   - Ações sugeridas baseadas no perfil da conta
   - Priorização automática por impacto esperado
   - ROI estimado de cada intervenção

---

## 8. DEPLOYMENT NO STREAMLIT COMMUNITY CLOUD

O dashboard com modelo preditivo será **deployado no Streamlit Community Cloud** para acesso público e gratuito.

### 🚀 Setup de Deployment:

**Plataforma:** Streamlit Community Cloud (share.streamlit.io)  
**Custo:** ✅ Grátis permanentemente  
**Acesso:** 🌍 Público (qualquer pessoa com URL)  
**URL Final:** `https://seu-usuario-churn-dashboard.streamlit.app`

### Preparação para Deploy:

#### 1. Estrutura do Repositório GitHub:

```
seu-repo/
├── .gitignore                      # Não versionar dados sensíveis
├── README.md                       # Documentação
├── requirements.txt                # Dependências Python
├── app.py                          # Dashboard (seu 05_dashboard_app.py)
├── churn_model.py                  # Classe ChurnPredictor com XGBoost
│
├── scripts/                        # (Análise, não vai produção)
│   ├── 01_data_preprocessing.py
│   ├── 02_root_cause_analysis.py
│   └── 03_risk_segmentation.py
│
└── outputs/                        # ❌ NÃO VERSIONE (em .gitignore)
    ├── risk_register.csv
    ├── critical_action_list.csv
    └── preprocessed_data.csv
```

#### 2. Arquivo .gitignore:

```
# Dados sensíveis (não versione)
outputs/*.csv
data/*.csv
*.pkl
*.joblib

# Python
__pycache__/
*.pyc
venv/
*.egg-info/

# Streamlit
.streamlit/secrets.toml
```

#### 3. requirements.txt:

```
streamlit==1.40.0
pandas==2.1.4
plotly==5.18.0
numpy==1.24.3
scikit-learn==1.3.2
xgboost==2.0.3
lightgbm==4.1.1
shap==0.44.1
scipy==1.11.4
reportlab==4.0.9
```

### Passos de Deployment:

#### Step 1: Prepare GitHub

```bash
cd seu-projeto/churn-analysis

# Crie/atualize .gitignore
cat > .gitignore << 'EOF'
outputs/*.csv
data/*.csv
*.pkl
__pycache__/
venv/
.streamlit/secrets.toml
EOF

# Commit e push
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

#### Step 2: Acesse Streamlit Cloud

1. Vá para **https://share.streamlit.io**
2. Clique em **"New app"**
3. Preencha:
   - **Repository:** seu-usuario/seu-repo
   - **Branch:** main
   - **Main file path:** app.py

4. Clique **"Deploy"**

#### Step 3: Aguarde Deploy (1-2 minutos)

Console mostrará:
```
Building...
Building done
Your app is running at: https://seu-usuario-churn-dashboard.streamlit.app
```

#### Step 4: Compartilhe

Envie para stakeholders:
```
https://seu-usuario-churn-dashboard.streamlit.app
```

### Carregamento de Dados no Deployment:

Como dados **não estão versionados**, use uma destas estratégias:

**Opção 1: Upload de Arquivo (Simples)**
```python
uploaded_file = st.file_uploader("Upload risk_register.csv")
if uploaded_file:
    risk_register = pd.read_csv(uploaded_file)
```

**Opção 2: URL Pública (Melhor)**
```python
@st.cache_data
def load_data():
    url = "https://seu-s3-bucket/risk_register.csv"
    return pd.read_csv(url)
```

**Opção 3: Secrets (Mais Seguro)**
```python
# No Streamlit Cloud Settings → Secrets:
[database]
url = "sua-database-url"

# Na app:
url = st.secrets["database"]["url"]
```

### Auto-Updates:

Qualquer mudança no GitHub atualiza automaticamente:

```bash
# Você faz:
git push origin main

# Streamlit Cloud:
# 1. Detecta mudança
# 2. Rebuilda (1-2 min)
# 3. Todos os usuários veem versão nova
```

### Limitações e Características:

| Aspecto | Detalhes |
|--------|----------|
| **Memória** | ~1GB RAM compartilhada |
| **CPU** | Compartilhado |
| **Usuários** | Ilimitados (até rate limit ~1000/dia) |
| **Rate Limiting** | Se muitos requests, retorna 429 |
| **Código** | Público (visível no GitHub) |
| **Custo** | ✅ Grátis permanentemente |

---

## 10. GERAÇÃO DE RELATÓRIO PDF

### Prompt para Claude Sonnet:

```
Gere relatório PDF usando ReportLab:

Estrutura:
1. Sumário Executivo (1 página)
   - Métricas-chave: taxa churn, receita em risco, top driver de risco
   - Ações críticas: top 3 intervenções
   
2. Análise de Causa Raiz (2 páginas)
   - Gaps adoção de features (tabela + gráfico)
   - Problemas qualidade suporte (trend + scatter satisfação)
   - Padrões desalinhamento de preço (análise declínio MRR)
   
3. Segmentação de Risco (2 páginas)
   - Distribuição nível de risco (gráfico pizza)
   - Top 20 contas em risco (tabela)
   - Métricas de segmento por indústria/plan_tier
   
4. Performance do Modelo (1 página)
   - Matriz confusão, curva AUC, feature importance
   - Acurácia modelo: 85%+
   
5. Recomendações & Impacto (2 páginas)
   - Roadmap de intervenção (Nível 1/2/3)
   - ROI estimado por ação
   - KPIs sucesso & dashboard monitoramento
   
Total: 8-10 páginas, headers/footers com marca
```

**Saída**: `churn_analysis_report_YYYY-MM-DD.pdf`

---

## 11. EXECUÇÃO NO VS CODE

### Setup:

```bash
# Terminal no VS Code
pip install pandas scikit-learn xgboost lightgbm shap streamlit plotly reportlab

# Criar estrutura projeto
mkdir churn-analysis && cd churn-analysis
mkdir data models outputs

# Copiar CSVs para data/
cp /path/to/*.csv data/
```

### Rodar Análise:

```bash
# Executar passo-a-passo
python 01_data_preprocessing.py
python 02_feature_engineering.py
python 03_model_training.py
python 04_risk_scoring.py

# Lançar dashboard
streamlit run 05_dashboard_app.py

# Gerar relatório
python generate_pdf_report.py
```

---

## 12. TEMPLATES DE PROMPT PARA CLAUDE SONNET

### Template A: Análise Rápida de Causa Raiz
```
Analise este dataset de churn focando em:
1. Padrões de adoção de features em contas churned
2. Correlação ticket de suporte com churn
3. Sequências de upgrade/downgrade precedendo churn

Forneça: Top 5 causas raiz classificadas por frequência e impacto
```

### Template B: Deep Dive Específico por Segmento
```
Para contas [INDÚSTRIA], calcule risco de churn usando:
- Diversidade adoção de features (# features únicas usadas)
- Qualidade interação suporte (tempo resposta, satisfação)
- Trends de MRR (mudança últimos 60 dias)

Output: Lista de contas classificada por risco com recomendações de ação específicas
```

### Template C: Explicabilidade de Modelo
```
Para as contas marcadas "risco crítico":
1. Explique os top 3 fatores impulsionando sua predição de churn
2. O que precisaria mudar para movê-las para "risco baixo"?
3. Priorize intervenções pelo resultado esperado
```

---

## 13. CHECKLIST DE VALIDAÇÃO

- [ ] **Qualidade de Dados**: Sem nulos em campos-chave (account_id, churn_flag)
- [ ] **Joins Verificados**: Todas contas têm ≥1 subscrição, todas subscrições ligadas
- [ ] **Feature Engineering**: 20+ features engenheiradas, matriz correlação checada
- [ ] **Modelo**: AUC >0.80, precisão >0.75 para nível crítico de risco
- [ ] **Dashboard**: Todos visualizações carregam, filtros responsivos
- [ ] **Simulador**: Interface de cenários funciona, predições corretas
- [ ] **PDF**: Relatório gera <10s, formatação limpa, dados precisos
- [ ] **Deployment**: App deployada no Streamlit Cloud, acessível publicamente
- [ ] **Recomendações**: Ligadas a impacto mensurável ($ ou % melhoria)

---

## 14. INSIGHTS ESPERADOS (Preview)

**Causa Raiz**: Gap adoção de features (usuários churned adotam 40% menos features)  
**Segmento em Risco**: Contas FinTech + EdTech em plano Basic com <30 dias tenure  
**Ação-Chave**: Auto-trigger workshop ativação feature no Dia 7 (lift retenção estimado 18%)  
**Performance do Modelo**: 84% AUC, identifica corretamente 73% de churn 30 dias antes

---

## NOTAS

- Atualizar modelo mensalmente com novos dados de churn
- Re-scored register semanal (usar script batch scoring)
- Rastrear outcomes de intervenção em tabela separada para refinamento do modelo
- Dashboard auto-atualiza diariamente da pasta de dados
