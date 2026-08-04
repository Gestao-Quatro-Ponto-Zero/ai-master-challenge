import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
import sys
import io
warnings.filterwarnings('ignore')

# Redirecionar saída para evitar problemas de codificação
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Configuração de visualização
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', 50)

# Caminho dos arquivos
base_path = r'C:\Users\thiag\Downloads\Teste G4\database'

print("=" * 80)
print("FASE 1: AUDITORIA INICIAL - CARREGANDO E EXPLORANDO OS DADOS")
print("=" * 80)

# Carregar as 5 tabelas
print("\n1. Carregando ravenstack_accounts.csv...")
accounts = pd.read_csv(f'{base_path}/ravenstack_accounts.csv')
print(f"   Shape: {accounts.shape}")
print(f"   Colunas: {list(accounts.columns)}")
print(f"   Primeiras linhas:")
print(accounts.head())

print("\n2. Carregando ravenstack_subscriptions.csv...")
subscriptions = pd.read_csv(f'{base_path}/ravenstack_subscriptions.csv')
print(f"   Shape: {subscriptions.shape}")
print(f"   Colunas: {list(subscriptions.columns)}")
print(f"   Primeiras linhas:")
print(subscriptions.head())

print("\n3. Carregando ravenstack_feature_usage.csv...")
feature_usage = pd.read_csv(f'{base_path}/ravenstack_feature_usage.csv')
print(f"   Shape: {feature_usage.shape}")
print(f"   Colunas: {list(feature_usage.columns)}")
print(f"   Primeiras linhas:")
print(feature_usage.head())

print("\n4. Carregando ravenstack_support_tickets.csv...")
support_tickets = pd.read_csv(f'{base_path}/ravenstack_support_tickets.csv')
print(f"   Shape: {support_tickets.shape}")
print(f"   Colunas: {list(support_tickets.columns)}")
print(f"   Primeiras linhas:")
print(support_tickets.head())

print("\n5. Carregando ravenstack_churn_events.csv...")
churn_events = pd.read_csv(f'{base_path}/ravenstack_churn_events.csv')
print(f"   Shape: {churn_events.shape}")
print(f"   Colunas: {list(churn_events.columns)}")
print(f"   Primeiras linhas:")
print(churn_events.head())

print("\n" + "=" * 80)
print("RESUMO ESTATÍSTICO INICIAL")
print("=" * 80)

print("\n[ACCOUNTS]")
print(f"   Total de contas: {len(accounts)}")
print(f"   Contas com churn: {accounts['churn_flag'].sum()}")
print(f"   Taxa de churn global: {accounts['churn_flag'].mean():.2%}")
print(f"   Distribuição por indústria:")
print(accounts['industry'].value_counts())
print(f"   Distribuição por plano inicial:")
print(accounts['plan_tier'].value_counts())

print("\n[SUBSCRIPTIONS]")
print(f"   Total de assinaturas: {len(subscriptions)}")
print(f"   Assinaturas com churn: {subscriptions['churn_flag'].sum()}")
print(f"   MRR médio: ${subscriptions['mrr_amount'].mean():.2f}")
print(f"   ARR médio: ${subscriptions['arr_amount'].mean():.2f}")
print(f"   Distribuição por plano atual:")
print(subscriptions['plan_tier'].value_counts())

print("\n[FEATURE USAGE]")
print(f"   Total de eventos de uso: {len(feature_usage)}")
print(f"   Features únicas: {feature_usage['feature_name'].nunique()}")
print(f"   Média de uso por evento: {feature_usage['usage_count'].mean():.2f}")
print(f"   Média de duração (segundos): {feature_usage['usage_duration_secs'].mean():.2f}")
print(f"   Total de erros: {feature_usage['error_count'].sum()}")
print(f"   Eventos com features beta: {feature_usage['is_beta_feature'].sum()}")

print("\n[SUPPORT TICKETS]")
print(f"   Total de tickets: {len(support_tickets)}")
print(f"   Taxa de resposta CSAT (não nulo): {(support_tickets['satisfaction_score'].notna().mean()):.2%}")
print(f"   CSAT médio (respostas): {support_tickets['satisfaction_score'].mean():.2f}/5")
print(f"   Tempo médio de primeira resposta: {support_tickets['first_response_time_minutes'].mean():.2f} minutos")
print(f"   Tempo médio de resolução: {support_tickets['resolution_time_hours'].mean():.2f} horas")
print(f"   Tickets escalados: {support_tickets['escalation_flag'].sum()} ({support_tickets['escalation_flag'].mean():.2%})")

