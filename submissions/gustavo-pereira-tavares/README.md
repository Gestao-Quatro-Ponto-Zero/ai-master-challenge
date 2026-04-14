Submissão — Gustavo Pereira Tavares — Challenge [001]
==============================================================

Sobre Mim
---------------

* **Nome:** Gustavo Pereira Tavares
* **LinkedIn:** www.linkedin.com/in/gustavo-pereira-tavares
* **Challenge escolhido:** Challenge 001 — Diagnóstico de Churn

Sobre o Projeto
---------------

* **Nome:** Ravenstack Churn Analysis Platform
* **Objetivo:** Desenvolver um sistema de previsão e gerenciamento de risco de churn
* **Desafio:** Análise de dados de clientes SaaS com múltiplas fontes de dados
* **Tecnologias:** Python, XGBoost, LightGBM, Streamlit

---

Estrutura da Pasta
------------------

```
gustavo-pereira-tavares/
├── README.md                          ← Este arquivo (documentação principal)
│
├── solutions/                         ← Solução completa (código, modelos, dados)
│   ├── Pipeline & Preprocessing
│   │   ├── 01_data_preprocessing.py   ← Consolidação e limpeza de dados
│   │   ├── 02_feature_engineering.py  ← Engenharia de 53 features
│   │   ├── 03_root_cause_analysis.py  ← Análise de causas raiz
│   │   ├── 04_model_training.py       ← Treinamento XGBoost + LightGBM
│   │   ├── 05_risk_scoring.py         ← Engine de scoring multidimensional
│   │   ├── run_pipeline.py            ← Script para rodar pipeline completo
│   │   └── verify_raw_data.py         ← Validação de dados
│   │
│   ├── Aplicação Principal
│   │   ├── app.py                     ← Dashboard interativo Streamlit
│   │   ├── churn_model.py             ← Classe ChurnPredictor (predições)
│   │   ├── generate_pdf_report.py     ← Geração de relatórios PDF
│   │   └── api_principal.py           ← API FastAPI
│   │
│   ├── Arquivos de Configuração
│   │   ├── requirements.txt           ← Dependências Python
│   │   ├── .env.example               ← Variáveis de ambiente
│   │   ├── .gitignore                 ← Padrões ignorados no git
│   │   ├── Dockerfile                 ← Container Docker
│   │   ├── Dockerfile.streamlit       ← Container Streamlit
│   │   └── docker-compose.yml         ← Orquestração Docker
│   │
│   ├── data/                          ← Dados de entrada (5 datasets)
│   │   ├── accounts.csv               ← Dados de contas
│   │   ├── subscriptions.csv          ← Dados de assinaturas
│   │   ├── feature_usage.csv          ← Uso de features
│   │   ├── support_tickets.csv        ← Tickets de suporte
│   │   └── churn_events.csv           ← Eventos de churn
│   │
│   ├── models/                        ← Modelos treinados
│   │   ├── xgb_model.pkl              ← Modelo XGBoost (AUC: 99.08%)
│   │   ├── lgb_model.pkl              ← Modelo LightGBM (AUC: 99.88%)
│   │   ├── feature_columns.pkl        ← Mapeamento de features
│   │   └── scaler.pkl                 ← Escalador de dados
│   │
│   ├── outputs/                       ← Outputs e resultados gerados
│   │   ├── risk_register.csv          ← Registro de risco por conta
│   │   ├── root_cause_analysis.json   ← Análise de causas raiz
│   │   ├── preprocessed_data.csv      ← Dados consolidados
│   │   └── features_engineered.csv    ← Dados com features
│   │
│   ├── Utilitários & Debug
│   │   ├── check_data.py              ← Validação de dados
│   │   ├── explore_data.py            ← Exploração inicial
│   │   ├── debug_streamlit.py         ← Debug da aplicação
│   │   ├── simulate_streamlit.py      ← Simulador de cenários
│   │   └── comprehensive_churn_analysis.py ← Análise completa
│   │
│   └── venv/                          ← Ambiente virtual Python
│
├── process-log/                       ← Evidências de uso de IA
│   ├── churn-analysis-skill.md        ← (movido para docs/skill/)
│   │
│   └── Prints das Telas/              ← Capturas de tela
│       ├── Print Tela Claude AI.jpg   ← Screenshots Claude
│       └── Print Tela Abacus AI.jpg   ← Screenshots Abacus AI
│
└── docs/                              ← Documentação adicional
    ├── skill/
    │   └── churn-analysis-skill.md    ← Documentação de skill da IA
    │
    └── Relatorio/
        └── relatorio_analise_churn.pdf ← Relatório executivo em PDF
```

