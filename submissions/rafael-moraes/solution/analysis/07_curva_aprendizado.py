"""Plano de 30 dias — quantos tickets rotulados a empresa precisa? Curva de aprendizado no Dataset 2.
Treina com amostras crescentes do conjunto de treino e mede sempre no mesmo conjunto de teste.
Uso: python 07_curva_aprendizado.py caminho/all_tickets_processed_improved_v3.csv
"""
import sys
import numpy as np, pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

d = pd.read_csv(sys.argv[1])
X_tr, X_te, y_tr, y_te = train_test_split(d.Document, d.Topic_group, test_size=0.2, stratify=d.Topic_group, random_state=42)
print("rotulados | acerto geral | IA sozinha (limiar 80%/90%) | acerto da IA sozinha")
for n in [250, 500, 1000, 2000, 5000, 10000, len(X_tr)]:
    Xs, _, ys, _ = train_test_split(X_tr, y_tr, train_size=n, stratify=y_tr, random_state=1) if n < len(X_tr) else (X_tr, None, y_tr, None)
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2 if n < 5000 else 3, max_features=20000, sublinear_tf=True)
    clf = LogisticRegression(C=5, max_iter=2000, class_weight="balanced").fit(vec.fit_transform(Xs), ys)
    P = clf.predict_proba(vec.transform(X_te)); p = P.argmax(1); c = P.max(1)
    ok = clf.classes_[p] == y_te.values
    adm = list(clf.classes_).index("Administrative rights"); a = c >= np.where(p == adm, 0.9, 0.8)
    print(f"{n:9d} | {ok.mean():11.1%} | {a.mean():26.1%} | {ok[a].mean():.1%}")