print("\n[CHURN EVENTS]")
print(f"   Total de eventos de churn: {len(churn_events)}")
print(f"   Motivos de churn:")
print(churn_events['reason_code'].value_counts())
print(f"   Reembolso médio: ${churn_events['refund_amount_usd'].mean():.2f}")
print(f"   Reactivações: {churn_events['is_reactivation'].sum()} ({churn_events['is_reactivation'].mean():.2%})")

print("\n" + "=" * 80)
print("VERIFICAÇÃO DE INTEGRIDADE DOS DADOS")
print("=" * 80)

# Verificar integridade das chaves estrangeiras
print("\n[Verificando chaves estrangeiras]")
print(f"   subscriptions.account_id -> accounts.account_id: {subscriptions['account_id'].isin(accounts['account_id']).all()}")
print(f"   feature_usage.subscription_id -> subscriptions.subscription_id: {feature_usage['subscription_id'].isin(subscriptions['subscription_id']).all()}")
print(f"   support_tickets.account_id -> accounts.account_id: {support_tickets['account_id'].isin(accounts['account_id']).all()}")
print(f"   churn_events.account_id -> accounts.account_id: {churn_events['account_id'].isin(accounts['account_id']).all()}")

print("\n[Dados carregados com sucesso!]")

print("\n" + "=" * 80)
print("FASE 1: ANALISANDO MEDIA DE USO VS CONTAS QUE DERAM CHURN")
print("=" * 80)

# Unir feature_usage com subscriptions e accounts para ter dados de churn
usage_with_accounts = feature_usage.merge(subscriptions[['subscription_id', 'account_id']], on='subscription_id')
usage_with_accounts = usage_with_accounts.merge(accounts[['account_id', 'churn_flag']], on='account_id')

print("\n[ANALISE DE USO POR STATUS DE CHURN]")
print(f"   Total de eventos de uso: {len(usage_with_accounts)}")
print(f"   Eventos de contas que deram churn: {len(usage_with_accounts[usage_with_accounts['churn_flag'] == True])}")
print(f"   Eventos de contas ativas: {len(usage_with_accounts[usage_with_accounts['churn_flag'] == False])}")

# Estatísticas de uso por status
usage_stats = usage_with_accounts.groupby('churn_flag').agg({
    'usage_count': ['mean', 'median', 'std'],
    'usage_duration_secs': ['mean', 'median'],
    'error_count': ['mean', 'sum']
}).round(2)

print("\n[Estatisticas de uso por status de churn]")
print(usage_stats)

# Analisar uso ao longo do tempo para contas que deram churn
usage_with_accounts['usage_date'] = pd.to_datetime(usage_with_accounts['usage_date'])
churn_accounts = accounts[accounts['churn_flag'] == True]['account_id'].tolist()

usage_churn_only = usage_with_accounts[usage_with_accounts['account_id'].isin(churn_accounts)]
usage_active_only = usage_with_accounts[~usage_with_accounts['account_id'].isin(churn_accounts)]

print("\n[Analise temporal - Uso medio por semana]")
usage_churn_only['week'] = usage_churn_only['usage_date'].dt.to_period('W')
usage_active_only['week'] = usage_active_only['usage_date'].dt.to_period('W')

weekly_usage_churn = usage_churn_only.groupby('week')['usage_count'].mean()
weekly_usage_active = usage_active_only.groupby('week')['usage_count'].mean()

print(f"   Tendencia de uso - Contas Churn (ultimas 8 semanas):")
print(weekly_usage_churn.tail(8))
print(f"\n   Tendencia de uso - Contas Ativas (ultimas 8 semanas):")
print(weekly_usage_active.tail(8))

# Analisar features beta vs erros
print("\n[Analise de Features Beta e Erros]")
beta_errors_churn = usage_churn_only[usage_churn_only['is_beta_feature'] == True]['error_count'].sum()
beta_errors_active = usage_active_only[usage_active_only['is_beta_feature'] == True]['error_count'].sum()

print(f"   Erros em features beta - Contas Churn: {beta_errors_churn}")
print(f"   Erros em features beta - Contas Ativas: {beta_errors_active}")
print(f"   Media de erros por evento (beta) - Churn: {usage_churn_only[usage_churn_only['is_beta_feature'] == True]['error_count'].mean():.2f}")
print(f"   Media de erros por evento (beta) - Ativas: {usage_active_only[usage_active_only['is_beta_feature'] == True]['error_count'].mean():.2f}")