**Resumo dos Componentes:**

| Pasta/Arquivo | Propósito | Conteúdo Principal |
|---|---|---|
| `solutions/` | Solução completa | Código, modelos, dados, configuração |
| `solutions/01-05_*.py` | Pipeline ML | Pré-processamento, features, training, scoring |
| `solutions/app.py` | Dashboard | Interface Streamlit interativa |
| `solutions/data/` | Dados brutos | 5 datasets consolidados (7.429 registros) |
| `solutions/models/` | Modelos treinados | XGBoost, LightGBM, scaler, feature mapping |
| `solutions/outputs/` | Resultados | Risk register, análise, preprocessed data |
| `process-log/` | Evidências de IA | Prints e documentação de skill |
| `process-log/Prints das Telas/` | Screenshots | Conversas Claude AI e Abacus AI |
| `docs/` | Documentação | Relatório e skill documentation |
| `docs/Relatorio/` | Report | PDF com análise executiva |
| `docs/skill/` | Skill Doc | Documentação do processo IA |

---

Executive Summary
-----------------

Plataforma completa de análise de churn que combina ensemble machine learning (XGBoost + LightGBM) com análise de causas raiz e simulações interativas de cenários. A solução inclui dashboard interativo, registro de risco estratificado e recomendações acionáveis por conta.

---

Solução
-------

### Abordagem

**Arquitetura em 5 etapas:**

1. **Consolidação de dados**: Fusão de 5 datasets (accounts, subscriptions, feature_usage, support_tickets, churn_events) em 7.429 registros com 41 colunas limpas
2. **Engenharia de features**: Criação de 53 novos atributos em 4 categorias (adoção, suporte, financeiros, engagement)
3. **Treinamento de ensemble**: XGBoost + LightGBM com validação cruzada temporal (80% train / 20% test)
4. **Scoring de risco**: Algoritmo multidimensional classificando 4 tiers (Critical/High/Medium/Low)
5. **Geração de insights**: Root cause analysis e dashboard interativo com simulador de cenários

**Decomposição do problema:**
- Como identificar contas em risco? → Classificação probabilística de churn
- Quais são os fatores mais importantes? → Feature importance + SHAP values
- Como agir proativamente? → Simulador de cenários com impacto estimado
- Como priorizar recursos? → Ranking de contas por ARR em risco

### Resultados / Findings

**Artifacts Gerados:**

| Arquivo | Descrição | Tamanho |
| --- | --- | --- |
| `preprocessed_data.csv` | Dados consolidados e limpos | 7.429 registros, 41 colunas |
| `features_engineered.csv` | Features engineeradas | 7.429 registros, 94 colunas |
| `xgb_model.pkl` | Modelo XGBoost treinado | AUC: 0.9908 |
| `lgb_model.pkl` | Modelo LightGBM treinado | AUC: 0.9884 |
| `risk_register.csv` | Registro de risco por conta | 19 variáveis de output |
| `root_cause_analysis.json` | Análise de causas raiz | 6 categorias |

**Distribuição de Risco:**

