"""
RavenStack Churn Diagnosis Dashboard
=====================================
Dashboard interativo com diagnóstico, modelo preditivo e recomendações.

Challenge 001 — AI Master Challenge (G4 Educação)
Author: Theo Garcia

Processo:
- Comecei validando integridade referencial entre as 5 tabelas
- Criei master table com 55 colunas agregadas por account_id
- Descobri que as médias mascaram o problema (churned ≈ retidos)
- Foquei na análise segmentada que revelou os drivers reais
- Modelo preditivo ficou com F1 baixo (0.098) — mantive como
  complemento mas o valor real está na análise segmentada
- Parte 4: risk scoring rule-based (0-100) baseado nos achados
  da análise segmentada — funciona melhor que ML neste caso
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ============================================
# CONFIG & THEME
# ============================================
st.set_page_config(
    page_title="RavenStack — Diagnóstico de Churn",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Consistent color palette (accessibility-friendly)
COLORS = {
    'danger': '#dc2626',
    'warning': '#f59e0b',
    'success': '#16a34a',
    'primary': '#2563eb',
    'muted': '#6b7280',
}

# ============================================
# DATA LOADING
# ============================================
@st.cache_data
def load_data():
    accounts = pd.read_csv('data/ravenstack_accounts.csv')
    subs = pd.read_csv('data/ravenstack_subscriptions.csv')
    usage = pd.read_csv('data/ravenstack_feature_usage.csv')
    tickets = pd.read_csv('data/ravenstack_support_tickets.csv')
    churn_events = pd.read_csv('data/ravenstack_churn_events.csv')
    master = pd.read_csv('data/master_churn_analysis.csv')

    # Parse dates
    accounts['signup_date'] = pd.to_datetime(accounts['signup_date'])
    subs['start_date'] = pd.to_datetime(subs['start_date'])
    subs['end_date'] = pd.to_datetime(subs['end_date'])
    churn_events['churn_date'] = pd.to_datetime(churn_events['churn_date'])
    tickets['submitted_at'] = pd.to_datetime(tickets['submitted_at'])

    return accounts, subs, usage, tickets, churn_events, master

accounts, subs, usage, tickets, churn_events, master = load_data()

# ============================================
# SIDEBAR FILTERS
# ============================================
st.sidebar.title("Filtros")

industries = st.sidebar.multiselect(
    "Indústria",
    options=sorted(master['industry'].unique()),
    default=sorted(master['industry'].unique())
)

plans = st.sidebar.multiselect(
    "Plano",
    options=sorted(master['plan_tier'].unique()),
    default=sorted(master['plan_tier'].unique())
)

countries = st.sidebar.multiselect(
    "País",
    options=sorted(master['country'].unique()),
    default=sorted(master['country'].unique())
)

# Apply filters
filtered = master[
    (master['industry'].isin(industries)) &
    (master['plan_tier'].isin(plans)) &
    (master['country'].isin(countries))
]

# ============================================
# TABS
# ============================================
tab1, tab2, tab3 = st.tabs(["📊 Diagnóstico", "🔮 Preditiva", "🎯 Recomendações"])

# ============================================
# TAB 1: DIAGNÓSTICO
# ============================================
with tab1:
    st.title("Diagnóstico de Churn — RavenStack")
    st.caption(f"Analisando {len(filtered)} contas | Filtros aplicados: {len(industries)} indústrias, {len(plans)} planos, {len(countries)} países")

    # --- KPIs ---
    col1, col2, col3, col4, col5 = st.columns(5)

    total_accounts = len(filtered)
    churned_accounts = filtered['churn_flag'].sum()
    churn_rate = churned_accounts / total_accounts if total_accounts > 0 else 0
    mrr_at_risk = filtered['mrr_at_risk'].sum()
    total_mrr = filtered['latest_mrr'].sum()
    accounts_with_events = filtered[filtered['total_churn_events'] > 0].shape[0]

    col1.metric("Contas Totais", f"{total_accounts}")
    col2.metric("Churn Rate", f"{churn_rate:.1%}", delta=f"{churned_accounts} contas", delta_color="inverse")
    col3.metric("MRR em Risco", f"${mrr_at_risk:,.0f}")
    col4.metric("MRR Total", f"${total_mrr:,.0f}")
    col5.metric("Já Churnearam (alguma vez)", f"{accounts_with_events}", delta=f"{accounts_with_events/total_accounts:.0%} das contas", delta_color="inverse")

    st.divider()

    # --- ROW 1: Churn by Segment ---
    st.subheader("Onde o churn se concentra?")
    col_a, col_b = st.columns(2)

    with col_a:
        # Churn by industry
        ind_data = filtered.groupby('industry').agg(
            accounts=('account_id', 'count'),
            churn_rate=('churn_flag', 'mean'),
            mrr_lost=('mrr_at_risk', 'sum')
        ).reset_index().sort_values('churn_rate', ascending=True)

        fig_ind = px.bar(
            ind_data, y='industry', x='churn_rate',
            orientation='h',
            color='churn_rate',
            color_continuous_scale='RdYlGn_r',
            text=ind_data['churn_rate'].apply(lambda x: f'{x:.1%}'),
            title='Churn Rate por Indústria',
            labels={'churn_rate': 'Churn Rate', 'industry': ''}
        )
        fig_ind.update_traces(textposition='outside')
        fig_ind.update_layout(coloraxis_showscale=False, height=350)
        fig_ind.add_vline(x=churn_rate, line_dash="dash", line_color="gray",
                          annotation_text=f"Média: {churn_rate:.1%}")
        st.plotly_chart(fig_ind, use_container_width=True)

    with col_b:
        # Churn by referral source
        ref_data = filtered.groupby('referral_source').agg(
            accounts=('account_id', 'count'),
            churn_rate=('churn_flag', 'mean'),
            mrr_lost=('mrr_at_risk', 'sum')
        ).reset_index().sort_values('churn_rate', ascending=True)

        fig_ref = px.bar(
            ref_data, y='referral_source', x='churn_rate',
            orientation='h',
            color='churn_rate',
            color_continuous_scale='RdYlGn_r',
            text=ref_data['churn_rate'].apply(lambda x: f'{x:.1%}'),
            title='Churn Rate por Canal de Aquisição',
            labels={'churn_rate': 'Churn Rate', 'referral_source': ''}
        )
        fig_ref.update_traces(textposition='outside')
        fig_ref.update_layout(coloraxis_showscale=False, height=350)
        fig_ref.add_vline(x=churn_rate, line_dash="dash", line_color="gray",
                          annotation_text=f"Média: {churn_rate:.1%}")
        st.plotly_chart(fig_ref, use_container_width=True)

    # --- ROW 2: MRR Impact & Reason Codes ---
    col_c, col_d = st.columns(2)

    with col_c:
        # MRR tier churn
        filtered_copy = filtered.copy()
        filtered_copy['mrr_tier'] = pd.cut(
            filtered_copy['avg_mrr'],
            bins=[0, 500, 1000, 2500, 5000, 40000],
            labels=['<$500', '$500-1K', '$1K-2.5K', '$2.5K-5K', '$5K+']
        )
        mrr_data = filtered_copy.groupby('mrr_tier', observed=True).agg(
            accounts=('account_id', 'count'),
            churn_rate=('churn_flag', 'mean'),
            mrr_lost=('mrr_at_risk', 'sum')
        ).reset_index()

        fig_mrr = make_subplots(specs=[[{"secondary_y": True}]])
        fig_mrr.add_trace(
            go.Bar(x=mrr_data['mrr_tier'], y=mrr_data['mrr_lost'],
                   name='MRR Perdido ($)', marker_color='#ef4444', opacity=0.7),
            secondary_y=False
        )
        fig_mrr.add_trace(
            go.Scatter(x=mrr_data['mrr_tier'], y=mrr_data['churn_rate'],
                       name='Churn Rate', mode='lines+markers+text',
                       text=mrr_data['churn_rate'].apply(lambda x: f'{x:.1%}'),
                       textposition='top center', line=dict(color='#1d4ed8', width=3)),
            secondary_y=True
        )
        fig_mrr.update_layout(title='Churn por Faixa de MRR (Volume vs Taxa)',
                              height=380, legend=dict(orientation="h", yanchor="bottom", y=1.02))
        fig_mrr.update_yaxes(title_text="MRR Perdido ($)", secondary_y=False)
        fig_mrr.update_yaxes(title_text="Churn Rate", secondary_y=True, tickformat='.0%')
        st.plotly_chart(fig_mrr, use_container_width=True)

    with col_d:
        # Churn reason codes
        churned_filtered = filtered[filtered['primary_reason'].notna()]
        if len(churned_filtered) > 0:
            reason_data = churned_filtered['primary_reason'].value_counts().reset_index()
            reason_data.columns = ['reason', 'count']

            fig_reason = px.pie(
                reason_data, names='reason', values='count',
                title='Razões do Churn (contas flagged)',
                color_discrete_sequence=px.colors.qualitative.Set2,
                hole=0.4
            )
            fig_reason.update_layout(height=380)
            st.plotly_chart(fig_reason, use_container_width=True)
        else:
            st.info("Nenhuma conta com churn neste filtro.")

    st.divider()

    # --- ROW 3: Feature Usage & Support ---
    st.subheader("Comportamento: Churned vs Retidos")
    col_e, col_f = st.columns(2)

    with col_e:
        # Escalation & satisfaction comparison
        churned_f = filtered[filtered.churn_flag == True]
        retained_f = filtered[filtered.churn_flag == False]

        metrics = ['avg_satisfaction', 'escalation_rate', 'avg_resolution_hours',
                   'avg_first_response_min', 'sub_churn_rate']
        labels = ['Satisfação Média', 'Taxa Escalação (%)', 'Tempo Resolução (h)',
                  'Primeiro Response (min)', 'Churn de Subscrições (%)']

        comparison_data = []
        for m, l in zip(metrics, labels):
            c_val = churned_f[m].mean() if len(churned_f) > 0 else 0
            r_val = retained_f[m].mean() if len(retained_f) > 0 else 0
            comparison_data.append({'Métrica': l, 'Churned': round(c_val, 2), 'Retidos': round(r_val, 2)})

        comp_df = pd.DataFrame(comparison_data)

        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(name='Churned', x=comp_df['Métrica'], y=comp_df['Churned'],
                                   marker_color='#ef4444'))
        fig_comp.add_trace(go.Bar(name='Retidos', x=comp_df['Métrica'], y=comp_df['Retidos'],
                                   marker_color='#22c55e'))
        fig_comp.update_layout(barmode='group', title='Suporte: Churned vs Retidos',
                               height=400, legend=dict(orientation="h", yanchor="bottom", y=1.02))
        st.plotly_chart(fig_comp, use_container_width=True)

    with col_f:
        # Country churn map
        country_data = filtered.groupby('country').agg(
            churn_rate=('churn_flag', 'mean'),
            accounts=('account_id', 'count'),
            mrr_lost=('mrr_at_risk', 'sum')
        ).reset_index()

        country_map = {'US': 'USA', 'UK': 'GBR', 'IN': 'IND', 'AU': 'AUS',
                       'DE': 'DEU', 'CA': 'CAN', 'FR': 'FRA'}
        country_data['iso'] = country_data['country'].map(country_map)

        fig_map = px.choropleth(
            country_data, locations='iso',
            color='churn_rate',
            hover_name='country',
            hover_data={'accounts': True, 'mrr_lost': ':$,.0f', 'churn_rate': ':.1%', 'iso': False},
            color_continuous_scale='RdYlGn_r',
            title='Churn Rate por País'
        )
        fig_map.update_layout(height=400, geo=dict(showframe=False, projection_type='natural earth'))
        st.plotly_chart(fig_map, use_container_width=True)

    st.divider()

    # --- ROW 4: Churn Timeline + Quarterly Acceleration ---
    st.subheader("Evolucao Temporal do Churn")

    col_tl1, col_tl2 = st.columns(2)

    with col_tl1:
        churn_timeline = churn_events.copy()
        churn_timeline['month'] = churn_timeline['churn_date'].dt.to_period('M').astype(str)
        churn_monthly = churn_timeline.groupby('month').agg(
            events=('churn_event_id', 'count'),
            refund_total=('refund_amount_usd', 'sum')
        ).reset_index()

        fig_timeline = make_subplots(specs=[[{"secondary_y": True}]])
        fig_timeline.add_trace(
            go.Bar(x=churn_monthly['month'], y=churn_monthly['events'],
                   name='Eventos de Churn', marker_color='#ef4444', opacity=0.7),
            secondary_y=False
        )
        fig_timeline.add_trace(
            go.Scatter(x=churn_monthly['month'], y=churn_monthly['refund_total'],
                       name='Refunds ($)', mode='lines+markers',
                       line=dict(color='#f59e0b', width=2)),
            secondary_y=True
        )
        fig_timeline.update_layout(title='Eventos de Churn por Mes', height=380,
                                   legend=dict(orientation="h", yanchor="bottom", y=1.02))
        fig_timeline.update_xaxes(tickangle=45)
        fig_timeline.update_yaxes(title_text="Eventos", secondary_y=False)
        fig_timeline.update_yaxes(title_text="Refunds ($)", secondary_y=True)
        st.plotly_chart(fig_timeline, use_container_width=True)

    with col_tl2:
        # Quarterly acceleration — the 42x story
        churn_q = churn_events.copy()
        churn_q['quarter'] = churn_q['churn_date'].dt.to_period('Q').astype(str)
        quarterly = churn_q.groupby('quarter').agg(
            events=('churn_event_id', 'count')
        ).reset_index()

        fig_accel = px.area(
            quarterly, x='quarter', y='events',
            title='Aceleracao Trimestral: de 6 para 251 eventos (42x)',
            labels={'events': 'Eventos por Trimestre', 'quarter': ''},
            color_discrete_sequence=['#dc2626']
        )
        fig_accel.update_layout(height=380)
        fig_accel.add_annotation(
            x=quarterly.iloc[0]['quarter'], y=quarterly.iloc[0]['events'],
            text=f"{quarterly.iloc[0]['events']} eventos", showarrow=True, arrowhead=2
        )
        fig_accel.add_annotation(
            x=quarterly.iloc[-1]['quarter'], y=quarterly.iloc[-1]['events'],
            text=f"{quarterly.iloc[-1]['events']} eventos", showarrow=True, arrowhead=2
        )
        st.plotly_chart(fig_accel, use_container_width=True)

    # --- CEO Claims Validation ---
    st.subheader("Validacao dos Claims do CEO")
    claim1, claim2, claim3 = st.columns(3)

    with claim1:
        st.markdown("**Claim: 'Uso da plataforma cresceu'**")
        st.markdown("**FALSO.** Uso per-account caiu ligeiramente no H2/2024 (-0.3% em count, -2.5% em duracao). O time de Produto provavelmente olha uso agregado.")
        st.metric("Veredicto", "FALSO", delta="-2.5% duracao", delta_color="inverse")

    with claim2:
        st.markdown("**Claim: 'Satisfacao esta ok'**")
        st.markdown("**VERDADE, mas irrelevante.** Churned (4.01) > Retidos (3.97). O problema nao e suporte -- e pricing, features e competicao.")
        st.metric("Veredicto", "VERDADE*", delta="mas irrelevante")

    with claim3:
        accounts_ever_churned = master[master.total_churn_events > 0].shape[0]
        st.markdown("**Claim: 'Churn e 22%'**")
        st.markdown(f"**INCOMPLETO.** {accounts_ever_churned} contas ({accounts_ever_churned/len(master):.0%}) ja churnearam pelo menos uma vez. {(master.total_churn_events > 1).sum()} churnearam multiplas vezes.")
        st.metric("Veredicto", "INCOMPLETO", delta=f"{accounts_ever_churned/len(master):.0%} real", delta_color="inverse")

    # --- ROW 5: Account-level drill-down ---
    st.subheader("Contas em Detalhe")
    show_churned_only = st.checkbox("Mostrar apenas contas churned", value=True)

    display_df = filtered[filtered.churn_flag == True] if show_churned_only else filtered
    display_cols = ['account_id', 'account_name', 'industry', 'country', 'plan_tier',
                    'latest_mrr', 'risk_score', 'risk_level', 'total_churn_events',
                    'primary_reason', 'escalation_rate', 'avg_satisfaction', 'sub_churn_rate']

    available_cols = [c for c in display_cols if c in display_df.columns]
    st.dataframe(
        display_df[available_cols].sort_values('latest_mrr', ascending=False),
        use_container_width=True,
        height=400
    )


# ============================================
# TAB 2: PREDITIVA
# ============================================
with tab2:
    st.title("Modelo Preditivo de Churn")
    st.caption("Risk Scoring (rule-based) + Random Forest | Explicabilidade via Feature Importance")

    # ---- Risk Matrix (from Part 4 risk scoring) ----
    st.subheader("Matriz de Risco: Probabilidade x Impacto")
    st.caption("Cada ponto e uma conta. Eixo X = risk score (0-100), Eixo Y = MRR mensal. Quadrante superior direito = emergencia.")

    if 'risk_score' in master.columns:
        active_accounts = filtered[filtered.churn_flag == False].copy()
        churned_accounts = filtered[filtered.churn_flag == True].copy()

        fig_matrix = go.Figure()

        # Active accounts
        if len(active_accounts) > 0:
            fig_matrix.add_trace(go.Scatter(
                x=active_accounts['risk_score'],
                y=active_accounts['avg_mrr'],
                mode='markers',
                name='Ativas',
                marker=dict(
                    size=8, color=active_accounts['risk_score'],
                    colorscale='YlOrRd', showscale=True,
                    colorbar=dict(title='Risk Score')
                ),
                text=active_accounts.apply(lambda r: f"{r['account_name']}<br>{r['industry']} | {r['referral_source']}<br>MRR: ${r['avg_mrr']:,.0f} | Score: {r['risk_score']:.0f}", axis=1),
                hoverinfo='text'
            ))

        # Churned accounts (as X markers for context)
        if len(churned_accounts) > 0:
            fig_matrix.add_trace(go.Scatter(
                x=churned_accounts['risk_score'],
                y=churned_accounts['avg_mrr'],
                mode='markers',
                name='Churned',
                marker=dict(size=6, color='#9ca3af', symbol='x', opacity=0.4),
                hoverinfo='skip'
            ))

        # Quadrant lines
        fig_matrix.add_hline(y=2500, line_dash="dash", line_color="gray", opacity=0.5,
                             annotation_text="$2.5K MRR")
        fig_matrix.add_vline(x=60, line_dash="dash", line_color="gray", opacity=0.5,
                             annotation_text="Risk Score 60")

        # Quadrant labels
        fig_matrix.add_annotation(x=80, y=active_accounts['avg_mrr'].max() * 0.9 if len(active_accounts) > 0 else 5000,
                                  text="CRITICO", font=dict(size=14, color='#dc2626'), showarrow=False)
        fig_matrix.add_annotation(x=30, y=active_accounts['avg_mrr'].max() * 0.9 if len(active_accounts) > 0 else 5000,
                                  text="MONITORAR", font=dict(size=14, color='#2563eb'), showarrow=False)
        fig_matrix.add_annotation(x=80, y=500,
                                  text="ATENCAO", font=dict(size=14, color='#f59e0b'), showarrow=False)
        fig_matrix.add_annotation(x=30, y=500,
                                  text="ESTAVEL", font=dict(size=14, color='#16a34a'), showarrow=False)

        fig_matrix.update_layout(
            height=500,
            xaxis_title='Risk Score (0-100)',
            yaxis_title='MRR Mensal ($)',
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
        st.plotly_chart(fig_matrix, use_container_width=True)

        # Risk level summary
        if 'risk_level' in filtered.columns:
            col_r1, col_r2, col_r3, col_r4 = st.columns(4)
            active_f = filtered[filtered.churn_flag == False]
            for col, level, color in [
                (col_r1, 'Baixo', 'success'), (col_r2, 'Moderado', 'warning'),
                (col_r3, 'Alto', 'danger'), (col_r4, 'Critico', 'danger')
            ]:
                level_accounts = active_f[active_f.risk_level == level]
                col.metric(
                    f"Risco {level}",
                    f"{len(level_accounts)} contas",
                    delta=f"${level_accounts['avg_mrr'].sum():,.0f} MRR"
                )
    else:
        st.info("Risk score nao disponivel. Execute notebooks/04_risk_segmentation.py primeiro.")

    st.divider()

    # ---- ML Model Section ----
    st.subheader("Modelo Preditivo (complementar)")
    st.caption("F1 = 0.098 — o modelo ML nao discrimina bem churned de retidos porque as features comportamentais sao quase identicas. O valor real esta no risk scoring acima.")

    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import cross_val_score, StratifiedKFold
    from sklearn.metrics import classification_report, confusion_matrix
    from sklearn.preprocessing import LabelEncoder

    @st.cache_data
    def train_model():
        df = master.copy()

        # Feature columns (numeric only)
        feature_cols = [
            'seats', 'tenure_days', 'total_subscriptions', 'avg_mrr', 'max_mrr',
            'total_upgrades', 'total_downgrades', 'pct_annual', 'pct_auto_renew',
            'sub_churn_rate', 'net_plan_movement',
            'total_usage_events', 'avg_usage_count', 'total_usage_duration',
            'avg_usage_duration', 'total_errors', 'avg_errors', 'max_errors',
            'pct_beta_usage', 'unique_features_used', 'error_rate',
            'total_tickets', 'avg_resolution_hours', 'avg_first_response_min',
            'avg_satisfaction', 'total_escalations', 'escalation_rate',
            'pct_urgent', 'pct_high'
        ]

        # Encode categoricals
        le_industry = LabelEncoder()
        df['industry_encoded'] = le_industry.fit_transform(df['industry'])
        le_country = LabelEncoder()
        df['country_encoded'] = le_country.fit_transform(df['country'])
        le_plan = LabelEncoder()
        df['plan_encoded'] = le_plan.fit_transform(df['plan_tier'])
        le_ref = LabelEncoder()
        df['referral_encoded'] = le_ref.fit_transform(df['referral_source'])
        df['is_trial_int'] = df['is_trial'].astype(int)

        feature_cols += ['industry_encoded', 'country_encoded', 'plan_encoded',
                         'referral_encoded', 'is_trial_int']

        X = df[feature_cols].fillna(0)
        y = df['churn_flag'].astype(int)

        # Train model
        model = RandomForestClassifier(
            n_estimators=200, max_depth=10, min_samples_leaf=5,
            class_weight='balanced', random_state=42
        )

        # Cross-validation
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        scores = cross_val_score(model, X, y, cv=cv, scoring='f1')

        # Fit on full data for feature importance
        model.fit(X, y)

        # Feature importance
        importances = pd.DataFrame({
            'feature': feature_cols,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)

        # Predictions for all accounts
        df['churn_probability'] = model.predict_proba(X)[:, 1]
        df['predicted_churn'] = model.predict(X)

        return model, importances, scores, df, feature_cols, X

    model, importances, cv_scores, pred_df, feature_cols, X = train_model()

    # --- Model Performance ---
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("F1 Score (CV)", f"{cv_scores.mean():.3f}", delta=f"±{cv_scores.std():.3f}")
    col_m2.metric("Features", f"{len(feature_cols)}")
    col_m3.metric("Contas Analisadas", f"{len(pred_df)}")

    st.divider()

    # --- Feature Importance ---
    col_fi, col_risk = st.columns([1, 1])

    with col_fi:
        st.subheader("Top 15 Drivers de Churn")
        top15 = importances.head(15).sort_values('importance', ascending=True)

        # Readable names
        name_map = {
            'sub_churn_rate': 'Taxa Churn Subscrições',
            'avg_mrr': 'MRR Médio',
            'tenure_days': 'Tempo como Cliente (dias)',
            'total_usage_duration': 'Duração Total de Uso',
            'avg_usage_duration': 'Duração Média de Uso',
            'max_mrr': 'MRR Máximo',
            'total_usage_events': 'Total Eventos de Uso',
            'avg_usage_count': 'Contagem Média de Uso',
            'avg_resolution_hours': 'Tempo Médio Resolução (h)',
            'avg_first_response_min': 'Tempo Primeiro Response (min)',
            'total_subscriptions': 'Total Subscrições',
            'seats': 'Licenças',
            'total_errors': 'Total Erros',
            'avg_satisfaction': 'Satisfação Média',
            'escalation_rate': 'Taxa de Escalação',
            'net_plan_movement': 'Movimento Líquido de Plano',
            'pct_annual': '% Billing Anual',
            'total_tickets': 'Total Tickets',
            'unique_features_used': 'Features Únicas Usadas',
            'total_escalations': 'Total Escalações',
            'pct_beta_usage': '% Uso Beta',
            'avg_errors': 'Erros Médios',
            'max_errors': 'Máx Erros',
            'error_rate': 'Taxa de Erro',
            'total_upgrades': 'Total Upgrades',
            'total_downgrades': 'Total Downgrades',
            'pct_auto_renew': '% Auto-Renovação',
            'pct_urgent': '% Tickets Urgentes',
            'pct_high': '% Tickets Alta Prioridade',
            'industry_encoded': 'Indústria',
            'country_encoded': 'País',
            'plan_encoded': 'Plano',
            'referral_encoded': 'Canal Aquisição',
            'is_trial_int': 'É Trial'
        }
        top15['feature_label'] = top15['feature'].map(name_map).fillna(top15['feature'])

        fig_fi = px.bar(
            top15, y='feature_label', x='importance',
            orientation='h',
            color='importance',
            color_continuous_scale='Blues',
            title='',
            labels={'importance': 'Importância', 'feature_label': ''}
        )
        fig_fi.update_layout(coloraxis_showscale=False, height=500)
        st.plotly_chart(fig_fi, use_container_width=True)

    with col_risk:
        st.subheader("Top 20 Contas em Risco (Score)")
        if 'risk_score' in master.columns:
            risk_df = master[(master.churn_flag == False)].nlargest(20, 'risk_score')
            risk_cols = ['account_id', 'account_name', 'industry', 'referral_source',
                         'avg_mrr', 'risk_score', 'risk_level']
            available_risk_cols = [c for c in risk_cols if c in risk_df.columns]
            risk_display = risk_df[available_risk_cols].copy()
            risk_display.columns = ['ID', 'Conta', 'Industria', 'Canal', 'MRR ($)', 'Score', 'Nivel'][:len(available_risk_cols)]
            st.dataframe(risk_display, use_container_width=True, height=500, hide_index=True)
        else:
            risk_df = pred_df[pred_df.churn_flag == False].nlargest(20, 'churn_probability')
            risk_display = risk_df[['account_id', 'account_name', 'industry', 'plan_tier',
                                     'latest_mrr', 'churn_probability']].copy()
            risk_display['churn_probability'] = risk_display['churn_probability'].apply(lambda x: f'{x:.1%}')
            risk_display.columns = ['ID', 'Conta', 'Industria', 'Plano', 'MRR ($)', 'Prob. Churn']
            st.dataframe(risk_display, use_container_width=True, height=500, hide_index=True)

    st.divider()

    # --- Risk Distribution ---
    st.subheader("Distribuição de Probabilidade de Churn")
    col_dist1, col_dist2 = st.columns(2)

    with col_dist1:
        fig_dist = px.histogram(
            pred_df, x='churn_probability', nbins=30,
            color='churn_flag',
            color_discrete_map={True: '#ef4444', False: '#22c55e'},
            labels={'churn_probability': 'Probabilidade de Churn', 'churn_flag': 'Churned?'},
            title='Distribuição: Modelo separa churned de retidos?',
            barmode='overlay', opacity=0.7
        )
        fig_dist.update_layout(height=400)
        st.plotly_chart(fig_dist, use_container_width=True)

    with col_dist2:
        # Risk by segment
        pred_df_copy = pred_df.copy()
        pred_df_copy['risk_bucket'] = pd.cut(
            pred_df_copy['churn_probability'],
            bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
            labels=['Baixo (<20%)', 'Moderado (20-40%)', 'Elevado (40-60%)',
                    'Alto (60-80%)', 'Crítico (>80%)']
        )
        risk_summary = pred_df_copy.groupby('risk_bucket', observed=True).agg(
            contas=('account_id', 'count'),
            mrr_total=('latest_mrr', 'sum')
        ).reset_index()

        fig_risk = px.bar(
            risk_summary, x='risk_bucket', y='contas',
            color='mrr_total',
            color_continuous_scale='YlOrRd',
            text='contas',
            title='Contas por Nível de Risco',
            labels={'risk_bucket': 'Nível de Risco', 'contas': 'Contas', 'mrr_total': 'MRR Total ($)'}
        )
        fig_risk.update_layout(height=400)
        st.plotly_chart(fig_risk, use_container_width=True)

    st.divider()

    # --- Individual Account Lookup ---
    st.subheader("Consulta Individual")
    account_options = pred_df['account_id'].tolist()
    selected_account = st.selectbox("Selecione uma conta:", account_options)

    if selected_account:
        acc_data = pred_df[pred_df.account_id == selected_account].iloc[0]
        col_acc1, col_acc2, col_acc3, col_acc4 = st.columns(4)
        col_acc1.metric("Prob. Churn", f"{acc_data['churn_probability']:.1%}")
        col_acc2.metric("MRR", f"${acc_data['latest_mrr']:,.0f}")
        col_acc3.metric("Indústria", acc_data['industry'])
        col_acc4.metric("Status", "🔴 Churned" if acc_data['churn_flag'] else "🟢 Ativo")

        # Top drivers for this account
        st.write("**Fatores desta conta vs média:**")
        acc_features = X.loc[pred_df[pred_df.account_id == selected_account].index]
        top_features = importances.head(8)['feature'].tolist()

        driver_data = []
        for feat in top_features:
            val = acc_features[feat].values[0]
            avg = X[feat].mean()
            label = name_map.get(feat, feat)
            direction = "⬆️" if val > avg else "⬇️" if val < avg else "➡️"
            driver_data.append({
                'Feature': label,
                'Valor da Conta': round(val, 2),
                'Média Geral': round(avg, 2),
                'Comparação': direction
            })

        st.dataframe(pd.DataFrame(driver_data), use_container_width=True, hide_index=True)


# ============================================
# TAB 3: RECOMENDAÇÕES
# ============================================
with tab3:
    st.title("Recomendações Acionáveis")
    st.caption("Priorizadas por impacto estimado em MRR")

    # Calculate dynamic stats for recommendations
    devtools_churn = master[master.industry == 'DevTools']['churn_flag'].mean()
    event_churn = master[master.referral_source == 'event']['churn_flag'].mean()
    partner_churn = master[master.referral_source == 'partner']['churn_flag'].mean()
    midmarket = master[(master.avg_mrr >= 1000) & (master.avg_mrr <= 2500)]
    midmarket_churn = midmarket['churn_flag'].mean()
    midmarket_mrr_at_risk = midmarket['mrr_at_risk'].sum()

    # High-risk non-churned accounts (using risk_score from Part 4)
    if 'risk_score' in master.columns:
        high_risk_active = master[(master.churn_flag == False) & (master.risk_score >= 60)]
        high_risk_mrr = high_risk_active['avg_mrr'].sum()
    else:
        high_risk_mrr = 0

    st.markdown("---")

    # Rec 1
    st.markdown("### 1. 🚨 Programa de Retenção DevTools (Impacto: ~$50K MRR)")
    st.markdown(f"""
    **Problema:** DevTools tem churn de **{devtools_churn:.0%}** — quase o dobro de EdTech/Cybersecurity.

    **Ação imediata:**
    - Criar um CS squad dedicado a DevTools (113 contas)
    - Entrevistas de saída com os 35 que churnearam → entender pain points específicos
    - Revisar se o produto resolve os use cases core de DevTools vs outras indústrias

    **Métrica de sucesso:** Reduzir churn DevTools para ≤20% em 90 dias
    """)

    # Rec 2
    st.markdown("### 2. 💸 Rever ROI de Aquisição via Eventos (Impacto: custo de aquisição)")
    st.markdown(f"""
    **Problema:** Clientes de eventos churn em **{event_churn:.0%}** vs **{partner_churn:.0%}** de partners — mais que o dobro.

    **Ação imediata:**
    - Calcular CAC por canal e comparar com LTV (partners provavelmente são 3x mais rentáveis)
    - Realocar budget de eventos para programa de partners
    - Se mantiver eventos: qualificar melhor os leads antes de converter

    **Métrica de sucesso:** Aumentar % de receita vinda de partners de {master[master.referral_source=='partner'].shape[0]/len(master):.0%} para 25%
    """)

    # Rec 3
    st.markdown("### 3. 🎯 Intervenção Mid-Market ($1K-$2.5K MRR)")
    st.markdown(f"""
    **Problema:** Faixa de $1K-$2.5K MRR tem **{midmarket_churn:.0%}** de churn com **${midmarket_mrr_at_risk:,.0f}** em risco.
    Essas contas são grandes demais para self-service mas pequenas demais para atendimento enterprise.

    **Ação imediata:**
    - Criar tier de atendimento "Growth" entre self-service e enterprise
    - Onboarding dedicado de 30 dias para novas contas nessa faixa
    - Check-in trimestral automatizado com CS

    **Métrica de sucesso:** Reduzir churn mid-market para ≤18% em 120 dias
    """)

    # Rec 4
    st.markdown("### 4. ⚡ Ação Imediata: Salvar Contas de Alto Risco Ativas")
    st.markdown(f"""
    **Problema:** O modelo identificou contas ativas com alta probabilidade de churn.
    MRR total em risco imediato: **${high_risk_mrr:,.0f}**

    **Ação imediata:**
    - Exportar lista da aba Preditiva → Top 20 contas de maior risco
    - CS entra em contato nas próximas 48h com oferta de suporte proativo
    - Para contas Enterprise: reunião de QBR (Quarterly Business Review) antecipada

    **Métrica de sucesso:** Reter ≥70% das contas de alto risco nos próximos 90 dias
    """)

    # Rec 5
    st.markdown("### 5. 📊 Corrigir a Métrica de Churn (o CEO está vendo errado)")
    st.markdown(f"""
    **Problema crítico de visibilidade:** O CEO vê **{master.churn_flag.mean():.0%}** de churn (contas flagged).
    Mas **{master[master.total_churn_events > 0].shape[0]}** contas ({master[master.total_churn_events > 0].shape[0]/len(master):.0%}) já tiveram pelo menos um evento de churn.
    **{(master.total_churn_events > 1).sum()}** contas churnearam múltiplas vezes (churn recorrente).

    **Ação imediata:**
    - Implementar 3 métricas de churn: Logo Churn (contas), Revenue Churn (MRR), Repeat Churn (reincidência)
    - Dashboard executivo mostrando as 3 métricas lado a lado
    - Alerta automático quando conta reativada mostra sinais de re-churn

    **Métrica de sucesso:** CEO e board usando as 3 métricas no próximo report
    """)

    st.divider()
    st.markdown("### Priorização")

    priority_data = pd.DataFrame({
        'Recomendação': ['DevTools Retention', 'Rever Eventos', 'Mid-Market Care',
                         'Salvar Alto Risco', 'Corrigir Métricas'],
        'Impacto Estimado': ['~$50K MRR', 'CAC savings', f'~${midmarket_mrr_at_risk:,.0f} MRR',
                             f'~${high_risk_mrr:,.0f} MRR', 'Visibilidade'],
        'Esforço': ['Médio', 'Baixo', 'Alto', 'Baixo', 'Baixo'],
        'Prazo': ['90 dias', '30 dias', '120 dias', '48h', '30 dias'],
        'Prioridade': ['🔴 Alta', '🟡 Média', '🟡 Média', '🔴 Urgente', '🔴 Alta']
    })
    st.dataframe(priority_data, use_container_width=True, hide_index=True)


# ============================================
# FOOTER
# ============================================
st.sidebar.divider()
st.sidebar.caption("RavenStack Churn Diagnosis | AI Master Challenge")
st.sidebar.caption("Powered by Claude Code + Streamlit")
