"""Avaliação complementar: F1 no teste separando linhas com/sem vizinho no treino (cosseno >= 0,80) — risco de vazamento residual."""
import json, joblib, pandas as pd
from sklearn.metrics import f1_score
te = pd.read_csv("splits/test.csv"); clf = joblib.load("model/classifier_pipeline.pkl")
p = clf.predict(te.Document); out = {}
for k, m in [("com_vizinho_treino", te.test_has_train_neighbor_0_80), ("sem_vizinho_treino", ~te.test_has_train_neighbor_0_80)]:
    out[k] = dict(n=int(m.sum()), f1_macro=round(float(f1_score(te.Topic_group[m], p[m], average="macro")), 4), accuracy=round(float((p[m] == te.Topic_group[m]).mean()), 4))
json.dump(out, open("evaluation/residual_leakage_eval.json", "w"), indent=1, ensure_ascii=False); print(out)
