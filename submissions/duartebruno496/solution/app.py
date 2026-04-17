import streamlit as st
import pandas as pd
import os
import plotly.express as px
import math

# 1. CONFIGURAÇÃO MASTER E ESTILIZAÇÃO
st.set_page_config(page_title="RavenStack | CRM Intelligence Hub", layout="wide", page_icon="📈")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    div.stMetric { background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    [data-testid="stMetricValue"] { font-size: 26px; font-weight: 700; color: #1e293b; }
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. ENGENHARIA DE DADOS (CRUZAMENTO DE 4 TABELAS) ---
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
        
        df['margem_pct'] = df.apply(lambda x: (x['valor_final'] / x['valor_base']) if x['valor_base'] > 0 else 1.0, axis=1)
        
        mapa_setores = {
            'retail': 'Varejo', 'medical': 'Saúde', 'software': 'Software/TI',
            'services': 'Serviços', 'entertainment': 'Entretenimento', 
            'finance': 'Finanças', 'employment': 'Recrutamento/RH', 
            'telecommunications': 'Telecom', 'technology': 'Tecnologia', 
            'technolgy': 'Tecnologia', 'marketing': 'Marketing'
        }
        df['sector'] = df['sector'].map(mapa_setores).fillna(df['sector'])
        df['office_location'] = df['regional_office'].fillna("Não Informado")
        
        for col in ['sector', 'sales_agent', 'product', 'office_location', 'manager']:
            df[col] = df[col].fillna("Não Informado").astype(str)
            
        df['data_eng'] = pd.to_datetime(df['engage_date'], errors='coerce')
        ordem_fase = {'Prospecting': '1. Prospecção', 'Engaging': '2. Reunião', 'Won': '3. Ganhou', 'Lost': '4. Perdido'}
        df['fase'] = df['deal_stage'].map(ordem_fase).fillna('1. Prospecção')
        
        return df, pipe, contas, teams, produtos
    except Exception as e:
        st.error(f"Erro Crítico de Dados: {e}"); return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# --- 3. MOTOR DE SCORING (RIGOR G4: DESFECHO REAL) ---
def motor_prioridade(df):
    if df.empty: return df
    temp = df.copy()
    df_desfecho = df[df['deal_stage'].isin(['Won', 'Lost'])]
    win_rate_produto = df_desfecho[df_desfecho['deal_stage'] == 'Won'].groupby('product').size() / df_desfecho.groupby('product').size()
    taxa_media_geral = df_desfecho[df_desfecho['deal_stage'] == 'Won'].shape[0] / df_desfecho.shape[0]
    win_rate_produto = win_rate_produto.fillna(taxa_media_geral)
    
    hoje = temp['data_eng'].max() if not temp['data_eng'].isnull().all() else pd.Timestamp.now()
    temp['dias_parado'] = (hoje - temp['data_eng']).dt.days.fillna(0).astype(int)

    def calc_score(row):
        score = 50
        taxa_prod = win_rate_produto.get(row['product'], taxa_media_geral)
        score += (taxa_prod - 0.5) * 40 
        if row['fase'] == '2. Reunião': score += 20
        elif row['fase'] == '3. Ganhou': return 100
        elif row['fase'] == '4. Perdido': return 0
        if row['dias_parado'] > 45: score -= (row['dias_parado'] - 45) * 0.6
        return max(0, min(int(score), 100))
    
    def calc_inteligencia(row):
        nota = calc_score(row)
        desc = f"Score {nota}: "
        if row['product'] in win_rate_produto and win_rate_produto[row['product']] > 0.6: desc += "Alta conversão histórica."
        else: desc += "Performance média histórica."
        if row['dias_parado'] > 45: desc += " Alerta: Aging elevado."
        return desc

    temp['nota'] = temp.apply(calc_score, axis=1)
    temp['Inteligência da Nota'] = temp.apply(calc_inteligencia, axis=1)
    temp['Status'] = temp['nota'].apply(lambda x: '🔥 Quente' if x > 75 else ('⚠️ Atenção' if x > 40 else '❄️ Frio'))
    
    def sug_acao(row):
        if row['fase'] == '4. Perdido': return "Analisar motivo da perda"
        if row['fase'] == '3. Ganhou': return "Passar para Sucesso"
        if row['dias_parado'] > 60: return "Ligar imediatamente"
        if row['fase'] == '2. Reunião': return "Enviar proposta"
        return "Tentar primeiro contato"
    temp['Próxima Ação'] = temp.apply(sug_acao, axis=1)
    return temp

# --- 4. FORMATADORES E RESETS ---
def format_brl(val):
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def reset_p1():
    st.session_state.p1_set = []; st.session_state.p1_vend = []; 
    st.session_state.p1_fase = []; st.session_state.p1_acao = []

def reset_intel():
    st.session_state.int_set = []; st.session_state.int_vend = []; 
    st.session_state.int_ger = []; st.session_state.int_loc = []

# --- 5. CARREGAMENTO E NAVEGAÇÃO ---
dados_mestre, p_raw, c_raw, t_raw, prod_raw = carregar_e_tratar_mestre()

st.sidebar.title("🏢 RavenStack CRM")
pagina = st.sidebar.radio("Navegar para:", ["🎯 Painel de Ações", "🏢 Inteligência de Mercado", "🔍 Auditoria de Dados"])

if not dados_mestre.empty:
    df_hub = motor_prioridade(dados_mestre)

    # --- PÁGINA 1: PAINEL DE AÇÕES ---
    if pagina == "🎯 Painel de Ações":
        st.title("🎯 Central de Ações Prioritárias")
        
        if 'p1_set' not in st.session_state: reset_p1()

        with st.container():
            f1, f2, f3, f4 = st.columns(4)
            set_sel = f1.multiselect("Setor", options=sorted(df_hub['sector'].unique()), key='p1_set')
            df_p = df_hub.copy()
            if set_sel: df_p = df_p[df_p['sector'].isin(set_sel)]
            
            vend_sel = f2.multiselect("Vendedor", options=sorted(df_p['sales_agent'].unique()), key='p1_vend')
            if vend_sel: df_p = df_p[df_p['sales_agent'].isin(vend_sel)]
            
            fase_sel = f3.multiselect("Fase", options=sorted(df_p['fase'].unique()), key='p1_fase')
            if fase_sel: df_p = df_p[df_p['fase'].isin(fase_sel)]
            
            acao_sel = f4.multiselect("Ação", options=sorted(df_p['Próxima Ação'].unique()), key='p1_acao')
            if acao_sel: df_p = df_p[df_p['Próxima Ação'].isin(acao_sel)]
            
            st.button("🧹 Limpar todos os filtros", on_click=reset_p1, key='btn_p1')

        st.divider()

        # Cards de Apoio
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Leads Filtrados", len(df_p))
        with c2: st.metric("Fase Predominante", df_p['fase'].mode()[0] if not df_p.empty else "-")
        with c3: st.metric("Ação Prioritária", df_p['Próxima Ação'].mode()[0] if not df_p.empty else "-")
        with c4: st.metric("Volume Financeiro", format_brl(df_p['valor_final'].sum()))

        st.divider()
        
        # Lista de Tarefas
        itens_pg = 15
        total_pag = math.ceil(len(df_p) / itens_pg)
        ct, cp = st.columns([0.8, 0.2])
        with ct: st.subheader(f"📝 Lista de Tarefas ({len(df_p)} registros)")
        with cp: p_atual = st.number_input("Página", 1, max(1, total_pag), 1)
        
        inicio = (p_atual - 1) * itens_pg
        df_disp = df_p.sort_values(by='nota', ascending=False).iloc[inicio:inicio+itens_pg][
            ['Status', 'nota', 'Inteligência da Nota', 'account', 'product', 'valor_final', 'sales_agent', 'Próxima Ação']
        ]
        df_disp['valor_final'] = df_disp['valor_final'].apply(format_brl)
        df_disp.columns = ['Status', 'Nota IA', 'Inteligência da Nota', 'Conta', 'Produto', 'Valor', 'Vendedor', 'Ação Sugerida']
        st.dataframe(df_disp, width='stretch', hide_index=True)

        st.divider()
        st.subheader("🏆 Histórico de Sucesso: Leads Ganhos por Vendedor")
        df_won_v = df_hub[df_hub['deal_stage'] == 'Won'].groupby('sales_agent').size().reset_index(name='Ganhos')
        st.plotly_chart(px.bar(df_won_v.sort_values('Ganhos', ascending=False), x='sales_agent', y='Ganhos', color='Ganhos', labels={'sales_agent': 'Vendedor'}, color_continuous_scale='Greens'), use_container_width=True)

    # --- PÁGINA 2: INTELIGÊNCIA DE MERCADO ---
    elif pagina == "🏢 Inteligência de Mercado":
        st.title("🏢 Inteligência de Mercado e Planejamento")
        
        if 'int_set' not in st.session_state: reset_intel()

        with st.expander("🛠️ Filtros Analíticos Expandidos", expanded=True):
            ca, cb, cc, cd = st.columns(4)
            set_i = ca.multiselect("Setor Estratégico", options=sorted(df_hub['sector'].unique()), key='int_set')
            df_i = df_hub.copy()
            if set_i: df_i = df_i[df_i['sector'].isin(set_i)]
            
            vend_i = cb.multiselect("Vendedor", options=sorted(df_i['sales_agent'].unique()), key='int_vend')
            if vend_i: df_i = df_i[df_i['sales_agent'].isin(vend_i)]
            
            ger_i = cc.multiselect("Gerente", options=sorted(df_i['manager'].unique()), key='int_ger')
            if ger_i: df_i = df_i[df_i['manager'].isin(ger_i)]
            
            loc_i = cd.multiselect("Localidade", options=sorted(df_i['office_location'].unique()), key='int_loc')
            if loc_i: df_i = df_i[df_i['office_location'].isin(loc_i)]
            
            st.button("🧹 Limpar todos os filtros", on_click=reset_intel, key='btn_int')

        m1, m2, m3 = st.columns(3)
        df_w = df_i[df_i['deal_stage'] == 'Won']
        df_c = df_i[df_i['deal_stage'].isin(['Won', 'Lost'])]
        m1.metric("Margem Média Retida (Won)", f"{(df_w['margem_pct'].mean() * 100) if not df_w.empty else 0:.1f}%")
        m2.metric("Taxa de Conversão Real", f"{(len(df_w)/len(df_c)*100) if not df_c.empty else 0:.1f}%")
        m3.metric("Faturamento Filtrado", format_brl(df_i['valor_final'].sum()))

        st.divider()
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("🏆 Performance por Equipe (Gerente)")
            df_manager = df_i.groupby('manager')['valor_final'].sum().reset_index().sort_values('valor_final', ascending=False)
            st.plotly_chart(px.bar(df_manager, x='manager', y='valor_final', color='valor_final', labels={'manager': 'Gerente', 'valor_final': 'Valor'}, color_continuous_scale='Viridis'), use_container_width=True)

        with col_g2:
            st.subheader("📍 Faturamento por Localidade Regional")
            df_loc = df_i.groupby('office_location')['valor_final'].sum().reset_index().sort_values('valor_final', ascending=False)
            st.plotly_chart(px.bar(df_loc, x='office_location', y='valor_final', color='valor_final', labels={'office_location': 'Localidade', 'valor_final': 'Valor'}, color_continuous_scale='Blues'), use_container_width=True)

        st.divider()
        st.subheader("📋 Performance Estratégica por Setor")
        df_s = df_i.groupby('sector').agg(leads=('opportunity_id', 'count'), margem=('margem_pct', lambda x: x.mean() * 100), total=('valor_final', 'sum')).reset_index()
        df_s['Margem Média (%)'] = df_s['margem'].map("{:.1f}%".format)
        df_s['Faturamento Total'] = df_s['total'].apply(format_brl)
        df_f = df_s[['sector', 'leads', 'Margem Média (%)', 'Faturamento Total']]
        df_f.columns = ['Setor', 'Qtd de Leads', 'Margem Média', 'Faturamento Total (BRL)']
        st.dataframe(df_f.sort_values('Setor'), width='stretch', hide_index=True)

    # --- PÁGINA 3: AUDITORIA DE DADOS ---
    else:
        st.title("🔍 Laudo de Saúde dos Dados")
        st.metric("Total de Registros Processados", len(dados_mestre))
        nulos = dados_mestre.isnull().sum().reset_index()
        nulos.columns = ['Campo', 'Falhas']
        imp = {'revenue': 'Impede Tiering.', 'employees': 'Dificulta escala.', 'manager': 'Falha na hierarquia.', 'close_value': 'Subestima faturamento.'}
        nulos['Impacto Estratégico'] = nulos['Campo'].map(imp)
        st.table(nulos[nulos['Falhas'] > 0].dropna(subset=['Impacto Estratégico']))
        st.subheader("📋 Dataset Consolidado (Amostra)")
        st.dataframe(dados_mestre.head(100), width='stretch')
else:
    st.error("Erro Crítico: CSVs não encontrados.")