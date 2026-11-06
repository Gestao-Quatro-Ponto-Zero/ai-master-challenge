"""Fase 4 — Treina o classificador final e exporta para o protótipo (roda no navegador, sem servidor).
Gera prototype/model.json (vocabulário, idf, pesos) e prototype/eval.json (previsões no conjunto de teste).
Uso: python 05_exportar_modelo.py caminho/all_tickets_processed_improved_v3.csv ../prototype
"""
import sys, json
import numpy as np, pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

src, out = sys.argv[1], sys.argv[2]
MAXF = int(sys.argv[3]) if len(sys.argv) > 3 else 20000
d = pd.read_csv(src)
X_tr, X_te, y_tr, y_te = train_test_split(d.Document, d.Topic_group, test_size=0.2, stratify=d.Topic_group, random_state=42)
vec = TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_features=MAXF, sublinear_tf=True)
clf = LogisticRegression(C=5, max_iter=2000, class_weight="balanced").fit(vec.fit_transform(X_tr), y_tr)
P = clf.predict_proba(vec.transform(X_te))
classes = list(clf.classes_)
order = np.argsort(-P, axis=1)
acc = (np.array(classes)[order[:, 0]] == y_te.values).mean()
print(f"max_features={MAXF} acurácia teste={acc:.4f}")

vocab = sorted(vec.vocabulary_, key=vec.vocabulary_.get)
model = {"classes": classes, "vocab": vocab, "idf": [round(float(x), 4) for x in vec.idf_],
         "coef": [[round(float(x), 3) for x in row] for row in clf.coef_],
         "intercept": [round(float(x), 4) for x in clf.intercept_],
         "test_accuracy": round(float(acc), 4), "n_train": len(X_tr), "n_test": len(X_te)}
json.dump(model, open(f"{out}/model.json", "w"), separators=(",", ":"))

ci = {c: i for i, c in enumerate(classes)}
ev = {"y": [ci[c] for c in y_te], "p1": order[:, 0].tolist(), "p2": order[:, 1].tolist(),
      "c": [round(float(x), 3) for x in P.max(1)]}
json.dump(ev, open(f"{out}/eval.json", "w"), separators=(",", ":"))

# Amostra para a fila de triagem (tickets do teste, nunca vistos no treino)
s = pd.DataFrame({"text": X_te.values, "real": y_te.values}).sample(80, random_state=7)
s.to_json(f"{out}/queue_sample.json", orient="records")
# Casos de verificação para comparar Python x JavaScript
chk = [{"text": t, "probs": [round(float(x), 4) for x in p]} for t, p in zip(X_te.values[:200], P[:200])]
json.dump(chk, open(f"{out}/parity_check.json", "w"))
