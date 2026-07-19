# -*- coding: utf-8 -*-
"""D-018 — Treina o classificador MULTILÍNGUE servido pelo portal (rodar 1x).

Pré-requisito: python src/embed_corpus_ml.py até DONE (embeddings_d2_ml.npy).

O que faz:
1. LogReg sobre embeddings multilíngues (mesmo split estratificado seed=42);
2. avalia no teste em inglês (metrics_ml.json) + smoke cross-lingual em pt-BR;
3. recalcula o gate de confiança (menor threshold com accuracy>=90% nos cobertos);
4. troca os artefatos servidos (backup do baseline inglês em models/en_baseline/):
   classifier.joblib (EmbeddingClassifier), faiss.index (espaço multilíngue),
   embeddings.npy, metadata.json (classifier_type=embed_logreg).

Trade-off declarado: o macro-F1 em inglês cai vs o TF-IDF vencedor da FASE 5
(0,865) — o ganho é a transferência cross-lingual (pergunta pt-BR, corpus en),
que o TF-IDF não faz por construção (zero sobreposição de tokens).
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data_prep import TOPIC_CLASSES, build_dataset2
from src.ticket_ai import (MODELS_DIR, MULTILINGUAL_MODEL_NAME, EmbeddingClassifier,
                           coverage_accuracy_curve, evaluate, load_split,
                           make_embed_logreg, pick_threshold)

PT_PROBES = [
    ("Não consigo entrar na minha conta, a senha expirou. Preciso do reset urgente.", "Access"),
    ("O drive compartilhado está sem espaço e não consigo salvar meus arquivos.", "Storage"),
    ("Precisamos comprar um notebook novo para quem começa na segunda. Podem cotar?", "Purchase"),
    ("Meu monitor não liga mais, já testei o cabo e a tomada.", "Hardware"),
    ("Preciso de acesso de administrador no sistema financeiro.", "Administrative rights"),
]


def main() -> None:
    t0 = time.time()
    emb_path = MODELS_DIR / "embeddings_d2_ml.npy"
    d2 = build_dataset2()
    emb_all = np.load(emb_path)
    assert len(emb_all) == len(d2), "rode src/embed_corpus_ml.py até DONE"

    train, test = load_split()
    pos = pd.Series(np.arange(len(d2)), index=d2["doc_id"].values)
    emb_tr = emb_all[pos[train["doc_id"].values].values]
    emb_te = emb_all[pos[test["doc_id"].values].values]
    ytr = np.asarray(train["Topic_group"].astype(str).tolist())
    yte = np.asarray(test["Topic_group"].astype(str).tolist())

    logreg = make_embed_logreg()
    logreg.fit(emb_tr, ytr)
    proba = logreg.predict_proba(emb_te)
    classes = list(logreg.classes_)
    result = evaluate(yte, np.asarray(classes)[proba.argmax(1)], "embed_logreg_multilingual")
    print(f"[{time.time()-t0:5.0f}s] f1_macro={result['f1_macro']:.4f} "
          f"accuracy={result['accuracy']:.4f} (teste em inglês, n={len(yte):,})")

    curve = coverage_accuracy_curve(proba, yte, classes)
    thr = pick_threshold(curve, min_accuracy=0.90)
    cov_row = curve.loc[curve["threshold"] == thr].iloc[0]
    print(f"Gate: threshold {thr} → cobertura {cov_row['coverage']:.1%}, "
          f"accuracy nos cobertos {cov_row['accuracy_covered']:.1%}")

    # smoke cross-lingual (o motivo da troca — D-018)
    clf = EmbeddingClassifier(logreg, MULTILINGUAL_MODEL_NAME)
    probes_out = []
    hits = 0
    for text, expected in PT_PROBES:
        p = clf.predict_proba([text])[0]
        got = classes[int(p.argmax())]
        ok = got == expected
        hits += ok
        probes_out.append({"text": text, "expected": expected, "got": got,
                           "confidence": round(float(p.max()), 3), "ok": bool(ok)})
        print(f"  pt-BR probe: {'OK ' if ok else 'ERR'} {expected:<22} → {got} "
              f"({p.max():.0%})")
    print(f"Cross-lingual smoke: {hits}/{len(PT_PROBES)}")

    # --- troca de artefatos (backup do baseline inglês) ---------------------
    import faiss
    bak = MODELS_DIR / "en_baseline"
    bak.mkdir(exist_ok=True)
    for name in ("classifier.joblib", "faiss.index", "metadata.json", "embeddings.npy"):
        src = MODELS_DIR / name
        if src.exists() and not (bak / name).exists():
            shutil.move(str(src), str(bak / name))

    joblib.dump(clf, MODELS_DIR / "classifier.joblib")
    index = faiss.IndexFlatIP(emb_all.shape[1])
    index.add(emb_all.astype(np.float32))
    faiss.write_index(index, str(MODELS_DIR / "faiss.index"))
    np.save(MODELS_DIR / "embeddings.npy", emb_all.astype(np.float32))
    (MODELS_DIR / "metadata.json").write_text(json.dumps({
        "threshold": thr,
        "embedder": MULTILINGUAL_MODEL_NAME,
        "classifier_type": "embed_logreg",
        "classes": TOPIC_CLASSES,
        "seed": 42,
    }, indent=2), encoding="utf-8")
    (MODELS_DIR / "metrics_ml.json").write_text(json.dumps({
        "model": "embed_logreg_multilingual",
        "embedder": MULTILINGUAL_MODEL_NAME,
        "f1_macro": result["f1_macro"],
        "accuracy": result["accuracy"],
        "precision_macro": result["precision_macro"],
        "recall_macro": result["recall_macro"],
        "per_class": result["per_class"],
        "threshold": thr,
        "coverage_at_threshold": float(cov_row["coverage"]),
        "accuracy_covered_at_threshold": float(cov_row["accuracy_covered"]),
        "threshold_curve": curve.to_dict(orient="records"),
        "pt_probes": probes_out,
        "baseline_en_f1_macro_tfidf": 0.8652,
        "train_seconds": round(time.time() - t0, 1),
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Artefatos trocados em {MODELS_DIR} (baseline inglês em en_baseline/) "
          f"— {time.time()-t0:,.0f}s")


if __name__ == "__main__":
    main()