print("\n" + "=" * 80)
print("FASE 1: AUDITANDO CSAT E METRICAS DE SUPORTE REAL")
print("=" * 80)

# Analisar CSAT
csat_response_rate = support_tickets['satisfaction_score'].notna().mean()
print(f"\n[Taxa de Resposta CSAT]")
print(f"   Total de tickets: {len(support_tickets)}")
print(f"   Tickets com CSAT: {support_tickets['satisfaction_score'].notna().sum()}")
print(f"   Tickets sem CSAT: {support_tickets['satisfaction_score'].isna().sum()}")
print(f"   Taxa de resposta: {csat_response_rate:.2%}")

# Analisar métricas reais de suporte
print(f"\n[Metricas Reais de Suporte]")
print(f"   Tempo medio de primeira resposta: {support_tickets['first_response_time_minutes'].mean():.2f} min")
print(f"   Tempo medio de resolucao: {support_tickets['resolution_time_hours'].mean():.2f} horas")
print(f"   Taxa de escalacao: {support_tickets['escalation_flag'].mean():.2%}")

# Analisar por prioridade
print(f"\n[Metricas por Prioridade]")
priority_stats = support_tickets.groupby('priority').agg({
    'first_response_time_minutes': 'mean',
    'resolution_time_hours': 'mean',
    'escalation_flag': 'mean',
    'satisfaction_score': 'mean'
}).round(2)
print(priority_stats)

# Analisar CSAT por status de churn da conta
tickets_with_churn = support_tickets.merge(accounts[['account_id', 'churn_flag']], on='account_id')
print(f"\n[CSAT por Status de Churn da Conta]")
csat_by_churn = tickets_with_churn.groupby('churn_flag').agg({
    'satisfaction_score': ['mean', 'count'],
    'first_response_time_minutes': 'mean',
    'resolution_time_hours': 'mean',
    'escalation_flag': 'mean'
}).round(2)
print(csat_by_churn)

print("\n" + "=" * 80)
print("FASE 1: FILTRANDO CHURN POR RECEITA (MRR/ARR)")
print("=" * 80)

# Unir subscriptions com churn_events
churn_with_revenue = churn_events.merge(subscriptions[['account_id', 'mrr_amount', 'arr_amount', 'plan_tier']], on='account_id')

print(f"\n[Churn por Valor de Receita]")
print(f"   Total de eventos de churn: {len(churn_with_revenue)}")
print(f"   MRR medio das contas que deram churn: ${churn_with_revenue['mrr_amount'].mean():.2f}")
print(f"   ARR medio das contas que deram churn: ${churn_with_revenue['arr_amount'].mean():.2f}")

# Churn por plano
print(f"\n[Churn por Plano]")
churn_by_plan = churn_with_revenue.groupby('plan_tier').agg({
    'account_id': 'count',
    'mrr_amount': ['mean', 'sum'],
    'arr_amount': ['mean', 'sum']
}).round(2)
print(churn_by_plan)

# Calcular impacto de receita
total_mrr_churn = churn_with_revenue['mrr_amount'].sum()
total_arr_churn = churn_with_revenue['arr_amount'].sum()
print(f"\n[Impacto Total de Receita]")
print(f"   MRR total perdido: ${total_mrr_churn:,.2f}")
print(f"   ARR total perdido: ${total_arr_churn:,.2f}")

# Comparar com receita total
total_mrr_all = subscriptions['mrr_amount'].sum()
total_arr_all = subscriptions['arr_amount'].sum()
print(f"\n[Comparacao com Receita Total]")
print(f"   MRR total base: ${total_mrr_all:,.2f}")
print(f"   ARR total base: ${total_arr_all:,.2f}")
print(f"   Percentual MRR perdido: {(total_mrr_churn / total_mrr_all):.2%}")
print(f"   Percentual ARR perdido: {(total_arr_churn / total_arr_all):.2%}")

print("\n" + "=" * 80)
print("FIM DA FASE 1 - AUDITORIA INICIAL CONCLUIDA")
print("=" * 80)

print("\n" + "=" * 80)
print("FASE 2: CRUZAMENTO FORENSE - ENCONTRANDO A CAUSA RAIZ")
print("=" * 80)