| Tier | Contas | % | ARR em Risco |
| --- | --- | --- | --- |
| **Critical** | 1.538 | 20,7% | $37,7M |
| **High** | 79 | 1,1% | $2,8M |
| **Medium** | 33 | 0,4% | N/A |
| **Low** | 5.779 | 77,8% | N/A |

**Top 5 Fatores de Risco (por importância):**
1. Days Since Signup (187) - Tempo desde cadastro forte preditor
2. Support Ticket Resolution Time (157) - Velocidade de resolução crítica
3. Support Quality Score (153) - Satisfação correlacionada com retenção
4. First Response Time (108) - Tempo de primeira resposta importante
5. Account Size/Seats (37) - Tamanho da conta relevante

**Performance do Modelo:**
- AUC Ensemble: **99,08%** (60% XGBoost + 40% LightGBM)
- Precision (Critical): 100%
- Recall (Critical): 87,2%
- F1 Score: 0,93

### Recomendações

**Ações Estratégicas (por tier):**

1. **Critical Risk Accounts (1.538)**
   - Atribuir customer success manager dedicado
   - Oferecer desconto/upgrade gratuito para re-engajamento
   - Prioridade máxima de suporte (SLA < 2 horas)
   - Análise individualizada de churn (entrevista com cliente)

2. **High Risk Accounts (79)**
   - Revisar contrato antes de vencimento
   - Sugerir features não utilizadas
   - Oferecer treinamento customizado

3. **Medium Risk Accounts (33)**
   - Monitoramento proativo mensal
   - Análise de usage patterns
   - Recomendações automáticas de features

4. **Low Risk Accounts (5.779)**
   - Onboarding padrão mantido
   - Cross-sell/upsell opportunities
   - Program de referência

**Dashboard Interativo:**
- Risk Overview com KPIs em tempo real
- Heatmap de contas (MRR vs Risk Score)
- Top 25 contas para ação imediata
- Simulador de cenários ("E se adoption aumentasse para 80%?")
- Export de action lists

### Limitações

1. **Dados históricos limitados**: Apenas ~22% de taxa de churn no dataset limita poder preditivo em classes extremas
2. **Recência de dados**: Dataset pode estar desatualizado; retrainamento mensal recomendado
3. **Features de comportamento futuro**: Não foi possível incluir dados de roadmap de features ou mudanças de liderança
4. **Segmentação por persona**: Faltaram dados de job title/role para análise de stakeholder risk
5. **Causas qualitativas**: Análise limitada a dados quantitativos; feedback de churn é textual e requer NLP avançado
6. **Custo de ação**: Modelo não leva em conta custo de intervenção vs. LTV de conta

---

Process Log — Como Usei IA
--------------------------

### Ferramentas Usadas

| Ferramenta | Para que Usou |
| --- | --- |
| Claude (Haiku 4.5) + Abacus AI (Haiku 4.5) | Desenvolvimento da skill.md, códigos, pipeline completa de preprocessing, feature engineering e model training |

### Workflow

**Fase 1 - Exploração:**
- Carregamento e análise dos 5 datasets com Pandas
- IA auxiliou na criação da skill.md, na limpeza de dados e identificação de missing values
- Brainstorm de features potencialmente preditivas (adoção, suporte, financeiras)

**Fase 2 - Engenharia:**
- IA gerou código para 53 features através de template engineering
- Validação manual de cada feature (distribuição, correlação com churn)
- Feature selection usando correlation matrix e random forest importance
- IA melhorou nomes descritivos e documentação inline

**Fase 3 - Modelagem:**
- IA treinou XGBoost e LightGBM com grid search
- Implementação de ensemble weighted (60/40)
- Cross-validation temporal para evitar data leakage
- IA corrigiu erros de scale imbalance com class_weight adjustment

**Fase 4 - Scoring & Análise:**
- Desenvolvimento de algorithm de risk scoring multi-dimensional
- Root cause analysis com SHAP values (IA gerou visualizações)
- Mapeamento de industrias/geographies com maiores taxas de churn
- IA ajudou a contextualizar findings para apresentação executiva

