import streamlit as st
import pandas as pd
import os
import plotly.express as px
import math

# 1. Configuração Master (Consistência Total)
st.set_page_config(page_title="RavenStack | CRM Intelligence Hub", layout="wide", page_icon="📈")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    div.stMetric { background-color: #ffffff; padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    [data-testid="stMetricValue"] { font-size: 32px; font-weight: 700; color: #1e293b; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ENGENHARIA DE DADOS (BLINDADA COM PATH DINÂMICO) ---
@st.cache_data
def carregar_e_tratar_mestre():
    base_path = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_path, "data")
    
    try:
        pipe = pd.read_csv(os.path.join(path, "sales_pipeline.csv"))
        contas = pd.read_csv(os.path.join(path, "accounts.csv"))
        teams = pd.read_csv(os.path.join(path, "sales_teams.csv"))
        produtos = pd.read_csv(os.path.join(path, "products.csv"))
        
        pipe['account'] = pipe['account'].fillna("Desconhecido").str.strip()
        contas['account'] = contas['account'].str.strip()
        df = pd.merge(pipe, contas, on='account', how='left')
        df = pd.merge(df, teams, on='sales_agent', how='left')
        
        dict_precos = produtos.set_index('product')['sales_price'].to_dict()
        df['valor_base'] = df['product'].map(dict_precos).fillna(0)
        df['valor_real'] = pd.to_numeric(df['close_value'], errors='coerce').fillna(0)
        df['valor_final'] = df.apply(lambda x: x['valor_real'] if x['valor_real'] > 0 else x['valor_base'], axis=1)
        
        mapa_setores = {
            'retail': 'Varejo', 'medical': 'Saúde', 'software': 'Software/TI', 
            'services': 'Serviços', 'entertainment': 'Entretenimento', 
            'finance': 'Finanças', 'employment': 'Recrutamento/RH', 
            'telecommunications': 'Telecom', 'technology': 'Tecnologia', 
            'technolgy': 'Tecnologia', 'marketing': 'Marketing'
        }
        df['sector'] = df['sector'].map(mapa_setores).fillna(df['sector'])
        
        df['porte_cliente'] = pd.cut(df['revenue'], bins=[0, 1000, 3000, float('inf')], 
                                    labels=['Pequeno (SMB)', 'Médio (Mid)', 'Grande (Enterprise)'])
        df['porte_cliente'] = df['porte_cliente'].astype(str).replace(['nan', 'nam', 'None', 'null'], 'N/A')
        
        for col in ['sector', 'sales_agent', 'product', 'office_location', 'subsidiary_of', 'manager']:
            df[col] = df[col].fillna("Não Informado").astype(str)
            
        df['data'] = pd.to_datetime(df['engage_date'], errors='coerce')
        df['data'] = df['data'].fillna(df['data'].mode()[0] if not df['data'].empty else pd.Timestamp.now())
        
        ordem_fase = {'Prospecting': '1. Prospecção', 'Engaging': '2. Reunião', 'Won': '3. Ganhou', 'Lost': '4. Perdido'}
        df['fase'] = df['deal_stage'].map(ordem_fase).fillna('1. Prospecção')
        return df, pipe, contas, teams
    except Exception as e:
        st.error(f"Erro Crítico: {e}"); return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# --- 3. MOTOR DE SCORING (FUNDAMENTADO EM DADOS HISTÓRICOS - G4) ---