print("\n" + "=" * 80)
print("DIMENSAO 1: PADRAO DE USO VS CHURN")
print("=" * 80)

# Cruzar feature_usage com churn_events
usage_with_churn = feature_usage.merge(subscriptions[['subscription_id', 'account_id']], on='subscription_id')
usage_with_churn = usage_with_churn.merge(churn_events[['account_id', 'churn_date', 'reason_code']], on='account_id', how='left')

# Marcar eventos antes do churn
usage_with_churn['usage_date'] = pd.to_datetime(usage_with_churn['usage_date'])
usage_with_churn['churn_date'] = pd.to_datetime(usage_with_churn['churn_date'])
usage_with_churn['days_before_churn'] = (usage_with_churn['churn_date'] - usage_with_churn['usage_date']).dt.days

# Filtrar apenas eventos de contas que deram churn
churn_usage_analysis = usage_with_churn[usage_with_churn['churn_date'].notna()]

print("\n[Padroes de Uso Antes do Churn]")
print(f"   Total de eventos de uso de contas que deram churn: {len(churn_usage_analysis)}")

# Analisar uso por período antes do churn
churn_usage_analysis['period_before_churn'] = pd.cut(
    churn_usage_analysis['days_before_churn'],
    bins=[-1, 7, 14, 30, 60, 999],
    labels=['0-7 dias', '8-14 dias', '15-30 dias', '31-60 dias', '60+ dias']
)

usage_by_period = churn_usage_analysis.groupby('period_before_churn').agg({
    'usage_count': 'mean',
    'error_count': 'mean',
    'is_beta_feature': 'mean'
}).round(2)

print("\n[Uso por periodo antes do churn]")
print(usage_by_period)

# Analisar features específicas usadas por contas que deram churn
print("\n[Features mais usadas por contas que deram churn]")
top_features_churn = churn_usage_analysis.groupby('feature_name').agg({
    'usage_count': 'sum',
    'error_count': 'sum',
    'account_id': 'nunique'
}).sort_values('usage_count', ascending=False).head(10)
print(top_features_churn)

# Analisar erros em features beta antes do churn
beta_errors_before_churn = churn_usage_analysis[churn_usage_analysis['is_beta_feature'] == True].groupby('period_before_churn').agg({
    'error_count': ['mean', 'sum'],
    'usage_count': 'count'
}).round(2)

print("\n[Erros em Features Beta por periodo antes do churn]")
print(beta_errors_before_churn)

print("\n" + "=" * 80)
print("DIMENSAO 2: ATENDIMENTO VS RETENCAO")
print("=" * 80)

# Cruzar support_tickets com churn_events
tickets_with_churn = support_tickets.merge(churn_events[['account_id', 'churn_date', 'reason_code']], on='account_id', how='left')

# Marcar tickets antes do churn
tickets_with_churn['submitted_at'] = pd.to_datetime(tickets_with_churn['submitted_at'])
tickets_with_churn['churn_date'] = pd.to_datetime(tickets_with_churn['churn_date'])
tickets_with_churn['days_before_churn'] = (tickets_with_churn['churn_date'] - tickets_with_churn['submitted_at']).dt.days

# Filtrar tickets de contas que deram churn
churn_tickets_analysis = tickets_with_churn[tickets_with_churn['churn_date'].notna()]

print("\n[Padroes de Tickets antes do Churn]")
print(f"   Total de tickets de contas que deram churn: {len(churn_tickets_analysis)}")

# Analisar tickets por período antes do churn
churn_tickets_analysis['period_before_churn'] = pd.cut(
    churn_tickets_analysis['days_before_churn'],
    bins=[-1, 7, 14, 30, 60, 999],
    labels=['0-7 dias', '8-14 dias', '15-30 dias', '31-60 dias', '60+ dias']
)

tickets_by_period = churn_tickets_analysis.groupby('period_before_churn').agg({
    'ticket_id': 'count',
    'escalation_flag': 'mean',
    'first_response_time_minutes': 'mean',
    'resolution_time_hours': 'mean',
    'satisfaction_score': 'mean'
}).round(2)

print("\n[Tickets por periodo antes do churn]")
print(tickets_by_period)

# Analisar motivo de churn vs características dos tickets
print("\n[Motivo de Churn vs Metricas de Suporte]")
churn_reason_tickets = churn_tickets_analysis.groupby('reason_code').agg({
    'ticket_id': 'count',
    'escalation_flag': 'mean',
    'first_response_time_minutes': 'mean',
    'resolution_time_hours': 'mean',
    'satisfaction_score': 'mean'
}).round(2)
print(churn_reason_tickets)