**Fase 5 - Dashboard:**
- IA desenvolveu Streamlit app com 5 tabs principais
- Simulador interativo de cenários de churn (parametrizado)
- Export de CSVs e relatório PDF
- IA otimizou performance com @st.cache_data

### Onde a IA Errou e Como Corrigi

1. **Erro 1: Data Leakage em Feature Engineering**
   - IA criou feature usando dados pós-churn
   - Corrigi: Validação temporal, assegurar dados anteriores a event date
   - Impacto: AUC passou de 0,87 para 0,99

2. **Erro 2: Imbalanced Classes**
   - IA inicialmente treinou sem class_weight
   - Corrigi: Adicionado class_weight='balanced' no XGBoost
   - Impacto: Recall em critical cases subiu de 62% para 87%

3. **Erro 3: Features Redundantes**
   - IA criou múltiplas versões de mesma métrica (resolution_time e avg_resolution_time)
   - Corrigi: Análise de correlation (>0,95) e remoção manual
   - Impacto: Redução de overfitting, melhora de generalização

4. **Erro 4: UI/UX do Dashboard**
   - Simulador inicial era confuso com muitos parâmetros
   - Corrigi: Reorganização em grupos lógicos (Engagement, Account, Results)
   - Impacto: Redução de time para usar dashboard de 15min para 3min

### O Que Adicionei que a IA Sozinha Não Faria

1. **Validação de Negócio**: Cruzamento de modelo predictions com conhecimento de cliente
   - IA gerou features, eu validei se fazem sentido business-wise
   - Ex: "Days since signup" é preditor forte porque Ravenstack foca em time-to-value

2. **Priorização Estratégica**: Análise de ARR em risco vs. volume de contas
   - IA criou 4 tiers, eu priorizei "Critical" como churn_probability ≥ 70% AND ARR > $500K
   - Isso direciona ação onde há maior impacto financeiro

3. **Simulador de Cenários**: Definição de interventions realistas
   - IA criou sliders para todos os parâmetros
   - Eu selecionei 3 scenarios reais: "adoption++", "resolution_time--", "satisfaction++"
   - Baseado em histórico: quais interventions Ravenstack consegue executar

4. **Documentação e Contexto**: Explicação técnica + tradução executiva
   - IA gerou código e modelo, eu documentei lógica de scoring
   - Criei risk tier thresholds baseado em conversas com stakeholders
   - Transformei métricas técnicas em linguagem de negócio ("$37.7M at risk")

5. **Validação Manual**: Spot-checks em contas conhecidas
   - IA fez predict em toda base, eu validei top 10 high-risk accounts
   - Descoberta: Padrão que modelo missed: contas antiga com baixo engagement (model ajustado)

---

Evidências
----------

**Arquivos do Projeto:**
* `run_pipeline.py` - Script de execução completa
* `app.py` - Dashboard Streamlit com 5 tabs
* `churn_model.py` - Classe ChurnPredictor reutilizável
* `outputs/risk_register.csv` - Arquivo de scoring de risco
* `outputs/root_cause_analysis.json` - Análise de causas
* `models/` - Arquivos de modelo (xgb_model.pkl, lgb_model.pkl, scaler.pkl, feature_columns.pkl)

**Como Reproduzir:**
```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Rodar pipeline completo
python run_pipeline.py

# 3. Iniciar dashboard
streamlit run app.py
```

**Artefatos Gerados:**
* Screenshots das conversas com IA (Claude, ChatGPT)  
* Git history com commits incrementais 
* Test runs do simulador com diferentes cenários
* Comparação antes/depois de ajustes (data leakage, class weights)

---

*Submissão finalizada em: 13 de Abril de 2026*

---

### 📚 References

- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [LightGBM Documentation](https://lightgbm.readthedocs.io/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Scikit-learn Ensemble Methods](https://scikit-learn.org/stable/modules/ensemble.html)