def motor_prioridade(df):
    if df.empty: return df
    temp = df.copy()
    
    # Win-Rate Histórico Real por Produto
    win_rate_produto = df[df['deal_stage'] == 'Won'].groupby('product').size() / df.groupby('product').size()
    win_rate_produto = win_rate_produto.fillna(df[df['deal_stage'] == 'Won'].shape[0] / df.shape[0])
    
    hoje = temp['data'].max() if not temp['data'].isnull().all() else pd.Timestamp.now()
    temp['dias_parado'] = (hoje - temp['data']).dt.days.fillna(0).astype(int)

    def calc_score(row):
        score = 50 
        taxa_prod = win_rate_produto.get(row['product'], 0.5)
        score += (taxa_prod - 0.5) * 40 
        
        if row['fase'] == '2. Reunião': score += 20
        elif row['fase'] == '3. Ganhou': return 100
        elif row['fase'] == '4. Perdido': return 0
        
        if row['dias_parado'] > 45:
            score -= (row['dias_parado'] - 45) * 0.6
        return max(0, min(int(score), 100))
    
    def calc_inteligencia(row):
        nota = calc_score(row)
        desc = f"Score {nota}: "
        if row['product'] in win_rate_produto and win_rate_produto[row['product']] > 0.6:
            desc += "Alta conversão histórica do produto."
        else:
            desc += "Performance média histórica."
        if row['dias_parado'] > 45:
            desc += " Alerta: Lead estagnado (Aging)."
        return desc

    temp['nota'] = temp.apply(calc_score, axis=1)
    temp['Inteligência da Nota'] = temp.apply(calc_inteligencia, axis=1)
    temp['Status'] = temp['nota'].apply(lambda x: '🔥 Quente' if x > 75 else ('⚠️ Atenção' if x > 40 else '❄️ Frio'))
    
    def sug_acao(row):
        if row['fase'] == '4. Perdido': return "Analisar motivo da perda"
        if row['fase'] == '3. Ganhou': return "Passar para o time de Sucesso"
        if row['dias_parado'] > 60: return "Ligar imediatamente"
        if row['fase'] == '2. Reunião': return "Enviar proposta"
        return "Tentar primeiro contato"
    temp['Próxima Ação'] = temp.apply(sug_acao, axis=1)
    return temp

# --- 4. FUNÇÕES DE RESET ---
def reset_p1():
    st.session_state.setor = []; st.session_state.vendedor = []; st.session_state.fase = []; st.session_state.acao = []
def reset_ex():
    st.session_state.set_ex = []; st.session_state.vend_ex = []; st.session_state.porte_ex = []

dados_mestre, p_raw, c_raw, t_raw = carregar_e_tratar_mestre()
st.sidebar.title("🏢 RavenStack CRM")
pagina = st.sidebar.radio("Navegar para:", ["🎯 Painel de Ações", "📊 Insights Executivos", "🔍 Auditoria de Dados"])

