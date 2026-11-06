"""Fase 4 — Classificador de tickets (Dataset 2): treino, teste em dados nunca vistos, curva de cobertura x erro.
Uso: python 03_classificador.py caminho/all_tickets_processed_improved_v3.csv
"""
import sys, json
import numpy as np, pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

d = pd.read_csv(sys.argv[1])
X_tr, X_te, y_tr, y_te = train_test_split(d.Document, d.Topic_group, test_size=0.2, stratify=d.Topic_group, random_state=42)
vec = TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_features=40000, sublinear_tf=True)
Xtr = vec.fit_transform(X_tr); Xte = vec.transform(X_te)
clf = LogisticRegression(C=5, max_iter=2000, class_weight="balanced")
clf.fit(Xtr, y_tr)
proba = clf.predict_proba(Xte); pred = clf.classes_[proba.argmax(1)]; conf = proba.max(1)
print(f"Treino {len(X_tr)} | Teste {len(X_te)} | Acurácia {accuracy_score(y_te, pred):.1%}")
print(classification_report(y_te, pred, digits=3))
print(pd.DataFrame(confusion_matrix(y_te, pred, labels=clf.classes_), index=clf.classes_, columns=clf.classes_))
ok = (pred == y_te.values)
curve = []
for t in np.round(np.arange(0.30, 0.96, 0.05), 2):
    m = conf >= t
    curve.append({"limiar": float(t), "cobertura": float(m.mean()), "acuracia_auto": float(ok[m].mean()) if m.any() else None})
    print(f"limiar {t:.2f}: automatiza {m.mean():5.1%} | acerto nos automatizados {ok[m].mean():.1%}")
json.dump(curve, open("curva_limiar.json", "w"), indent=1)
