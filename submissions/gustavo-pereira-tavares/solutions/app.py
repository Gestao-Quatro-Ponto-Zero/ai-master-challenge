import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os
import importlib.util

sys.path.append(os.path.dirname(__file__))

# Load modules using importlib pattern
def load_module(file_path, module_name):
    """Load a Python module from file path using importlib."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

churn_model_module = load_module('churn_model.py', 'churn_model')
ChurnPredictor = churn_model_module.ChurnPredictor

risk_scoring_module = load_module('05_risk_scoring.py', 'risk_scoring')
RiskScoringEngine = risk_scoring_module.RiskScoringEngine

feature_engineering_module = load_module('02_feature_engineering.py', 'feature_engineering')
FeatureEngineer = feature_engineering_module.FeatureEngineer

preprocessing_module = load_module('01_data_preprocessing.py', 'preprocessing')
DataPreprocessor = preprocessing_module.DataPreprocessor

pdf_report_module = load_module('generate_pdf_report.py', 'pdf_report')
PDFReportGenerator = pdf_report_module.PDFReportGenerator

st.set_page_config(page_title="Dashboard de Inteligência de Churn", layout="wide", initial_sidebar_state="expanded")

st.title("📊 Dashboard de Inteligência de Churn Ravenstack")
st.markdown("**Plataforma Analítica de Churn Preditivo & Gestão de Riscos**")

# Initialize session state for simulator results
if 'simulator_results' not in st.session_state:
    st.session_state.simulator_results = []

@st.cache_resource
def load_data():
    """Load and preprocess data."""
    preprocessor = DataPreprocessor(data_path='data')
    raw_data = preprocessor.load_raw_data().merge_datasets().handle_missing_values().get_merged_data()
    
    engineer = FeatureEngineer(raw_data)
    processed_data = engineer.get_processed_data()
    
    risk_engine = RiskScoringEngine(processed_data)
    risk_engine.generate_risk_register()
    
    return processed_data, risk_engine.risk_register, risk_engine.get_risk_summary_stats(), raw_data

@st.cache_resource
def load_predictor():
    """Load the churn predictor model."""
    return ChurnPredictor()

try:
    processed_data, risk_register, risk_stats, raw_data = load_data()
    predictor = load_predictor()
except Exception as e:
    st.error(f"Error loading data or models: {e}")
    st.info("Please ensure the data files and trained models are available.")
    st.stop()

# Sidebar filters
st.sidebar.header("🔍 Filtros")
selected_industries = st.sidebar.multiselect(
    "Indústria",
    options=risk_register['industry'].unique(),
    default=risk_register['industry'].unique()
)
selected_plan_tiers = st.sidebar.multiselect(
    "Plano",
    options=risk_register['plan_tier'].unique(),
    default=risk_register['plan_tier'].unique()
)
selected_risk_tiers = st.sidebar.multiselect(
    "Nível de Risco",
    options=['Critical', 'High', 'Medium', 'Low'],
    default=['Critical', 'High', 'Medium', 'Low']
)

# Apply filters
filtered_register = risk_register[
    (risk_register['industry'].isin(selected_industries)) &
    (risk_register['plan_tier'].isin(selected_plan_tiers)) &
    (risk_register['risk_tier'].isin(selected_risk_tiers))
]

# 1. KEY METRICS
st.header("1️⃣ Visão Geral de Riscos")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total de Contas",
        f"{len(filtered_register):,}",
        f"{len(filtered_register)/len(risk_register)*100:.0f}% do total"
    )

with col2:
    critical_count = len(filtered_register[filtered_register['risk_tier'] == 'Critical'])
    st.metric(
        "🔴 Risco Crítico",
        f"{critical_count}",
        f"${filtered_register[filtered_register['risk_tier'] == 'Critical']['arr_amount'].sum():,.0f} ARR em risco"
    )

with col3:
    avg_churn_prob = filtered_register['churn_probability'].mean() * 100
    st.metric(
        "Probabilidade Média de Churn",
        f"{avg_churn_prob:.1f}%",
        delta=f"{avg_churn_prob - 18.3:.1f}% vs baseline"
    )

with col4:
    total_revenue_at_risk = (
        filtered_register[filtered_register['risk_tier'].isin(['Critical', 'High'])]['arr_amount'].sum()
    )
    st.metric(
        "💰 Receita em Risco",
        f"${total_revenue_at_risk:,.0f}",
        f"{total_revenue_at_risk/filtered_register['arr_amount'].sum()*100:.1f}% do ARR total"
    )

# 2. RISK DISTRIBUTION HEATMAP
st.header("2️⃣ Distribuição de Riscos")

col1, col2 = st.columns(2)

with col1:
    # Risk tier distribution
    risk_dist = filtered_register['risk_tier'].value_counts()
    risk_order = ['Critical', 'High', 'Medium', 'Low']
    risk_dist = risk_dist.reindex([r for r in risk_order if r in risk_dist.index])
    fig_risk = px.pie(
        values=risk_dist.values,
        names=risk_dist.index,
        title="Contas por Nível de Risco",
        color=risk_dist.index,
        color_discrete_map={'Critical': '#d62728', 'High': '#ff7f0e', 'Medium': '#ffdd57', 'Low': '#2ca02c'}
    )
    st.plotly_chart(fig_risk, use_container_width=True)

with col2:
    # Industry risk
    industry_risk = filtered_register.groupby('industry')['churn_probability'].mean().sort_values(ascending=False).head(10)
    fig_ind = px.bar(
        x=industry_risk.values * 100,
        y=industry_risk.index,
        orientation='h',
        title="Probabilidade Média de Churn por Indústria",
        labels={'x': 'Probabilidade de Churn (%)', 'y': 'Indústria'}
    )
    st.plotly_chart(fig_ind, use_container_width=True)

# 3. ACCOUNT RISK SCATTER
st.header("3️⃣ Análise de Risco de Contas")

fig_scatter = px.scatter(
    filtered_register,
    x='mrr_amount',
    y='risk_score',
    size='arr_amount',
    color='risk_tier',
    hover_data=['account_name', 'industry', 'plan_tier', 'churn_probability'],
    title='Risco da Conta vs MRR (tamanho da bolha = ARR)',
    color_discrete_map={'Critical': '#d62728', 'High': '#ff7f0e', 'Medium': '#ffdd57', 'Low': '#2ca02c'},
    labels={'mrr_amount': 'MRR ($)', 'risk_score': 'Pontuação de Risco (0-100)'}
)
st.plotly_chart(fig_scatter, use_container_width=True)

# 4. TOP ACCOUNTS AT RISK
st.header("4️⃣ Principais Contas Que Requerem Ação")

action_cols = ['account_id', 'account_name', 'industry', 'plan_tier', 'mrr_amount', 
               'churn_probability', 'risk_tier', 'primary_risk_driver']
top_risk = filtered_register[action_cols].head(25).copy()
top_risk['churn_probability'] = (top_risk['churn_probability'] * 100).round(1).astype(str) + '%'
top_risk['mrr_amount'] = top_risk['mrr_amount'].apply(lambda x: f'${x:,.0f}')

st.dataframe(top_risk, use_container_width=True)

# 5. CHURN PREDICTIVE SIMULATOR
st.header("5️⃣ 🔮 Simulador de Predição de Churn")
st.markdown("Teste diferentes cenários para prever risco de churn")

with st.expander("📋 Simulador Interativo de Cenários", expanded=True):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Parâmetros de Engajamento")
        
        adoption_rate = st.slider(
            "Taxa de Adoção de Recursos (%)",
            min_value=0, max_value=100, value=50, step=5,
            help="Percentual de recursos disponíveis sendo usados"
        )
        
        support_tickets = st.number_input(
            "Tickets de Suporte (últimos 90 dias)",
            min_value=0, max_value=50, value=5
        )
        
        avg_resolution_time = st.slider(
            "Tempo Médio de Resolução (horas)",
            min_value=0, max_value=240, value=48, step=12
        )
        
        satisfaction_score = st.slider(
            "Pontuação de Satisfação (1-5)",
            min_value=1.0, max_value=5.0, value=3.5, step=0.5
        )
    
    with col2:
        st.subheader("💰 Parâmetros da Conta")
        
        mrr_amount = st.number_input(
            "Receita Recorrente Mensal ($)",
            min_value=0, max_value=50000, value=2500, step=100
        )
        
        days_since_signup = st.slider(
            "Dias Desde o Cadastro",
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
    
    # Prediction button
    if st.button("🔮 Prever Risco de Churn", use_container_width=True):
        
        # Prepare scenario
        scenario_data = {
            'adoption_rate': adoption_rate / 100,
            'support_quality_score': satisfaction_score * (1 - min(avg_resolution_time, 100)/100),
            'support_ticket_count': support_tickets,
            'avg_resolution_time': avg_resolution_time,
            'avg_satisfaction_score': satisfaction_score,
            'mrr_amount': mrr_amount,
            'days_since_signup': days_since_signup,
            'plan_tier': plan_tier,
            'industry': industry
        }
        
        # Get prediction
        prediction = predictor.predict(scenario_data)
        
        # Store result in session state for PDF export
        result_entry = {
            'scenario': scenario_data,
            'prediction': prediction,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        st.session_state.simulator_results.append(result_entry)
        
        # Display results
        st.divider()
        st.subheader("📊 Resultados da Predição")
        
        col_result1, col_result2, col_result3 = st.columns(3)
        
        with col_result1:
            st.metric(
                "Probabilidade de Churn",
                f"{prediction['churn_probability']*100:.1f}%",
                delta=f"{prediction['churn_probability']*100 - 18.3:.1f}% vs baseline"
            )
        
        with col_result2:
            tier_colors = {
                'Critical': '🔴',
                'High': '🟠',
                'Medium': '🟡',
                'Low': '🟢'
            }
            st.metric(
                "Nível de Risco",
                f"{tier_colors.get(prediction['risk_tier'], '⚪')} {prediction['risk_tier']}"
            )
        
        with col_result3:
            st.metric(
                "Pontuação de Risco",
                f"{prediction['risk_score']}/100"
            )
        
        # Top drivers
        st.subheader("⚙️ Principais Fatores de Risco")
        drivers_df = pd.DataFrame({
            'Fator': list(prediction['top_drivers'].keys()),
            'Pontuação de Impacto': list(prediction['top_drivers'].values())
        })
        st.dataframe(drivers_df, use_container_width=True)
        
        # Recommendations
        st.subheader("💡 Ações Recomendadas")
        for i, rec in enumerate(prediction['recommendations'], 1):
            st.info(f"{i}. {rec}")
        
        # Intervention scenarios
        st.subheader("🎯 Cenários E-Se")
        
        int_col1, int_col2, int_col3 = st.columns(3)
        
        with int_col1:
            st.write("**Se adoção aumentasse para 80%:**")
            improved_scenario = scenario_data.copy()
            improved_scenario['adoption_rate'] = 0.8
            improved_pred = predictor.predict(improved_scenario)
            improvement = (prediction['churn_probability'] - improved_pred['churn_probability']) * 100
            if improvement > 0:
                st.success(f"Risco → {improved_pred['churn_probability']*100:.1f}% (-{improvement:.1f}pp)")
            else:
                st.write(f"Risco → {improved_pred['churn_probability']*100:.1f}%")
        
        with int_col2:
            st.write("**Se tempo de resolução < 24h:**")
            improved_scenario = scenario_data.copy()
            improved_scenario['avg_resolution_time'] = 24
            improved_pred = predictor.predict(improved_scenario)
            improvement = (prediction['churn_probability'] - improved_pred['churn_probability']) * 100
            if improvement > 0:
                st.success(f"Risco → {improved_pred['churn_probability']*100:.1f}% (-{improvement:.1f}pp)")
            else:
                st.write(f"Risco → {improved_pred['churn_probability']*100:.1f}%")
        
        with int_col3:
            st.write("**Se satisfação aumentasse para 4.5:**")
            improved_scenario = scenario_data.copy()
            improved_scenario['avg_satisfaction_score'] = 4.5
            improved_pred = predictor.predict(improved_scenario)
            improvement = (prediction['churn_probability'] - improved_pred['churn_probability']) * 100
            if improvement > 0:
                st.success(f"Risco → {improved_pred['churn_probability']*100:.1f}% (-{improvement:.1f}pp)")
            else:
                st.write(f"Risco → {improved_pred['churn_probability']*100:.1f}%")

# 6. EXPORT OPTIONS
st.divider()
st.header("📥 Exportar & Relatórios")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 Baixar Registro de Riscos (CSV)", use_container_width=True):
        csv = filtered_register.to_csv(index=False)
        st.download_button(
            label="Clique para baixar",
            data=csv,
            file_name=f"registro_riscos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

with col2:
    if st.button("🎯 Baixar Lista de Ações (CSV)", use_container_width=True):
        action_list = filtered_register[
            filtered_register['risk_tier'].isin(['Critical', 'High'])
        ][['account_id', 'account_name', 'industry', 'plan_tier', 'mrr_amount', 
           'risk_tier', 'primary_risk_driver', 'recommended_action']].head(100)
        csv = action_list.to_csv(index=False)
        st.download_button(
            label="Clique para baixar",
            data=csv,
            file_name=f"lista_acoes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

with col3:
    if st.button("📄 Gerar Relatório em PDF", use_container_width=True):
        with st.spinner("Gerando relatório PDF com gráficos e análises..."):
            try:
                # Debug logging
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"[DEBUG] raw_data available: {raw_data is not None}")
                logger.info(f"[DEBUG] raw_data type: {type(raw_data)}")
                logger.info(f"[DEBUG] filtered_register shape: {filtered_register.shape}")
                logger.info(f"[DEBUG] processed_data shape: {processed_data.shape}")
                
                report_gen = PDFReportGenerator(
                    filtered_register, 
                    processed_data, 
                    st.session_state.simulator_results,
                    raw_data
                )
                pdf_path = report_gen.generate_report(f'outputs/churn_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf')
                
                with open(pdf_path, 'rb') as pdf_file:
                    st.download_button(
                        label="📥 Clique para baixar PDF",
                        data=pdf_file.read(),
                        file_name=f"relatorio_churn_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                st.success("✅ Relatório PDF gerado com sucesso!")
            except Exception as e:
                st.error(f"❌ Erro ao gerar PDF: {e}")

st.divider()
st.markdown(f"✅ Dashboard Atualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Footer
st.divider()
st.markdown("""
---
**Plataforma de Inteligência de Churn Ravenstack** | Desenvolvido com Claude AI | Ensemble XGBoost & LightGBM
""")
