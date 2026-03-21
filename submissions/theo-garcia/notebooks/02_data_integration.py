"""
02 — Integração Cross-Table e Feature Engineering
==================================================
Merge das 5 tabelas em uma base master por account_id.

Decisão de design: agregar tudo por conta (não por subscrição).
Motivo: o CEO pensa em "clientes" (accounts), não em "contratos" (subscriptions).
O dashboard precisa falar a língua dele.

Correção feita: inicialmente eu ia usar a última subscrição de cada conta,
mas percebi que isso perderia o histórico de upgrades/downgrades.
Melhor agregar TODAS as subscrições e criar features derivadas.
"""

import pandas as pd
import numpy as np

# ── Load ──────────────────────────────────────────────────────────────
accounts = pd.read_csv('data/ravenstack_accounts.csv')
subs = pd.read_csv('data/ravenstack_subscriptions.csv')
usage = pd.read_csv('data/ravenstack_feature_usage.csv')
tickets = pd.read_csv('data/ravenstack_support_tickets.csv')
churn = pd.read_csv('data/ravenstack_churn_events.csv')

# Parse dates upfront
accounts['signup_date'] = pd.to_datetime(accounts['signup_date'])
subs['start_date'] = pd.to_datetime(subs['start_date'])
subs['end_date'] = pd.to_datetime(subs['end_date'])
usage['usage_date'] = pd.to_datetime(usage['usage_date'])
tickets['submitted_at'] = pd.to_datetime(tickets['submitted_at'])
churn['churn_date'] = pd.to_datetime(churn['churn_date'])

# ── 1. Features de Subscrição (por conta) ─────────────────────────────
# Cada conta tem em média 10 subscrições — preciso agregar
print("Construindo features de subscrição...")

sub_features = subs.groupby('account_id').agg(
    total_subscriptions=('subscription_id', 'count'),
    churned_subscriptions=('churn_flag', 'sum'),
    avg_mrr=('mrr_amount', 'mean'),
    max_mrr=('mrr_amount', 'max'),
    total_arr=('arr_amount', 'sum'),
    latest_mrr=('mrr_amount', 'last'),
    total_upgrades=('upgrade_flag', 'sum'),
    total_downgrades=('downgrade_flag', 'sum'),
    pct_annual=('billing_frequency', lambda x: (x == 'annual').mean()),
    pct_auto_renew=('auto_renew_flag', 'mean'),
    latest_plan=('plan_tier', 'last'),
).reset_index()

# Feature derivada: taxa de churn de subscrições
# Hipótese: contas com alto sub_churn_rate estão "morrendo devagar"
sub_features['sub_churn_rate'] = (
    sub_features['churned_subscriptions'] / sub_features['total_subscriptions']
)
# Movimento líquido: upgrades - downgrades. Negativo = conta deteriorando.
sub_features['net_plan_movement'] = (
    sub_features['total_upgrades'] - sub_features['total_downgrades']
)

# ── 2. Features de Uso (por conta, via subscription) ──────────────────
# usage → subscription → account (preciso do mapeamento intermediário)
print("Construindo features de uso...")

sub_account_map = subs[['subscription_id', 'account_id']].drop_duplicates()
usage_with_account = usage.merge(sub_account_map, on='subscription_id', how='left')

usage_features = usage_with_account.groupby('account_id').agg(
    total_usage_events=('usage_id', 'count'),
    avg_usage_count=('usage_count', 'mean'),
    total_usage_duration=('usage_duration_secs', 'sum'),
    avg_usage_duration=('usage_duration_secs', 'mean'),
    total_errors=('error_count', 'sum'),
    avg_errors=('error_count', 'mean'),
    max_errors=('error_count', 'max'),
    pct_beta_usage=('is_beta_feature', 'mean'),
    unique_features_used=('feature_name', 'nunique'),
).reset_index()

# Taxa de erro: erros / total de eventos de uso
usage_features['error_rate'] = (
    usage_features['total_errors'] / usage_features['total_usage_events']
)

# ── 3. Features de Suporte (por conta) ────────────────────────────────
# Nota: satisfaction_score tem 41% de nulls. Vou manter como NaN nas
# agregações (mean ignora NaN por default). Não vou imputar porque
# não sei se são missing at random — pode ser que clientes insatisfeitos
# simplesmente não respondam a pesquisa.
print("Construindo features de suporte...")

