"""Auditoria — (1) limiar confirmado em validação separada; (2) exporta os textos de teste para medir o efeito das regras.
Uso: python 06_validacao_e_regras.py caminho/all_tickets_processed_improved_v3.csv saida_textos_teste.json
"""
import sys, json
import numpy as np, pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

d = pd.read_csv(sys.argv[1])
X_tr, X_te, y_tr, y_te = train_test_split(d.Document, d.Topic_group, test_size=0.2, stratify=d.Topic_group, random_state=42)
json.dump([{"text": t, "real": y} for t, y in zip(X_te, y_te)], open(sys.argv[2], "w"))

# Validação: separa 20% do TREINO, treina no restante e mede no conjunto de validação e no de teste.
X_fit, X_val, y_fit, y_val = train_test_split(X_tr, y_tr, test_size=0.25, stratify=y_tr, random_state=7)
vec = TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_features=20000, sublinear_tf=True)
clf = LogisticRegression(C=5, max_iter=2000, class_weight="balanced").fit(vec.fit_transform(X_fit), y_fit)
adm = list(clf.classes_).index("Administrative rights")
for nome, X, y in [("validação", X_val, y_val), ("teste", X_te, y_te)]:
    P = clf.predict_proba(vec.transform(X)); p = P.argmax(1); c = P.max(1); ok = clf.classes_[p] == y.values
    thr = np.where(p == adm, 0.9, 0.8); a = c >= thr
    top2 = np.argsort(-P, 1)[:, :2]; yi = np.array([list(clf.classes_).index(v) for v in y])
    in2 = (top2 == yi[:, None]).any(1)
    print(f"{nome:10s} n={len(y):5d} acerto={ok.mean():.1%} | IA sozinha {a.mean():.1%} com {ok[a].mean():.1%} | "
          f"dúvida: acerto {ok[~a].mean():.1%}, certa entre as 2 opções {in2[~a].mean():.1%}")