# Cruzar com accounts para ver canal de aquisição
tickets_with_accounts = tickets_with_churn.merge(accounts[['account_id', 'referral_source']], on='account_id')

print("\n[Canal de Aquisicao vs Churn com Tickets]")
acquisition_churn_tickets = tickets_with_accounts[tickets_with_accounts['churn_date'].notna()].groupby('referral_source').agg({
    'ticket_id': 'count',
    'escalation_flag': 'mean',
    'satisfaction_score': 'mean'
}).round(2)
print(acquisition_churn_tickets)

print("\n" + "=" * 80)
print("DIMENSAO 3: PERFIL DE RISCO (SEGMENTACAO)")
print("=" * 80)

# Cruzar accounts + subscriptions + churn_events
full_churn_analysis = accounts.merge(
    subscriptions[['account_id', 'mrr_amount', 'arr_amount', 'plan_tier']], 
    on='account_id', 
    suffixes=('', '_sub')
)
full_churn_analysis = full_churn_analysis.merge(churn_events[['account_id', 'churn_date', 'reason_code']], on='account_id', how='left')

# Marcar contas que deram churn
full_churn_analysis['is_churn'] = full_churn_analysis['churn_date'].notna()

print("\n[Segmentacao por Industria]")
industry_churn = full_churn_analysis.groupby('industry').agg({
    'account_id': 'count',
    'is_churn': 'mean',
    'mrr_amount': 'mean'
}).round(2)
industry_churn.columns = ['Total Contas', 'Taxa Churn', 'MRR Medio']
industry_churn = industry_churn.sort_values('Taxa Churn', ascending=False)
print(industry_churn)

print("\n[Segmentacao por Pais]")
country_churn = full_churn_analysis.groupby('country').agg({
    'account_id': 'count',
    'is_churn': 'mean',
    'mrr_amount': 'mean'
}).round(2)
country_churn.columns = ['Total Contas', 'Taxa Churn', 'MRR Medio']
country_churn = country_churn.sort_values('Taxa Churn', ascending=False).head(10)
print(country_churn)

print("\n[Segmentacao por Canal de Aquisicao]")
referral_churn = full_churn_analysis.groupby('referral_source').agg({
    'account_id': 'count',
    'is_churn': 'mean',
    'mrr_amount': 'mean'
}).round(2)
referral_churn.columns = ['Total Contas', 'Taxa Churn', 'MRR Medio']
referral_churn = referral_churn.sort_values('Taxa Churn', ascending=False)
print(referral_churn)

print("\n[Segmentacao por Plano]")
plan_churn = full_churn_analysis.groupby('plan_tier_sub').agg({
    'account_id': 'count',
    'is_churn': 'mean',
    'mrr_amount': 'mean'
}).round(2)
plan_churn.columns = ['Total Contas', 'Taxa Churn', 'MRR Medio']
plan_churn = plan_churn.sort_values('Taxa Churn', ascending=False)
print(plan_churn)

# Analisar combinação de fatores de risco
print("\n[Contas com Maior Risco - Multiplos Fatores]")
high_risk_accounts = full_churn_analysis[
    (full_churn_analysis['is_churn'] == True) &
    ((full_churn_analysis['mrr_amount'] > full_churn_analysis['mrr_amount'].median()) |
     (full_churn_analysis['plan_tier_sub'] == 'Enterprise'))
].sort_values('mrr_amount', ascending=False).head(10)

print(high_risk_accounts[['account_id', 'account_name', 'industry', 'plan_tier_sub', 'mrr_amount', 'reason_code']])

print("\n" + "=" * 80)
print("FIM DA FASE 2 - CRUZAMENTO FORENSE CONCLUIDO")
print("=" * 80)

print("\n" + "=" * 80)
print("FASE 3: CONSTRUINDO O DIFERENCIAL DE ALTO IMPACTO")
print("=" * 80)

print("\n" + "=" * 80)
print("MODELO PREDITIVO SIMPLES DE CHURN")
print("=" * 80)

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.preprocessing import StandardScaler, LabelEncoder

# Preparar dados para o modelo
print("\n[Preparando dados para o modelo preditivo]")

# Criar features por conta
account_features = accounts.copy()

