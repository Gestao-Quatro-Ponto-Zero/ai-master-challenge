import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, precision_score, recall_score
import numpy as np

df = pd.read_csv("master_table.csv")

# Prepare features
features = ['seats', 'current_mrr', 'total_mrr', 'num_upgrades', 'num_downgrades', 
            'tenure_days', 'total_usage_count', 'distinct_features', 'total_error_count', 
            'used_beta', 'usage_last_30', 'usage_prev_60', 'usage_trend', 'num_tickets', 
            'avg_resolution_hours', 'avg_first_response_mins', 'avg_csat', 'num_escalations',
            'is_trial', 'billing_frequency', 'industry']

df_model = df.dropna(subset=['churn_flag']).copy()

# Fill NAs
df_model['avg_csat'] = df_model['avg_csat'].fillna(df_model['avg_csat'].mean())
df_model['avg_resolution_hours'] = df_model['avg_resolution_hours'].fillna(df_model['avg_resolution_hours'].mean())
df_model['avg_first_response_mins'] = df_model['avg_first_response_mins'].fillna(df_model['avg_first_response_mins'].mean())
df_model['usage_trend'] = df_model['usage_trend'].fillna('Stable')
df_model['billing_frequency'] = df_model['billing_frequency'].fillna('monthly')

# Encode categoricals
df_encoded = pd.get_dummies(df_model[features], drop_first=True)
X = df_encoded
y = df_model['churn_flag'].astype(int)

# Train Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Model
rf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
rf.fit(X_train, y_train)

# Evaluation
y_pred = rf.predict(X_test)
y_prob = rf.predict_proba(X_test)[:, 1]
auc = roc_auc_score(y_test, y_prob)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)

# Feature Importance
importances = pd.DataFrame({'feature': X.columns, 'importance': rf.feature_importances_})
importances = importances.sort_values('importance', ascending=False).head(10)

with open('phase45_results.txt', 'w', encoding='utf-8') as f:
    f.write(f"Model AUC: {auc:.3f} | Precision: {precision:.3f} | Recall: {recall:.3f}\n\n")
    f.write("Top 10 Important Features:\n")
    f.write(importances.to_string(index=False) + "\n\n")

# Predict risk for active accounts
active_accounts = df_model[df_model['churn_flag'] == False].copy()
X_active = df_encoded.loc[active_accounts.index]
active_accounts['risk_score'] = rf.predict_proba(X_active)[:, 1]

# Sort by risk * MRR to get "MRR at risk"
active_accounts['mrr_at_risk'] = active_accounts['risk_score'] * active_accounts['current_mrr']
top_risk = active_accounts.sort_values('mrr_at_risk', ascending=False).head(15)

with open('phase45_results.txt', 'a', encoding='utf-8') as f:
    f.write("Top 15 Accounts in Risk (by MRR at Risk):\n")
    cols_to_print = ['account_id', 'industry', 'current_mrr', 'risk_score', 'mrr_at_risk']
    f.write(top_risk[cols_to_print].to_string(index=False))
