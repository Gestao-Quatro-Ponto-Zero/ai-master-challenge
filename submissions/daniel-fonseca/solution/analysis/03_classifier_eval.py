"""Avaliação dos classificadores do DS2 no mesmo holdout (ds2_tickets.split, 80/20 estratificado, seed 42).

Métodos:
  A. baseline  — TF-IDF + regressão logística (barato, determinístico)
  B. kNN       — vizinhos mais próximos por embedding (é o que o RAG usa: mostra os casos parecidos)
  C. emb + LR  — regressão logística sobre os embeddings
  B e C rodam em 1536 e em 512 dimensões (truncar + renormalizar = parâmetro `dimensions` da OpenAI).

Métricas: acurácia, F1 macro, F1 por classe, matriz de confusão e a curva cobertura × precisão
(quanto dá para automatizar a cada limiar de confiança) — é dela que saem os limiares dos 3 níveis (ADR-0005).

Saída: solution/analysis/output/classifier_eval.json
Uso: .venv/bin/python solution/analysis/03_classifier_eval.py [--skip-embeddings]
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import load_raw_datasets as raw  # noqa: E402

OUT = ROOT / "solution/analysis/output"
EMB = ROOT / "data/embeddings/ds2_te3s_1536.npy"
THRESHOLDS = [0.0, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95]

df = raw.ds2()
train, test = df[df.split == "train"], df[df.split == "test"]
classes = sorted(df.topic_group.unique())
y_tr, y_te = train.topic_group.values, test.topic_group.values


def report(name: str, pred: np.ndarray, conf: np.ndarray, seconds: float) -> dict:
    curve = []
    for t in THRESHOLDS:
        m = conf >= t
        curve.append({"threshold": t, "coverage": round(float(m.mean()), 4),
                      "precision": round(float((pred[m] == y_te[m]).mean()), 4) if m.any() else None})
    r = {
        "method": name,
        "accuracy": round(accuracy_score(y_te, pred), 4),
        "f1_macro": round(f1_score(y_te, pred, average="macro"), 4),
        "f1_per_class": dict(zip(classes, np.round(f1_score(y_te, pred, labels=classes, average=None), 4).tolist())),
        "coverage_precision": curve,
        "confusion_matrix": {"labels": classes, "matrix": confusion_matrix(y_te, pred, labels=classes).tolist()},
        "seconds": round(seconds, 1),
    }
    pc = " ".join(f"{c[:8]}={v:.2f}" for c, v in r["f1_per_class"].items())
    print(f"\n## {name}: acurácia {r['accuracy']:.3f} | F1 macro {r['f1_macro']:.3f} | {seconds:.0f}s\n  F1/classe: {pc}")
    print("  cobertura→precisão: " + " · ".join(
        f"≥{c['threshold']:.2f}: {c['coverage']:.0%}→{c['precision']:.1%}" for c in curve if c["precision"] is not None))
    return r


results = []

# A. baseline TF-IDF + LR
t0 = time.time()
vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
Xtr, Xte = vec.fit_transform(train.document), vec.transform(test.document)
lr = LogisticRegression(max_iter=2000, C=5)
lr.fit(Xtr, y_tr)
proba = lr.predict_proba(Xte)
results.append(report("tfidf_lr", lr.classes_[proba.argmax(1)], proba.max(1), time.time() - t0))

if "--skip-embeddings" not in sys.argv and EMB.exists():
    E = np.load(EMB).astype(np.float32)
    for dims in (1536, 512):
        V = E[:, :dims]
        V = V / np.linalg.norm(V, axis=1, keepdims=True)
        Vtr, Vte = V[train.index.values], V[test.index.values]

        # B. kNN ponderado por similaridade (k=15)
        t0 = time.time()
        k, cls_idx = 15, {c: i for i, c in enumerate(classes)}
        ytr_idx = np.array([cls_idx[c] for c in y_tr])
        pred, conf, top1 = [], [], []
        for s in range(0, len(Vte), 1000):
            with np.errstate(all="ignore"):  # avisos espúrios do matmul (Accelerate/macOS); checado abaixo
                sims = Vte[s:s + 1000] @ Vtr.T
            assert np.isfinite(sims).all()
            top = np.argpartition(-sims, k, axis=1)[:, :k]
            w = np.take_along_axis(sims, top, axis=1).clip(min=0)
            votes = np.zeros((len(top), len(classes)))
            np.add.at(votes, (np.repeat(np.arange(len(top)), k), ytr_idx[top].ravel()), w.ravel())
            share = votes / votes.sum(1, keepdims=True)
            pred += [classes[i] for i in share.argmax(1)]
            conf += share.max(1).tolist()
            top1 += sims.max(1).tolist()
        r = report(f"knn15_{dims}", np.array(pred), np.array(conf), time.time() - t0)
        # vazamento: tickets de teste quase idênticos a algum de treino inflam a métrica
        top1, pred_a = np.array(top1), np.array(pred)
        for cut in (0.95, 0.98):
            near = top1 >= cut
            r[f"near_dup_{cut}"] = {"share": round(float(near.mean()), 4),
                                    "accuracy_without": round(float((pred_a[~near] == y_te[~near]).mean()), 4)}
            print(f"  quase-duplicatas (sim ≥ {cut}): {near.mean():.1%} do teste | acurácia sem elas: {r[f'near_dup_{cut}']['accuracy_without']:.3f}")
        results.append(r)

        # C. LR sobre embeddings
        t0 = time.time()
        lre = LogisticRegression(max_iter=3000, C=10)
        lre.fit(Vtr, y_tr)
        p = lre.predict_proba(Vte)
        results.append(report(f"emb_lr_{dims}", lre.classes_[p.argmax(1)], p.max(1), time.time() - t0))
elif "--skip-embeddings" not in sys.argv:
    print(f"\n(embeddings ainda não existem em {EMB.relative_to(ROOT)} — rode scripts/embed_ds2.py)")

OUT.mkdir(parents=True, exist_ok=True)
payload = {"dataset": "DS2", "n_train": len(train), "n_test": len(test), "classes": classes,
           "class_share_test": test.topic_group.value_counts(normalize=True).round(4).to_dict(), "results": results}
(OUT / "classifier_eval.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1))
print(f"\nsalvo: {(OUT / 'classifier_eval.json').relative_to(ROOT)}")
