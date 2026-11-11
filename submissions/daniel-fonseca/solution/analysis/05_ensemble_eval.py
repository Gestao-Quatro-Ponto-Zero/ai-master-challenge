"""Do resultado da avaliação para a política de produção (ADR-0005).

1. TF-IDF compacto: dá para exportar o modelo em JSON (vocabulário + idf + coeficientes) e rodar
   em TypeScript/JS (n8n Code node ou função da Vercel) sem perder acurácia?
2. Concordância: quando o TF-IDF e o kNN do RAG (pgvector, 512 dims) concordam, quanto cobrimos e com que precisão?
   Dois métodos independentes concordando é um critério de automação mais robusto que um limiar isolado.

Saída: solution/analysis/output/ensemble_eval.json
Uso: .venv/bin/python solution/analysis/05_ensemble_eval.py
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

warnings.filterwarnings("ignore", category=RuntimeWarning)  # avisos espúrios do matmul no macOS
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import load_raw_datasets as raw  # noqa: E402

df = raw.ds2()
train, test = df[df.split == "train"], df[df.split == "test"]
classes = sorted(df.topic_group.unique())
y_te = test.topic_group.values
out = {}

print("## 1. TF-IDF: completo × compacto")
models = {}
for name, kw in {"full_1-2gram": dict(ngram_range=(1, 2), min_df=2),
                 "compact_20k": dict(ngram_range=(1, 2), min_df=3, max_features=20000),
                 "compact_10k_unigram": dict(ngram_range=(1, 1), min_df=3, max_features=10000)}.items():
    vec = TfidfVectorizer(sublinear_tf=True, **kw)
    lr = LogisticRegression(max_iter=2000, C=5).fit(vec.fit_transform(train.document), train.topic_group)
    p = lr.predict_proba(vec.transform(test.document))
    acc = float((lr.classes_[p.argmax(1)] == y_te).mean())
    size_mb = (len(vec.vocabulary_) * (len(classes) + 1) * 8) / 1e6
    models[name] = (vec, lr, p)
    out[name] = {"vocab": len(vec.vocabulary_), "accuracy": round(acc, 4), "approx_json_mb": round(size_mb, 1)}
    print(f"{name:22s} vocab {len(vec.vocabulary_):>7,} | acurácia {acc:.3f} | JSON ≈ {size_mb:.1f} MB")

print("\n## 2. Concordância TF-IDF compacto × kNN 512 (RAG)")
E = np.load(ROOT / "data/embeddings/ds2_te3s_1536.npy").astype(np.float32)[:, :512]
E /= np.linalg.norm(E, axis=1, keepdims=True)
Vtr, Vte = E[train.index.values], E[test.index.values]
idx = {c: i for i, c in enumerate(classes)}
ytr = np.array([idx[c] for c in train.topic_group])
k, share = 15, np.zeros((len(Vte), len(classes)))
for s in range(0, len(Vte), 1000):
    sims = Vte[s:s + 1000] @ Vtr.T
    top = np.argpartition(-sims, k, axis=1)[:, :k]
    w = np.take_along_axis(sims, top, axis=1).clip(min=0)
    v = np.zeros((len(top), len(classes)))
    np.add.at(v, (np.repeat(np.arange(len(top)), k), ytr[top].ravel()), w.ravel())
    share[s:s + 1000] = v / v.sum(1, keepdims=True)

_, lr, p_tf = models["compact_20k"]
pred_tf, conf_tf = lr.classes_[p_tf.argmax(1)], p_tf.max(1)
pred_kn, conf_kn = np.array(classes)[share.argmax(1)], share.max(1)
agree = pred_tf == pred_kn
rows = []
for t in (0.0, 0.6, 0.7, 0.8, 0.9):
    m = agree & (conf_tf >= t) & (conf_kn >= t)
    rows.append({"min_conf_both": t, "coverage": round(float(m.mean()), 4), "precision": round(float((pred_tf[m] == y_te[m]).mean()), 4)})
    print(f"concordam e confiança ≥ {t:.1f} nos dois: cobertura {m.mean():.1%} → precisão {(pred_tf[m] == y_te[m]).mean():.1%}")
dis = ~agree
print(f"discordam: {dis.mean():.1%} dos tickets | TF-IDF acerta {(pred_tf[dis] == y_te[dis]).mean():.1%} deles → vão para humano")
out["agreement"] = {"rows": rows, "disagree_share": round(float(dis.mean()), 4),
                    "tfidf_acc_on_disagree": round(float((pred_tf[dis] == y_te[dis]).mean()), 4)}

# precisão por classe no critério "concordam + ≥0,8" (para a política por categoria)
m = agree & (conf_tf >= .8) & (conf_kn >= .8)
per = {c: {"coverage": round(float(m[y_te == c].mean()), 3),
           "precision": round(float((y_te[m & (pred_tf == c)] == c).mean()), 3) if (m & (pred_tf == c)).any() else None}
       for c in classes}
print("\npor categoria (concordam + ≥0,8):", " | ".join(f"{c[:10]} {v['coverage']:.0%}@{v['precision']:.0%}" for c, v in per.items()))
out["agreement_0_8_per_class"] = per

print("\n## 3. Política de 3 níveis (ADR-0005) aplicada ao holdout")
SENSITIVE = {"HR Support", "Administrative rights"}  # só humano, decisão do Daniel (ADR-0005)
sens = np.isin(pred_tf, list(SENSITIVE)) | np.isin(pred_kn, list(SENSITIVE))
low = (conf_tf < 0.5) & (conf_kn < 0.5)
lvl3 = sens | low
lvl1 = ~lvl3 & agree & (conf_tf >= 0.8) & (conf_kn >= 0.8)
lvl2 = ~lvl3 & ~lvl1
tiers = {}
for name, m in (("1_automatico", lvl1), ("2_revisao_humana", lvl2), ("3_so_humano", lvl3)):
    tiers[name] = {"share": round(float(m.mean()), 4), "classification_precision": round(float((pred_tf[m] == y_te[m]).mean()), 4)}
    print(f"nível {name:18s} {m.mean():6.1%} dos tickets | precisão da classificação {(pred_tf[m] == y_te[m]).mean():.1%}")
print(f"  nível 3 por categoria sensível: {(sens).mean():.1%} | por baixa confiança: {(low & ~sens).mean():.1%}")
print(f"  tickets realmente sensíveis que escapariam do nível 3: {(np.isin(y_te, list(SENSITIVE)) & ~lvl3).sum()} de {np.isin(y_te, list(SENSITIVE)).sum()}")
true_sens = np.isin(y_te, list(SENSITIVE))
leak = {n: int((true_sens & m).sum()) for n, m in (("1_automatico", lvl1), ("2_revisao_humana", lvl2))}
print(f"  onde caem os sensíveis que escapam: {leak} (no nível 1 = {leak['1_automatico'] / max(lvl1.sum(), 1):.2%} do nível 1)")
tiers["sensitive_escapes"] = leak
out["tiers"] = tiers
out["tiers_rule"] = "nível 3 = categoria sensível prevista por qualquer método OU confiança < 0,5 nos dois; nível 1 = concordam e ≥ 0,8 nos dois; nível 2 = resto"
(ROOT / "solution/analysis/output/ensemble_eval.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
