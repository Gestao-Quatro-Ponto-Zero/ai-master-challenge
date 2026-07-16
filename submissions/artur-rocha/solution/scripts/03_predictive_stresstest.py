import os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
"""
Challenge 001 — Passo 3: teste a prova de bala.
Pergunta: combinando TODOS os sinais, da pra prever churn?
Se AUC ~0.5 -> churn e imprevisivel nos dados (o insight central).
Testa sob DOIS rotulos de churn (flag oficial vs baseado em eventos) pra garantir
que a conclusao nao e artefato da escolha de rotulo.
"""
import pandas as pd, numpy as np
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer

DATA = os.path.join(_ROOT,'data')
OUT  = os.path.join(_ROOT,'solution','outputs')
m = pd.read_csv(f'{OUT}/account_master_clean.csv')
chn = pd.read_csv(f'{DATA}/ravenstack_churn_events.csv', parse_dates=['churn_date'])

# rotulo alternativo: teve evento de churn e NAO foi reativado
last_evt = chn.sort_values('churn_date').groupby('account_id').tail(1)
evt_churn = set(last_evt.loc[~last_evt.is_reactivation,'account_id'])
m['churn_evt'] = m.account_id.isin(evt_churn)
print(f"label oficial (churn_flag): {m.churn_flag.mean():.1%} churn")
print(f"label alternativo (evento): {m.churn_evt.mean():.1%} churn")

num = ['mrr_amount','arr_amount','seats','usage_events','errors','usage_days',
       'tickets','avg_resolution_h','avg_satisfaction','escalations']
cat = ['industry','referral_source','plan_tier','billing_frequency','is_trial','auto_renew_flag']

# preparar dados: preencher NaN numerico (mediana) e categorico ('missing'); bool -> str
for c in num:
    m[c] = pd.to_numeric(m[c], errors='coerce').fillna(m[c].median())
for c in cat:
    m[c] = m[c].astype(str).fillna('missing')

pre = ColumnTransformer([
    ('n', StandardScaler(), num),
    ('c', OneHotEncoder(handle_unknown='ignore'), cat),
])
models = {
    'LogReg': LogisticRegression(max_iter=1000, class_weight='balanced'),
    'RandomForest': RandomForestClassifier(n_estimators=300, class_weight='balanced', random_state=0),
}
cv = StratifiedKFold(5, shuffle=True, random_state=0)
print("\n" + "="*80)
print("AUC (0.5 = moeda; >0.65 = ha sinal util) — 5-fold CV")
print("="*80)
for label in ['churn_flag','churn_evt']:
    y = m[label].astype(int)
    X = m[num+cat]
    print(f"\n--- rotulo: {label} (churn base {y.mean():.1%}) ---")
    for name, clf in models.items():
        pipe = Pipeline([('pre',pre),('clf',clf)])
        auc = cross_val_score(pipe, X, y, cv=cv, scoring='roc_auc')
        print(f"  {name:14s} AUC = {auc.mean():.3f} +/- {auc.std():.3f}")

# baseline "dummy" para referencia visual
print("\nInterpretacao: se todos os AUC ~0.5, nenhum modelo bate cara-ou-coroa ->")
print("churn NAO e explicavel/previsivel pelos dados coletados. Esse e o achado central.")

# feature importance do RF (so pra mostrar que nem as 'melhores' features ajudam)
from sklearn.ensemble import RandomForestClassifier as RF
pipe = Pipeline([('pre',pre),('clf',RF(n_estimators=300,random_state=0))]).fit(m[num+cat], m.churn_flag.astype(int))
ohe = pipe.named_steps['pre'].named_transformers_['c']
feat = num + list(ohe.get_feature_names_out(cat))
imp = pd.Series(pipe.named_steps['clf'].feature_importances_, index=feat).sort_values(ascending=False)
print("\nTop 10 features 'mais importantes' (mesmo assim inuteis se AUC~0.5):")
print((imp.head(10)*100).round(1).to_string())