ticket_features = tickets.groupby('account_id').agg(
    total_tickets=('ticket_id', 'count'),
    avg_resolution_hours=('resolution_time_hours', 'mean'),
    max_resolution_hours=('resolution_time_hours', 'max'),
    avg_first_response_min=('first_response_time_minutes', 'mean'),
    avg_satisfaction=('satisfaction_score', 'mean'),
    min_satisfaction=('satisfaction_score', 'min'),
    total_escalations=('escalation_flag', 'sum'),
    pct_urgent=('priority', lambda x: (x == 'urgent').mean()),
    pct_high=('priority', lambda x: (x == 'high').mean()),
).reset_index()

ticket_features['escalation_rate'] = (
    ticket_features['total_escalations'] / ticket_features['total_tickets']
)

# ── 4. Features de Churn Events (por conta) ───────────────────────────
print("Construindo features de churn events...")

churn_features = churn.groupby('account_id').agg(
    total_churn_events=('churn_event_id', 'count'),
    total_refund_usd=('refund_amount_usd', 'sum'),
    avg_refund_usd=('refund_amount_usd', 'mean'),
    pct_preceded_by_downgrade=('preceding_downgrade_flag', 'mean'),
    pct_preceded_by_upgrade=('preceding_upgrade_flag', 'mean'),
    any_reactivation=('is_reactivation', 'any'),
    latest_reason=('reason_code', 'last'),
    first_churn_date=('churn_date', 'min'),
    last_churn_date=('churn_date', 'max'),
).reset_index()

# Razão principal (moda) — qual motivo aparece mais pra cada conta
reason_mode = churn.groupby('account_id')['reason_code'].agg(
    lambda x: x.mode().iloc[0]
).reset_index()
reason_mode.columns = ['account_id', 'primary_reason']
churn_features = churn_features.merge(reason_mode, on='account_id', how='left')

# ── 5. Master Table ───────────────────────────────────────────────────
print("Montando master table...")

master = accounts.copy()

# Tenure: dias desde signup até fim do dataset
master['tenure_days'] = (pd.Timestamp('2024-12-31') - master['signup_date']).dt.days

# Left joins — todas as contas, mesmo sem tickets ou churn
master = master.merge(sub_features, on='account_id', how='left')
master = master.merge(usage_features, on='account_id', how='left')
master = master.merge(ticket_features, on='account_id', how='left')
master = master.merge(churn_features, on='account_id', how='left')

# Fill NAs pra contas sem atividade nessas dimensões
master['total_tickets'] = master['total_tickets'].fillna(0)
master['total_escalations'] = master['total_escalations'].fillna(0)
master['total_churn_events'] = master['total_churn_events'].fillna(0)
master['total_refund_usd'] = master['total_refund_usd'].fillna(0)

# Impacto em receita: quanto MRR está em risco por conta churned
master['mrr_at_risk'] = master['latest_mrr'] * master['churn_flag'].astype(int)

# ── Validação ─────────────────────────────────────────────────────────
print(f"\nMaster table: {master.shape[0]} rows x {master.shape[1]} cols")
print(f"Nenhuma conta perdida no merge: {len(master) == 500}")

# ── Quick check: as médias mascaram o problema? ───────────────────────
# Essa comparação foi o momento em que entendi a confusão do CEO
print("\n" + "=" * 60)
print("CHURNED vs RETIDOS — por que o CEO acha que 'tá tudo ok'")
print("=" * 60)

churned = master[master.churn_flag == True]
retained = master[master.churn_flag == False]

comparisons = [
    ('MRR Médio ($)', 'avg_mrr'),
    ('Tickets de suporte', 'total_tickets'),
    ('Duração média de uso (s)', 'avg_usage_duration'),
    ('Total de erros', 'total_errors'),
    ('Satisfação média', 'avg_satisfaction'),
    ('% billing anual', 'pct_annual'),
    ('Features usadas', 'unique_features_used'),
    ('Taxa de escalação', 'escalation_rate'),
    ('Sub churn rate', 'sub_churn_rate'),
]

for label, col in comparisons:
    c = churned[col].mean()
    r = retained[col].mean()
    diff = ((c - r) / r * 100) if r != 0 else 0
    flag = "⚠️" if abs(diff) > 10 else "  "
    print(f"  {flag} {label:30s}  Churned: {c:>8.1f}  Retidos: {r:>8.1f}  (Δ {diff:+.1f}%)")

print("""
CONCLUSÃO: As médias são quase idênticas.
Isso NÃO significa que não há problema — significa que o problema
está escondido em SEGMENTOS específicos, não na base toda.
Preciso fazer análise segmentada no próximo passo.
""")

# Save
master.to_csv('data/master_churn_analysis.csv', index=False)
print("Salvo em data/master_churn_analysis.csv")