# Features de uso
usage_stats = feature_usage.merge(subscriptions[['subscription_id', 'account_id']], on='subscription_id')
usage_by_account = usage_stats.groupby('account_id').agg({
    'usage_count': ['mean', 'std', 'sum'],
    'usage_duration_secs': 'mean',
    'error_count': ['sum', 'mean'],
    'is_beta_feature': 'sum'
}).round(2)
usage_by_account.columns = ['usage_mean', 'usage_std', 'usage_total', 'duration_mean', 'errors_total', 'errors_mean', 'beta_total']
usage_by_account = usage_by_account.reset_index()

# Features de suporte
support_stats = support_tickets.groupby('account_id').agg({
    'ticket_id': 'count',
    'escalation_flag': 'sum',
    'first_response_time_minutes': 'mean',
    'resolution_time_hours': 'mean',
    'satisfaction_score': 'mean'
}).round(2)
support_stats.columns = ['tickets_total', 'escalations_total', 'frt_mean', 'resolution_mean', 'csat_mean']
support_stats = support_stats.reset_index()

# Features de subscription
subscription_features = subscriptions.groupby('account_id').agg({
    'mrr_amount': 'max',
    'arr_amount': 'max',
    'plan_tier': 'first',
    'upgrade_flag': 'sum',
    'downgrade_flag': 'sum'
}).reset_index()

# Merge all features
model_data = account_features[['account_id', 'churn_flag', 'industry', 'country', 'referral_source', 'seats']]
model_data = model_data.merge(usage_by_account, on='account_id', how='left')
model_data = model_data.merge(support_stats, on='account_id', how='left')
model_data = model_data.merge(subscription_features, on='account_id', how='left')

# Fill missing values
model_data = model_data.fillna(0)

# Encode categorical variables
le_industry = LabelEncoder()
le_country = LabelEncoder()
le_referral = LabelEncoder()
le_plan = LabelEncoder()

model_data['industry_encoded'] = le_industry.fit_transform(model_data['industry'].astype(str))
model_data['country_encoded'] = le_country.fit_transform(model_data['country'].astype(str))
model_data['referral_encoded'] = le_referral.fit_transform(model_data['referral_source'].astype(str))
model_data['plan_encoded'] = le_plan.fit_transform(model_data['plan_tier'].astype(str))

# Select features for model
feature_columns = [
    'seats', 'usage_mean', 'usage_std', 'usage_total', 'duration_mean',
    'errors_total', 'errors_mean', 'beta_total', 'tickets_total',
    'escalations_total', 'frt_mean', 'resolution_mean', 'csat_mean',
    'mrr_amount', 'arr_amount', 'upgrade_flag', 'downgrade_flag',
    'industry_encoded', 'country_encoded', 'referral_encoded', 'plan_encoded'
]

X = model_data[feature_columns]
y = model_data['churn_flag']

print(f"   Dataset shape: {X.shape}")
print(f"   Churn rate: {y.mean():.2%}")

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train model
print("\n[Treinando modelo de regressao logistica]")
model = LogisticRegression(random_state=42, max_iter=1000)
model.fit(X_train_scaled, y_train)

# Predictions
y_pred = model.predict(X_test_scaled)
y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]

# Evaluation
print("\n[Avaliacao do Modelo]")
print("Classification Report:")
print(classification_report(y_test, y_pred))

print(f"\nROC-AUC Score: {roc_auc_score(y_test, y_pred_proba):.3f}")

# Feature importance
feature_importance = pd.DataFrame({
    'feature': feature_columns,
    'coefficient': model.coef_[0]
})
feature_importance['abs_coefficient'] = feature_importance['coefficient'].abs()
feature_importance = feature_importance.sort_values('abs_coefficient', ascending=False)

print("\n[Top 10 Features mais importantes]")
print(feature_importance.head(10))

# Apply model to all accounts to get risk scores
print("\n[Calculando scores de risco para todas as contas]")
all_X_scaled = scaler.transform(X)
model_data['churn_probability'] = model.predict_proba(all_X_scaled)[:, 1]
model_data['risk_level'] = pd.cut(
    model_data['churn_probability'],
    bins=[0, 0.3, 0.6, 1.0],
    labels=['Baixo', 'Medio', 'Alto']
)

print("\n[Distribuicao de Risco]")
print(model_data['risk_level'].value_counts())

