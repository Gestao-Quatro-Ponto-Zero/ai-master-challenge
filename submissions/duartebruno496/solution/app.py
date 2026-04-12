import streamlit as st
import pandas as pd
import os
import plotly.express as px
import math

# 1. Configuração Master (RavenStack CRM)
st.set_page_config(page_title="RavenStack | CRM Intelligence Hub", layout="wide", page_icon="📈")

# Estilo SaaS Profissional
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    div.stMetric { background-color: #ffffff; padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    [data-testid="stMetricValue"] { font-size: 32px; font-weight: 700; color: #1e293b; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ENGENHARIA DE DADOS (BLINDADA) ---
@st.cache_data
def carregar_e_tratar_mestre():
    path = "data/"
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

def motor_prioridade(df):
    if df.empty: return df
    temp = df.copy()
    hoje = temp['data'].max() if not temp['data'].isnull().all() else pd.Timestamp.now()
    temp['dias_parado'] = (hoje - temp['data']).dt.days.fillna(0).astype(int)
    def calc_score(row):
        score = 0; fase = row['fase']
        if fase == '2. Reunião': score += 65
        elif fase == '1. Prospecção': score += 30
        elif fase == '3. Ganhou': score += 100
        if row['porte_cliente'] == 'Grande (Enterprise)': score += 10
        if row['dias_parado'] > 45: score *= 0.7
        return min(int(score), 100)
    
    def calc_inteligencia(row):
        fase = row['fase']; desc = ""
        if fase == '2. Reunião': desc = "Oportunidade avançada em fase de reunião."
        elif fase == '1. Prospecção': desc = "Negociação em estágio inicial."
        elif fase == '3. Ganhou': desc = "Venda concluída com sucesso."
        if row['porte_cliente'] == 'Grande (Enterprise)': desc += " Cliente estratégico de grande porte."
        if row['dias_parado'] > 45: desc += " Atenção: Lead esfriando por falta de interação."
        return desc

    temp['nota'] = temp.apply(calc_score, axis=1)
    temp['Inteligência da Nota'] = temp.apply(calc_inteligencia, axis=1)
    temp['Status'] = temp['nota'].apply(lambda x: '🔥 Quente' if x > 80 else ('⚠️ Atenção' if x > 45 else '❄️ Frio'))
    
    def sug_acao(row):
        if row['fase'] == '4. Perdido': return "Analisar motivo da perda"
        if row['fase'] == '3. Ganhou': return "Passar para o time de Sucesso"
        if row['dias_parado'] > 60: return "Ligar imediatamente: Lead esfriando"
        if row['fase'] == '2. Reunião': return "Enviar proposta comercial"
        return "Tentar primeiro contato"
    temp['Próxima Ação'] = temp.apply(sug_acao, axis=1)
    return temp

def reset_p1():
    st.session_state.setor = []; st.session_state.vendedor = []; st.session_state.fase = []; st.session_state.acao = []
def reset_ex():
    st.session_state.set_ex = []; st.session_state.vend_ex = []; st.session_state.porte_ex = []

# --- 4. EXECUÇÃO ---
dados_mestre, p_raw, c_raw, t_raw = carregar_e_tratar_mestre()
st.sidebar.title("🏢 RavenStack CRM")
pagina = st.sidebar.radio("Navegar para:", ["🎯 Painel de Ações", "📊 Insights Executivos", "🔍 Auditoria de Dados"])

if not dados_mestre.empty:
    df_hub = motor_prioridade(dados_mestre)

    # --- TELA 1: PAINEL DE AÇÕES (COM PAGINAÇÃO) ---
    if pagina == "🎯 Painel de Ações":
        st.title("🎯 Central de Ações Prioritárias")
        if 'setor' not in st.session_state: reset_p1()

        with st.container():
            f1, f2, f3, f4 = st.columns(4)
            setor_sel = f1.multiselect("Setor", options=sorted(df_hub['sector'].unique()), key='setor')
            df_p1 = df_hub.copy()
            if setor_sel: df_p1 = df_p1[df_p1['sector'].isin(setor_sel)]

            vendedor_sel = f2.multiselect("Vendedor (Disponível)", options=sorted(df_p1['sales_agent'].unique()), key='vendedor')
            df_p2 = df_p1.copy()
            if vendedor_sel: df_p2 = df_p2[df_p2['sales_agent'].isin(vendedor_sel)]

            fase_sel = f3.multiselect("Fase (Disponível)", options=sorted(df_p2['fase'].unique()), key='fase')
            df_p3 = df_p2.copy()
            if fase_sel: df_p3 = df_p3[df_p3['fase'].isin(fase_sel)]

            acao_sel = f4.multiselect("Ação Sugerida (Disponível)", options=sorted(df_p3['Próxima Ação'].unique()), key='acao')
            st.button("🧹 Limpar Filtros", on_click=reset_p1)

        f = df_p3.copy()
        if acao_sel: f = f[f['Próxima Ação'].isin(acao_sel)]

        st.divider()
        if not f.empty:
            c1, c2, c3, c4 = st.columns(4)
            ativos = f[f['fase'].str.contains('1|2', na=False)]
            c1.metric("Dinheiro em Jogo", f"R$ {ativos['valor_final'].sum()/1e6:.1f}M")
            nota_media = int(f['nota'].mean())
            c2.metric("Qualidade das Vendas", f"{nota_media} pts", delta="Saudável" if nota_media > 45 else "Crítico", delta_color="normal" if nota_media > 45 else "inverse")
            c3.metric("Ticket Médio", f"R$ {f['valor_final'].mean()/1e3:.1f}k")
            aging_medio = int(f['dias_parado'].mean())
            c4.metric("Tempo s/ Contato", f"{aging_medio} dias", delta="No Prazo" if aging_medio < 45 else "Perigo", delta_color="normal" if aging_medio < 45 else "inverse")
            
            st.divider()
            
            # --- LÓGICA DE PAGINAÇÃO ---
            itens_por_pagina = 20
            total_itens = len(f)
            total_paginas = math.ceil(total_itens / itens_por_pagina)
            
            col_tit, col_pag = st.columns([0.8, 0.2])
            with col_tit:
                st.subheader(f"📝 Lista de Tarefas ({total_itens} registros)")
            with col_pag:
                pagina_atual = st.number_input("Página", min_value=1, max_value=total_paginas, step=1, value=1)
            
            # Fatiamento dinâmico (Slicing)
            inicio = (pagina_atual - 1) * itens_por_pagina
            fim = inicio + itens_por_pagina
            
            todo_table = f.sort_values(by='nota', ascending=False).iloc[inicio:fim]
            display_table = todo_table[['Status', 'nota', 'Inteligência da Nota', 'account', 'product', 'valor_final', 'sales_agent', 'Próxima Ação']].copy()
            display_table.columns = ['Status', 'Nota IA', 'Inteligência da Nota', 'Conta/Cliente', 'Produto', 'Valor (R$)', 'Vendedor', 'Ação Sugerida']
            
            st.dataframe(display_table, width='stretch', height=600, hide_index=True)
            st.caption(f"Mostrando {inicio+1} a {min(fim, total_itens)} de {total_itens} registros.")
            
        else: st.warning("⚠️ Nenhum dado encontrado.")

    # --- TELA 2: INSIGHTS EXECUTIVOS (CONGELADA) ---
    elif pagina == "📊 Insights Executivos":
        st.title("📊 Insights Executivos")
        if 'set_ex' not in st.session_state: reset_ex()
        with st.container():
            fi1, fi2, fi3 = st.columns(3)
            setor_ex = fi1.multiselect("Setor Estratégico", options=sorted(df_hub['sector'].unique()), key='set_ex')
            df_temp = df_hub.copy()
            if setor_ex: df_temp = df_temp[df_temp['sector'].isin(setor_ex)]
            vendedor_ex = fi2.multiselect("Time de Vendas", options=sorted(df_temp['sales_agent'].unique()), key='vend_ex')
            if vendedor_ex: df_temp = df_temp[df_temp['sales_agent'].isin(vendedor_ex)]
            
            # Normalização p/ N/A (Encapsulamento de Lista)
            opcoes_porte = sorted(list(set([str(x) if str(x).lower() not in ['nan', 'nam', 'none'] else 'N/A' for x in df_temp['porte_cliente'].unique()])))
            porte_ex = fi3.multiselect("Porte do Cliente", options=opcoes_porte, key='porte_ex')
            st.button("🧹 Resetar Dashboard", on_click=reset_ex)

        fe = df_temp.copy()
        if porte_ex: fe = fe[fe['porte_cliente'].isin(porte_ex)]
        
        if not fe.empty:
            st.divider()
            col1, col2 = st.columns([1.8, 1.2])
            with col1:
                st.subheader("🗺️ Onde o Dinheiro Mora (Top 3 Produtos Globais)")
                top3_produtos = fe.groupby('product')['valor_final'].sum().nlargest(3).index
                fe_top3 = fe[fe['product'].isin(top3_produtos)]
                fig_tree = px.treemap(fe_top3, path=['product', 'sector'], values='valor_final', color='valor_final', color_continuous_scale='Greens', labels={'valor_final': 'Fat'})
                fig_tree.update_traces(texttemplate="<b>%{label}</b><br>R$ %{value:.2s}", textinfo="label+value")
                st.plotly_chart(fig_tree, use_container_width=True)
            with col2:
                st.subheader("🤵 Performance por Vendedor & Status")
                fig_stack = px.bar(fe, x='sales_agent', y='valor_final', color='fase', color_discrete_map={'3. Ganhou': '#10B981', '4. Perdido': '#EF4444', '2. Reunião': '#3B82F6', '1. Prospecção': '#94A3B8'})
                fig_stack.update_layout(xaxis_title=None, yaxis_title=None)
                st.plotly_chart(fig_stack, use_container_width=True)
        else: st.warning("⚠️ Ajuste os filtros.")

    # --- TELA 3: AUDITORIA DE DADOS (CONGELADA) ---
    else:
        st.title("🔍 Laudo de Saúde dos Dados")
        ca1, ca2, ca3 = st.columns(3)
        ca1.metric("Vendas Gravadas", f"{p_raw.shape[0]} linhas"); ca2.metric("Empresas Cadastradas", f"{c_raw.shape[0]} contas"); ca3.metric("Time de Vendas", f"{t_raw.shape[0]} agentes")
        st.divider()
        st.subheader("🚨 Diagnóstico de Impacto de Negócio")
        nulos_df = dados_mestre.isnull().sum().reset_index()
        nulos_df.columns = ['Informação Faltante', 'Qtd de Falhas']
        impacto_map = {
            'account': 'Clientes sem nome (Impossível identificar a origem do dinheiro)',
            'engage_date': 'Falta data de entrada (Impede saber a velocidade da venda)',
            'close_date': 'Falta data prevista (Dificulta a previsão de fluxo de caixa)',
            'close_value': 'Vendas sem valor (Afeta diretamente o cálculo de lucro)',
            'sector': 'Setor não identificado (Impede saber quais ramos são mais rentáveis)',
            'year_established': 'Falta ano de fundação (Dificulta análise de maturidade do cliente)',
            'revenue': 'Faturamento ausente (Impede classificar o porte da conta/Tier)',
            'employees': 'Falta nº de funcionários (Dificulta entender a escala do cliente)',
            'office_location': 'Sede desconhecida (Impacta estratégias regionais e logística)',
            'subsidiary_of': 'Falta vínculo de grupo (Impede ver conexões entre empresas)',
            'manager': 'Vendedor sem gestor (Falha na hierarquia e cobrança)',
            'data': 'Erro no tratamento de tempo (Afeta todos os cálculos de IA)',
            'porte_cliente': 'Porte do cliente não mapeado (Impede segmentação por faturamento)'
        }
        nulos_df['O que isso significa?'] = nulos_df['Informação Faltante'].map(impacto_map).fillna("Dado técnico em falta")
        st.table(nulos_df[nulos_df['Qtd de Falhas'] > 0])
        st.divider()
        st.subheader("📋 Tabela Integrada Dinâmica")
        st.dataframe(dados_mestre, width='stretch', hide_index=True)
else:
    st.error("Erro Crítico na pasta /data.")