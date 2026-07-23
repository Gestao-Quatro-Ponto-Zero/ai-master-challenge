import streamlit as st
import pandas as pd
import plotly.express as px
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_openai import ChatOpenAI
import os

st.set_page_config(page_title="RavenStack Churn Dashboard", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("master_table.csv")
    return df

df = load_data()

st.sidebar.title("Configurações")
st.sidebar.markdown("Para conversar com seus dados, insira sua chave da OpenAI:")
openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")

st.title("📊 RavenStack - Churn & Analytics Dashboard")
st.markdown("Insights consolidados sobre uso, suporte e faturamento para identificar o risco real de churn.")

tab1, tab2 = st.tabs(["Visão Geral", "💬 Chatbot com os Dados (LLM)"])

with tab1:
    col1, col2, col3 = st.columns(3)
    churn_rate = df['churn_flag'].mean() * 100
    avg_mrr = df['current_mrr'].mean()
    total_mrr_lost = df[df['churn_flag']==True]['refund_amount_usd'].sum() # Example metric

    col1.metric("Taxa Global de Churn", f"{churn_rate:.1f}%")
    col2.metric("MRR Médio por Conta", f"${avg_mrr:,.0f}")
    col3.metric("Uso Médio (Últimos 30d)", f"{df['usage_last_30'].mean():.1f}")
    
    st.divider()
    
    st.markdown("### Churn por Indústria")
    industry_churn = df.groupby('industry')['churn_flag'].mean().reset_index()
    industry_churn['churn_flag'] = industry_churn['churn_flag'] * 100
    fig_ind = px.bar(industry_churn.sort_values('churn_flag', ascending=False), 
                     x='industry', y='churn_flag', 
                     color='churn_flag', color_continuous_scale='Reds',
                     labels={'churn_flag': 'Taxa de Churn (%)', 'industry': 'Indústria'})
    st.plotly_chart(fig_ind, use_container_width=True)
    
    col4, col5 = st.columns(2)
    with col4:
        st.markdown("### Uso de Features (Últimos 30 Dias)")
        fig_use = px.box(df, x='churn_flag', y='usage_last_30', color='churn_flag',
                         labels={'churn_flag': 'Deu Churn?', 'usage_last_30': 'Volume de Uso (30d)'})
        st.plotly_chart(fig_use, use_container_width=True)
    
    with col5:
        st.markdown("### Tempo de Resolução (Suporte)")
        fig_sup = px.box(df, x='churn_flag', y='avg_resolution_hours', color='churn_flag',
                         labels={'churn_flag': 'Deu Churn?', 'avg_resolution_hours': 'Tempo Médio Resolução (h)'})
        st.plotly_chart(fig_sup, use_container_width=True)

    st.markdown("### Visão Detalhada dos Clientes")
    st.dataframe(df[['account_id', 'industry', 'current_mrr', 'usage_last_30', 'num_tickets', 'churn_flag', 'reason_code']])

with tab2:
    st.markdown("### Analista de Dados Virtual")
    st.markdown("Pergunte qualquer coisa sobre a base de dados (`master_table.csv`). O agente escreverá e executará o código Pandas em background para te responder.")
    
    if not openai_api_key:
        st.warning("Por favor, insira sua chave de API da OpenAI na barra lateral para habilitar o chat.")
    else:
        # Initialize Agent
        os.environ["OPENAI_API_KEY"] = openai_api_key
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        agent = create_pandas_dataframe_agent(
            llm, 
            df, 
            verbose=True, 
            agent_type="openai-tools",
            allow_dangerous_code=True # Required by langchain-experimental for pandas agents
        )
        
        if "messages" not in st.session_state:
            st.session_state.messages = []
            
        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])
            
        if prompt := st.chat_input("Ex: Qual indústria tem o maior faturamento total (current_mrr) mas também o maior churn?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Analisando os dados..."):
                    try:
                        response = agent.invoke(prompt)
                        st.write(response["output"])
                        st.session_state.messages.append({"role": "assistant", "content": response["output"]})
                    except Exception as e:
                        st.error(f"Ocorreu um erro: {e}")
                        