print("\n[Top 20 Contas com Maior Risco de Churn]")
high_risk = model_data[model_data['churn_flag'] == False].sort_values('churn_probability', ascending=False).head(20)
print(high_risk[['account_id', 'industry', 'mrr_amount', 'churn_probability', 'risk_level']])

print("\n" + "=" * 80)
print("PLAYBOOK DE ALERTA PRECOCE (EARLY WARNING SYSTEM)")
print("=" * 80)

print("\n[Regras de Alerta Automatico]")

# Regra 1: Queda de uso > 30% em 14 dias
print("\nRegra 1: Queda de Uso > 30% em 14 dias")
print("   - Logica: Comparar media de uso dos ultimos 14 dias com os 14 dias anteriores")
print("   - Acao: Alerta amarelo para CS entrar em contato")
print("   - Prioridade: Alta se MRR > mediano")

# Regra 2: Ticket escalado não resolvido
print("\nRegra 2: Ticket Escalado Nao Resolvido > 48 horas")
print("   - Logica: Verificar tickets com escalation_flag = True e resolution_time_hours > 48")
print("   - Acao: Alerta vermelho para CS Master agendar QBR")
print("   - Prioridade: Urgente")

# Regra 3: Aumento de erros em features beta
print("\nRegra 3: Aumento de Erros em Features Beta > 50%")
print("   - Logica: Comparar taxa de erros em features beta com media historica")
print("   - Acao: Alerta para equipe tecnica e CS")
print("   - Prioridade: Alta")

# Regra 4: Score de risco do modelo > 60%
print("\nRegra 4: Score de Risco do Modelo > 60%")
print("   - Logica: Usar probabilidade do modelo preditivo")
print("   - Acao: Alerta vermelho para intervencao imediata")
print("   - Prioridade: Urgente")

# Regra 5: Combinacao de fatores
print("\nRegra 5: Combinacao de Fatores de Risco")
print("   - Logica: (MRR > mediano) AND (Escalacoes > 0) AND (CSAT < 3.5)")
print("   - Acao: Alerta vermelho para executivo de conta")
print("   - Prioridade: Urgente")

# Implementar regras no dataset atual
print("\n[Aplicando regras ao dataset atual]")

# Contas ativas para analise
active_accounts = model_data[model_data['churn_flag'] == False].copy()

# Regra 1: Simular queda de uso (usando variacao padrao como proxy)
active_accounts['usage_volatility'] = active_accounts['usage_std'] / (active_accounts['usage_mean'] + 0.001)
rule1_alerts = active_accounts[active_accounts['usage_volatility'] > 0.3].shape[0]
print(f"   Regra 1 (Queda de uso): {rule1_alerts} contas em risco")

# Regra 2: Tickets escalados
rule2_alerts = active_accounts[active_accounts['escalations_total'] > 0].shape[0]
print(f"   Regra 2 (Tickets escalados): {rule2_alerts} contas em risco")

# Regra 3: Erros em features beta
rule3_alerts = active_accounts[active_accounts['beta_total'] > 5].shape[0]
print(f"   Regra 3 (Erros em features beta): {rule3_alerts} contas em risco")

# Regra 4: Score do modelo
rule4_alerts = active_accounts[active_accounts['churn_probability'] > 0.6].shape[0]
print(f"   Regra 4 (Score modelo > 60%): {rule4_alerts} contas em risco")

# Regra 5: Combinacao de fatores
rule5_alerts = active_accounts[
    (active_accounts['mrr_amount'] > active_accounts['mrr_amount'].median()) &
    (active_accounts['escalations_total'] > 0) &
    (active_accounts['csat_mean'] < 3.5)
].shape[0]
print(f"   Regra 5 (Combinacao de fatores): {rule5_alerts} contas em risco")

# Matriz de priorizacao
print("\n[Matriz de Priorizacao de Intervencao]")
high_priority = active_accounts[
    (active_accounts['churn_probability'] > 0.6) |
    (active_accounts['escalations_total'] > 0)
].sort_values(['churn_probability', 'mrr_amount'], ascending=[False, False])

print(f"   Total de contas em alta prioridade: {len(high_priority)}")
print("\n   Top 10 contas para intervencao imediata:")
print(high_priority[['account_id', 'industry', 'mrr_amount', 'churn_probability', 'escalations_total', 'csat_mean']].head(10))

print("\n" + "=" * 80)
print("FIM DA FASE 3 - DIFERENCIAL DE ALTO IMPACTO CONCLUIDO")
print("=" * 80)