if not dados_mestre.empty:
    df_hub = motor_prioridade(dados_mestre)

    if pagina == "🎯 Painel de Ações":
        st.title("🎯 Central de Ações Prioritárias")
        if 'setor' not in st.session_state: reset_p1()
        with st.container():
            f1, f2, f3, f4 = st.columns(4)
            setor_sel = f1.multiselect("Setor", options=sorted(df_hub['sector'].unique()), key='setor')
            df_p1 = df_hub.copy()
            if setor_sel: df_p1 = df_p1[df_p1['sector'].isin(setor_sel)]
            vendedor_sel = f2.multiselect("Vendedor", options=sorted(df_p1['sales_agent'].unique()), key='vendedor')
            df_p2 = df_p1.copy()
            if vendedor_sel: df_p2 = df_p2[df_p2['sales_agent'].isin(vendedor_sel)]
            fase_sel = f3.multiselect("Fase", options=sorted(df_p2['fase'].unique()), key='fase')
            df_p3 = df_p2.copy()
            if fase_sel: df_p3 = df_p3[df_p3['fase'].isin(fase_sel)]
            acao_sel = f4.multiselect("Ação", options=sorted(df_p3['Próxima Ação'].unique()), key='acao')
            st.button("🧹 Limpar Filtros", on_click=reset_p1)

        f = df_p3.copy()
        if acao_sel: f = f[f['Próxima Ação'].isin(acao_sel)]

        st.divider()
        itens_pg = 20
        total_pag = math.ceil(len(f) / itens_pg)
        col_tit, col_pag = st.columns([0.8, 0.2])
        with col_tit: st.subheader(f"📝 Lista de Tarefas ({len(f)} registros)")
        with col_pag: p_atual = st.number_input("Página", 1, max(1, total_pag), 1)
        
        inicio = (p_atual - 1) * itens_pg
        df_display = f.sort_values(by='nota', ascending=False).iloc[inicio:inicio+itens_pg][
            ['Status', 'nota', 'Inteligência da Nota', 'account', 'product', 'valor_final', 'sales_agent', 'Próxima Ação']
        ]

        # Cabeçalhos Corrigidos e Traduzidos (EXCLUSIVO UX)
        df_display.columns = [
            'Status', 'Nota IA', 'Inteligência da Nota', 'Conta', 
            'Produto', 'Valor (R$)', 'Vendedor', 'Ação Sugerida'
        ]

        st.dataframe(df_display, width='stretch', hide_index=True)

    elif pagina == "📊 Insights Executivos":
        st.title("📊 Insights Executivos")
        if 'set_ex' not in st.session_state: reset_ex()
        with st.container():
            fi1, fi2, fi3 = st.columns(3)
            setor_ex = fi1.multiselect("Setor Estratégico", options=sorted(df_hub['sector'].unique()), key='set_ex')
            df_temp = df_hub.copy()
            if setor_ex: df_temp = df_temp[df_temp['sector'].isin(setor_ex)]
            vendedor_ex = fi2.multiselect("Vendedores", options=sorted(df_temp['sales_agent'].unique()), key='vend_ex')
            if vendedor_ex: df_temp = df_temp[df_temp['sales_agent'].isin(vendedor_ex)]
            opcoes_porte = sorted(list(set([str(x) if str(x).lower() not in ['nan', 'nam'] else 'N/A' for x in df_temp['porte_cliente'].unique()])))
            porte_ex = fi3.multiselect("Porte do Cliente", options=opcoes_porte, key='porte_ex')
            st.button("🧹 Resetar Dashboard", on_click=reset_ex)

        st.divider()
        fe = df_temp.copy()
        if porte_ex: fe = fe[fe['porte_cliente'].isin(porte_ex)]
        
        c1, c2 = st.columns([1.8, 1.2])
        with c1:
            st.subheader("🗺️ Onde o Dinheiro Mora (Top 3 Produtos)")
            top3 = fe.groupby('product')['valor_final'].sum().nlargest(3).index
            st.plotly_chart(px.treemap(fe[fe['product'].isin(top3)], path=['product', 'sector'], values='valor_final', color='valor_final', color_continuous_scale='Greens'), use_container_width=True)
        with c2:
            st.subheader("🤵 Performance por Vendedor")
            st.plotly_chart(px.bar(fe, x='sales_agent', y='valor_final', color='fase'), use_container_width=True)

    else:
        # --- AUDITORIA DE DADOS (TEXTOS REAIS EXPLICATIVOS) ---
        st.title("🔍 Laudo de Saúde dos Dados")
        st.metric("Vendas Processadas", f"{p_raw.shape[0]} registros")
        
        st.subheader("🚨 Diagnóstico de Integridade")
        nulos_df = dados_mestre.isnull().sum().reset_index()
        nulos_df.columns = ['Informação Faltante', 'Qtd de Falhas']
        
        impacto_map = {
            'revenue': 'Faturamento ausente (impede classificar o porte da conta/tier)',
            'employees': 'Falta nº de funcionários (Dificulta entender a escala do cliente)',
            'office_location': 'Sede desconhecida (Impacta estratégias regionais e logística)',
            'subsidiary_of': 'Falta vínculo de grupo (Impede ver conexões entre empresas)',
            'manager': 'Vendedor sem gestor (Falha na hierarquia e cobrança)',
            'data': 'Erro no tratamento de tempo (Afeta todos os cálculos de IA)',
            'porte_cliente': 'Porte do cliente não mapeado (Impede segmentação por faturamento)',
            'close_value': 'Valor de fechamento ausente (Gera subestimação do faturamento real)'
        }
        
        nulos_df['O que isso significa?'] = nulos_df['Informação Faltante'].map(impacto_map)
        # Filtramos apenas as falhas reais com impacto mapeado
        nulos_df = nulos_df[(nulos_df['Qtd de Falhas'] > 0) & (nulos_df['O que isso significa?'].notnull())]
        
        st.table(nulos_df)
        
        st.divider()
        st.subheader("📋 Tabela Integrada Dinâmica")
        st.dataframe(dados_mestre, width='stretch', hide_index=True)
else:
    st.error("Erro Crítico na pasta /data.")