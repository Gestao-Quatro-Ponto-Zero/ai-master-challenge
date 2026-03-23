"""
Análise de Churn — RavenStack
Challenge 001 — G4 Educação AI Master

Autor: Lucas Caldeira Liberato Souza
Data: Março 2026

Este script reproduz toda a análise realizada no diagnóstico de churn.
Para executar: python analise_exploratoria.py

Requer: pandas, numpy
Dados: arquivos CSV na pasta ravenstack_data/
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

DATA_PATH = Path("ravenstack_data")  # Ajuste conforme necessário

# ============================================================================
# CARREGAR DADOS
# ============================================================================

def load_data():
    """Carrega os 5 datasets."""
    accounts = pd.read_csv(DATA_PATH / "ravenstack_accounts.csv")
    subscriptions = pd.read_csv(DATA_PATH / "ravenstack_subscriptions.csv")
    feature_usage = pd.read_csv(DATA_PATH / "ravenstack_feature_usage.csv")
    support_tickets = pd.read_csv(DATA_PATH / "ravenstack_support_tickets.csv")
    churn_events = pd.read_csv(DATA_PATH / "ravenstack_churn_events.csv")
    
    print("=" * 70)
    print("DADOS CARREGADOS")
    print("=" * 70)
    print(f"  accounts:        {len(accounts):,} registros")
    print(f"  subscriptions:   {len(subscriptions):,} registros")
    print(f"  feature_usage:   {len(feature_usage):,} registros")
    print(f"  support_tickets: {len(support_tickets):,} registros")
    print(f"  churn_events:    {len(churn_events):,} registros")
    
    return accounts, subscriptions, feature_usage, support_tickets, churn_events

# ============================================================================
# MÉTRICAS BÁSICAS
# ============================================================================

def basic_metrics(accounts, subscriptions):
    """Calcula métricas básicas de churn."""
    print("\n" + "=" * 70)
    print("MÉTRICAS BÁSICAS")
    print("=" * 70)
    
    total = len(accounts)
    churned = accounts['churn_flag'].sum()
    churn_rate = churned / total
    
    # MRR
    subscriptions['start_date'] = pd.to_datetime(subscriptions['start_date'])
    latest_subs = subscriptions.sort_values('start_date').groupby('account_id').last().reset_index()
    
    accounts_churn = accounts[['account_id', 'churn_flag']].copy()
    accounts_churn.columns = ['account_id', 'is_churned']
    latest_subs = latest_subs.merge(accounts_churn, on='account_id', how='left')
    
    churned_mrr = latest_subs[latest_subs['is_churned'] == True]['mrr_amount'].sum()
    active_mrr = latest_subs[latest_subs['is_churned'] == False]['mrr_amount'].sum()
    
    print(f"\n  Total accounts:  {total}")
    print(f"  Churned:         {churned} ({churn_rate*100:.1f}%)")
    print(f"  Active:          {total - churned} ({(1-churn_rate)*100:.1f}%)")
    print(f"\n  MRR perdido:     ${churned_mrr:,.0f}")
    print(f"  MRR ativo:       ${active_mrr:,.0f}")
    
    return latest_subs

# ============================================================================
# ANÁLISE POR SEGMENTO
# ============================================================================

def segment_analysis(accounts):
    """Analisa churn por diferentes segmentos."""
    print("\n" + "=" * 70)
    print("ANÁLISE POR SEGMENTO")
    print("=" * 70)
    
    # Por indústria
    print("\n📊 CHURN POR INDÚSTRIA:")
    for ind in accounts['industry'].unique():
        ind_data = accounts[accounts['industry'] == ind]
        churn_rate = ind_data['churn_flag'].mean() * 100
        n = len(ind_data)
        print(f"  {ind}: {churn_rate:.1f}% (n={n})")
    
    # Por canal
    print("\n📊 CHURN POR CANAL:")
    for ref in accounts['referral_source'].unique():
        ref_data = accounts[accounts['referral_source'] == ref]
        churn_rate = ref_data['churn_flag'].mean() * 100
        n = len(ref_data)
        print(f"  {ref}: {churn_rate:.1f}% (n={n})")
    
    # Cruzamento crítico: DevTools x Canal
    print("\n📊 DEVTOOLS POR CANAL (cruzamento crítico):")
    devtools = accounts[accounts['industry'] == 'DevTools']
    for ref in ['event', 'partner', 'ads', 'organic']:
        ref_data = devtools[devtools['referral_source'] == ref]
        if len(ref_data) >= 5:
            churn_rate = ref_data['churn_flag'].mean() * 100
            print(f"  DevTools + {ref}: {churn_rate:.1f}% churn (n={len(ref_data)})")

# ============================================================================
# CORE FEATURES ANALYSIS
# ============================================================================

def core_features_analysis(accounts, subscriptions, feature_usage):
    """Identifica core features e correlação com churn."""
    print("\n" + "=" * 70)
    print("ANÁLISE DE CORE FEATURES")
    print("=" * 70)
    
    # Merge para conectar features a accounts
    sub_account = subscriptions[['subscription_id', 'account_id']].drop_duplicates()
    usage_with_account = feature_usage.merge(sub_account, on='subscription_id', how='left')
    usage_with_churn = usage_with_account.merge(
        accounts[['account_id', 'churn_flag']], 
        on='account_id', 
        how='left'
    )
    
    # Identificar core features (top 10 de ativos)
    active_usage = usage_with_churn[usage_with_churn['churn_flag'] == False]
    core_features = active_usage.groupby('feature_name')['usage_count'].sum().nlargest(10).index.tolist()
    
    print(f"\n📊 CORE FEATURES (top 10 de ativos):")
    for i, feat in enumerate(core_features, 1):
        print(f"  {i}. {feat}")
    
    # Calcular % de core usage por account
    usage_by_account = usage_with_churn.groupby(['account_id', 'feature_name'])['usage_count'].sum().reset_index()
    total_usage = usage_by_account.groupby('account_id')['usage_count'].sum().reset_index()
    total_usage.columns = ['account_id', 'total_usage']
    
    core_usage = usage_by_account[usage_by_account['feature_name'].isin(core_features)]
    core_by_account = core_usage.groupby('account_id')['usage_count'].sum().reset_index()
    core_by_account.columns = ['account_id', 'core_usage']
    
    account_features = total_usage.merge(core_by_account, on='account_id', how='left')
    account_features['core_usage'] = account_features['core_usage'].fillna(0)
    account_features['core_pct'] = (account_features['core_usage'] / account_features['total_usage'] * 100)
    account_features = account_features.merge(accounts[['account_id', 'churn_flag']], on='account_id', how='left')
    
    # Churn por faixa de core adoption
    print("\n📊 CHURN POR ADOÇÃO DE CORE FEATURES:")
    account_features['core_bucket'] = pd.cut(
        account_features['core_pct'], 
        bins=[-1, 20, 40, 60, 100],
        labels=['0-20%', '20-40%', '40-60%', '60%+']
    )
    
    for bucket in ['0-20%', '20-40%', '40-60%', '60%+']:
        bucket_data = account_features[account_features['core_bucket'] == bucket]
        if len(bucket_data) > 0:
            churn_rate = bucket_data['churn_flag'].mean() * 100
            n = len(bucket_data)
            print(f"  {bucket}: {churn_rate:.1f}% churn (n={n})")
    
    return account_features, core_features

# ============================================================================
# RISK SCORING
# ============================================================================

def calculate_risk_scores(accounts, subscriptions, support_tickets, account_features):
    """Calcula risk score para accounts ativos."""
    print("\n" + "=" * 70)
    print("RISK SCORING")
    print("=" * 70)
    
    # Criar dataset master
    master = accounts.copy()
    
    # Subscription data
    subscriptions['start_date'] = pd.to_datetime(subscriptions['start_date'])
    latest_subs = subscriptions.sort_values('start_date').groupby('account_id').last().reset_index()
    latest_subs = latest_subs[['account_id', 'mrr_amount', 'plan_tier']]
    latest_subs.columns = ['account_id', 'mrr_amount', 'current_plan']
    master = master.merge(latest_subs, on='account_id', how='left')
    
    # Support data
    support_agg = support_tickets.groupby('account_id').agg({
        'escalation_flag': 'sum',
        'satisfaction_score': 'mean'
    }).reset_index()
    support_agg.columns = ['account_id', 'escalations', 'avg_csat']
    master = master.merge(support_agg, on='account_id', how='left')
    
    # Core features
    master = master.merge(
        account_features[['account_id', 'core_pct']], 
        on='account_id', 
        how='left'
    )
    
    # Apenas ativos
    active_accounts = master[master['churn_flag'] == False].copy()
    
    # Calcular risk score
    def calc_risk(row):
        score = 0
        if row['industry'] == 'DevTools':
            score += 3
        if row['referral_source'] in ['event', 'ads']:
            score += 3
        if pd.notna(row['core_pct']) and row['core_pct'] < 20:
            score += 2
        if pd.notna(row['escalations']) and row['escalations'] > 0:
            score += 2
        if pd.notna(row['avg_csat']) and row['avg_csat'] < 4.0:
            score += 1
        return score
    
    active_accounts['risk_score'] = active_accounts.apply(calc_risk, axis=1)
    
    # High risk (score >= 5)
    high_risk = active_accounts[active_accounts['risk_score'] >= 5]
    
    print(f"\n📊 CONTAS DE ALTO RISCO (score >= 5):")
    print(f"  Total: {len(high_risk)} contas")
    print(f"  MRR:   ${high_risk['mrr_amount'].sum():,.0f}")
    
    print("\n📊 TOP 10 CONTAS:")
    top_10 = high_risk.nlargest(10, 'risk_score')[
        ['account_id', 'industry', 'referral_source', 'current_plan', 'mrr_amount', 'risk_score']
    ]
    print(top_10.to_string(index=False))
    
    return active_accounts, high_risk

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Executa toda a análise."""
    print("\n" + "=" * 70)
    print("DIAGNÓSTICO DE CHURN — RAVENSTACK")
    print("=" * 70)
    
    # Carregar dados
    accounts, subscriptions, feature_usage, support_tickets, churn_events = load_data()
    
    # Métricas básicas
    latest_subs = basic_metrics(accounts, subscriptions)
    
    # Análise por segmento
    segment_analysis(accounts)
    
    # Core features
    account_features, core_features = core_features_analysis(accounts, subscriptions, feature_usage)
    
    # Risk scoring
    active_accounts, high_risk = calculate_risk_scores(
        accounts, subscriptions, support_tickets, account_features
    )
    
    # Salvar high risk
    high_risk.to_csv('contas_alto_risco.csv', index=False)
    print(f"\n✓ Lista de contas salva em 'contas_alto_risco.csv'")
    
    print("\n" + "=" * 70)
    print("ANÁLISE CONCLUÍDA")
    print("=" * 70)

if __name__ == "__main__":
    main()
