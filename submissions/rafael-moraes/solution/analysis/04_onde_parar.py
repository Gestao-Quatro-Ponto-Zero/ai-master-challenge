"""Fase 3 — Onde a automação deve parar: desempenho por categoria no limiar de confiança.
Uso: python 04_onde_parar.py caminho/all_tickets_processed_improved_v3.csv [limiar]
"""
import sys
import numpy as np, pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

d = pd.read_csv(sys.argv[1]); t = float(sys.argv[2]) if len(sys.argv) > 2 else 0.80
X_tr, X_te, y_tr, y_te = train_test_split(d.Document, d.Topic_group, test_size=0.2, stratify=d.Topic_group, random_state=42)
vec = TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_features=40000, sublinear_tf=True)
clf = LogisticRegression(C=5, max_iter=2000, class_weight="balanced").fit(vec.fit_transform(X_tr), y_tr)
P = clf.predict_proba(vec.transform(X_te)); pred = clf.classes_[P.argmax(1)]; conf = P.max(1)
r = pd.DataFrame({"real": y_te.values, "pred": pred, "conf": conf, "texto": X_te.values})
r["auto"] = r.conf >= t; r["ok"] = r.real == r.pred
g = r.groupby("pred").apply(lambda x: pd.Series({"tickets": len(x), "automatiza": x.auto.mean(),
     "acerto_auto": x[x.auto].ok.mean(), "acerto_revisao": x[~x.auto].ok.mean()}), include_groups=False)
print(f"Limiar {t}\n", g.round(3).sort_values("acerto_auto"))
print("\nConfusões mais frequentes entre os automatizados errados:")
print(r[r.auto & ~r.ok].groupby(["real", "pred"]).size().sort_values(ascending=False).head(5))
print("\nExemplos de baixa confiança (vão para humano):")
for _, x in r[~r.auto].sample(5, random_state=3).iterrows():
    print(f"  [{x.conf:.0%} → {x.pred} | real {x.real}] {x.texto[:110]}")
