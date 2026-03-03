"""
Phase 3+4: Risk Scoring & Predictive Churn Model
=================================================
Build a model that predicts churn, identifies at-risk accounts,
and provides feature importance analysis.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.preprocessing import LabelEncoder
import warnings
import json
warnings.filterwarnings('ignore')

DATA = '/home/user/ai-master-challenge/datasets/'
OUT = '/home/user/ai-master-challenge/submissions/ai-master/solution/'

# Load
accounts = pd.read_csv(f'{DATA}ravenstack_accounts.csv')
subs = pd.read_csv(f'{DATA}ravenstack_subscriptions.csv')
usage = pd.read_csv(f'{DATA}ravenstack_feature_usage.csv')
tickets = pd.read_csv(f'{DATA}ravenstack_support_tickets.csv')
churn = pd.read_csv(f'{DATA}ravenstack_churn_events.csv')

# Target
churned_ids = set(churn['account_id'].unique())
accounts['churned'] = accounts['account_id'].isin(churned_ids).astype(int)

print("=" * 70)
print("PHASE 3+4: CHURN PREDICTION MODEL")
print("=" * 70)

# ============================================================
# FEATURE ENGINEERING
# ============================================================
print("\n1. Feature Engineering...")

# --- Subscription features ---
sub_features = subs.groupby('account_id').agg(
    total_subs=('subscription_id', 'count'),
    avg_mrr=('mrr', 'mean'),
    max_mrr=('mrr', 'max'),
    total_mrr=('mrr', 'sum'),
    avg_arr=('arr', 'mean'),
    n_churned_subs=('status', lambda x: (x.isin(['Churned', 'Cancelled'])).sum()),
    n_downgrades=('status', lambda x: (x == 'Downgraded').sum()),
    n_upgrades=('status', lambda x: (x == 'Upgraded').sum()),
    pct_monthly=('billing_frequency', lambda x: (x == 'Monthly').mean()),
    avg_discount=('discount_pct', 'mean'),
    has_auto_renew=('auto_renew', 'mean'),
).reset_index()

sub_features['downgrade_ratio'] = sub_features['n_downgrades'] / sub_features['total_subs']
sub_features['upgrade_ratio'] = sub_features['n_upgrades'] / sub_features['total_subs']

# --- Usage features ---
sub_acct = subs[['subscription_id', 'account_id']].drop_duplicates()
usage_with_acct = usage.merge(sub_acct, on='subscription_id', how='left')

usage_features = usage_with_acct.groupby('account_id').agg(
    total_usage=('usage_count', 'sum'),
    avg_usage=('usage_count', 'mean'),
    total_errors=('error_count', 'sum'),
    avg_errors=('error_count', 'mean'),
    total_duration=('duration_minutes', 'sum'),
    features_used=('feature_name', 'nunique'),
    total_sessions=('session_count', 'sum'),
    pct_beta=('is_beta_feature', 'mean'),
    usage_records=('usage_count', 'count'),
).reset_index()

usage_features['error_rate'] = usage_features['total_errors'] / usage_features['total_usage'].replace(0, 1)
usage_features['avg_duration_per_use'] = usage_features['total_duration'] / usage_features['total_usage'].replace(0, 1)

# Feature-specific error rates
for feat in ['Workflow Builder', 'Report Generator', 'AI Chat']:
    feat_data = usage_with_acct[usage_with_acct['feature_name'] == feat]
    feat_agg = feat_data.groupby('account_id').agg(
        **{f'{feat.lower().replace(" ", "_")}_errors': ('error_count', 'sum'),
           f'{feat.lower().replace(" ", "_")}_usage': ('usage_count', 'sum')}
    ).reset_index()
    usage_features = usage_features.merge(feat_agg, on='account_id', how='left')

# --- Ticket features ---
ticket_features = tickets.groupby('account_id').agg(
    total_tickets=('ticket_id', 'count'),
    avg_response_hrs=('first_response_hours', 'mean'),
    avg_resolution_hrs=('resolution_hours', 'mean'),
    max_resolution_hrs=('resolution_hours', 'max'),
    avg_satisfaction=('satisfaction_score', 'mean'),
    pct_missing_satisfaction=('satisfaction_score', lambda x: x.isna().mean()),
    escalation_rate=('escalated', 'mean'),
    reopen_rate=('reopened', 'mean'),
    pct_high_critical=('priority', lambda x: x.isin(['High', 'Critical']).mean()),
    pct_technical=('category', lambda x: (x == 'Technical').mean()),
    pct_integration=('category', lambda x: (x == 'Integration').mean()),
).reset_index()

# --- Account features ---
le_plan = LabelEncoder()
le_industry = LabelEncoder()
le_channel = LabelEncoder()

acct_features = accounts[['account_id', 'industry', 'plan', 'acquisition_channel',
                           'is_trial', 'employee_count', 'churned']].copy()
acct_features['plan_encoded'] = le_plan.fit_transform(acct_features['plan'])
acct_features['industry_encoded'] = le_industry.fit_transform(acct_features['industry'])
acct_features['channel_encoded'] = le_channel.fit_transform(acct_features['acquisition_channel'])

# --- Merge all ---
model_data = acct_features.merge(sub_features, on='account_id', how='left')
model_data = model_data.merge(usage_features, on='account_id', how='left')
model_data = model_data.merge(ticket_features, on='account_id', how='left')

# Fill NaN
model_data = model_data.fillna(0)

# ============================================================
# FEATURE SELECTION
# ============================================================
feature_cols = [
    # Account
    'plan_encoded', 'industry_encoded', 'channel_encoded', 'is_trial', 'employee_count',
    # Subscription
    'total_subs', 'avg_mrr', 'max_mrr', 'n_downgrades', 'n_upgrades',
    'pct_monthly', 'avg_discount', 'has_auto_renew', 'downgrade_ratio', 'upgrade_ratio',
    # Usage
    'total_usage', 'avg_usage', 'total_errors', 'error_rate', 'features_used',
    'total_sessions', 'pct_beta', 'avg_duration_per_use',
    # Ticket
    'total_tickets', 'avg_response_hrs', 'avg_resolution_hrs', 'avg_satisfaction',
    'pct_missing_satisfaction', 'escalation_rate', 'reopen_rate', 'pct_high_critical',
    'pct_technical', 'pct_integration',
]

# Add feature-specific if available
for col in model_data.columns:
    if col.endswith('_errors') or col.endswith('_usage'):
        if col not in feature_cols and col != 'total_errors':
            feature_cols.append(col)

X = model_data[feature_cols]
y = model_data['churned']

print(f"Features: {len(feature_cols)}")
print(f"Samples: {len(X)} (churned: {y.sum()}, retained: {(1-y).sum()})")

# ============================================================
# MODEL TRAINING
# ============================================================
print("\n2. Training Models...")

# Random Forest
rf = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, class_weight='balanced')
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

rf_scores = cross_val_score(rf, X, y, cv=cv, scoring='roc_auc')
print(f"\nRandom Forest CV AUC: {rf_scores.mean():.3f} ± {rf_scores.std():.3f}")

# Gradient Boosting
gb = GradientBoostingClassifier(n_estimators=200, max_depth=5, learning_rate=0.1, random_state=42)
gb_scores = cross_val_score(gb, X, y, cv=cv, scoring='roc_auc')
print(f"Gradient Boosting CV AUC: {gb_scores.mean():.3f} ± {gb_scores.std():.3f}")

# Train final model on all data
best_model = gb if gb_scores.mean() > rf_scores.mean() else rf
best_model.fit(X, y)

# Full data predictions
y_pred = best_model.predict(X)
y_proba = best_model.predict_proba(X)[:, 1]

print(f"\nFull-data Classification Report:")
print(classification_report(y, y_pred, target_names=['Retained', 'Churned']))

# ============================================================
# FEATURE IMPORTANCE
# ============================================================
print("\n3. Feature Importance (Top 15):")
importances = pd.DataFrame({
    'feature': feature_cols,
    'importance': best_model.feature_importances_
}).sort_values('importance', ascending=False)

for _, row in importances.head(15).iterrows():
    bar = '█' * int(row['importance'] * 100)
    print(f"  {row['feature']:30s}: {row['importance']:.4f} {bar}")

# ============================================================
# RISK SCORING — ACTIVE ACCOUNTS
# ============================================================
print("\n\n4. Risk Scoring — At-Risk Accounts")
print("-" * 50)

model_data['churn_probability'] = y_proba
model_data['risk_tier'] = pd.cut(y_proba, bins=[0, 0.3, 0.6, 0.8, 1.0],
                                  labels=['Low', 'Medium', 'High', 'Critical'])

# Focus on accounts NOT yet churned but at high risk
active_at_risk = model_data[(model_data['churned'] == 0) & (model_data['churn_probability'] >= 0.5)]
active_at_risk = active_at_risk.merge(
    accounts[['account_id', 'company_name', 'industry', 'plan', 'acquisition_channel']],
    on='account_id', how='left'
)
active_at_risk = active_at_risk.sort_values('churn_probability', ascending=False)

print(f"\nActive accounts at risk (probability >= 50%): {len(active_at_risk)}")
print(f"Total MRR at risk: ${active_at_risk['avg_mrr'].sum():,.0f}")

print(f"\nTop 20 At-Risk Accounts:")
print(f"{'Account':12} {'Company':18} {'Industry':15} {'Plan':14} {'MRR':>10} {'Risk':>8} {'Tier'}")
print("-" * 95)
for _, row in active_at_risk.head(20).iterrows():
    print(f"{row['account_id']:12} {row['company_name']:18} {row['industry']:15} "
          f"{row['plan']:14} ${row['avg_mrr']:>8,.0f} {row['churn_probability']:>7.1%} {row['risk_tier']}")

# Risk tier summary
print(f"\n\nRisk Tier Summary (ALL accounts):")
for tier in ['Critical', 'High', 'Medium', 'Low']:
    subset = model_data[model_data['risk_tier'] == tier]
    print(f"  {tier:10}: {len(subset):>4} accounts | "
          f"Avg MRR: ${subset['avg_mrr'].mean():>8,.0f} | "
          f"Actual churn: {subset['churned'].mean()*100:.0f}%")

# ============================================================
# SAVE OUTPUTS
# ============================================================
# Save risk scores
risk_output = model_data[['account_id', 'churned', 'churn_probability', 'risk_tier',
                           'avg_mrr', 'total_usage', 'error_rate', 'total_tickets',
                           'avg_response_hrs', 'escalation_rate']].merge(
    accounts[['account_id', 'company_name', 'industry', 'plan', 'acquisition_channel']],
    on='account_id'
)
risk_output.to_csv(f'{OUT}account_risk_scores.csv', index=False)

# Save feature importance
importances.to_csv(f'{OUT}feature_importance.csv', index=False)

# Save model metrics as JSON
metrics = {
    'model': 'GradientBoosting' if gb_scores.mean() > rf_scores.mean() else 'RandomForest',
    'cv_auc_mean': round(float(max(gb_scores.mean(), rf_scores.mean())), 3),
    'cv_auc_std': round(float(gb_scores.std() if gb_scores.mean() > rf_scores.mean() else rf_scores.std()), 3),
    'n_features': len(feature_cols),
    'n_samples': len(X),
    'churn_rate': round(float(y.mean()), 3),
    'active_at_risk_count': int(len(active_at_risk)),
    'active_at_risk_mrr': round(float(active_at_risk['avg_mrr'].sum()), 2),
    'top_features': importances.head(10).to_dict('records'),
}
with open(f'{OUT}model_metrics.json', 'w') as f:
    json.dump(metrics, f, indent=2)

print(f"\n\nOutputs saved:")
print(f"  - account_risk_scores.csv")
print(f"  - feature_importance.csv")
print(f"  - model_metrics.json")
print(f"\nDone!")
