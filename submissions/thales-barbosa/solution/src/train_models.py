# -*- coding: utf-8 -*-
"""FASE 5 — Treina, compara e salva os modelos (rodar 1x: python src/train_models.py).

Saídas em models/: classifier.joblib, faiss.index, corpus.parquet,
embeddings.npy, metadata.json, metrics.json, predictions.parquet (p/ notebook).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data_prep import TOPIC_CLASSES
from src.ticket_ai import (MODELS_DIR, coverage_accuracy_curve,
                           evaluate, load_split, make_embed_logreg,
                           make_tfidf_linsvc, make_tfidf_logreg,
                           pick_threshold, save_artifacts)


def main() -> None:
    t0 = time.time()
    train, test = load_split()
    Xtr = train["Document"].tolist()
    Xte = test["Document"].tolist()
    # numpy explícito: dtype arrow-backed quebra o _safe_indexing do
    # CalibratedClassifierCV (indexação por array em ArrowExtensionArray)
    ytr = np.asarray(train["Topic_group"].astype(str).tolist())
    yte = np.asarray(test["Topic_group"].astype(str).tolist())
    print(f"Split estratificado: {len(train):,} treino / {len(test):,} teste "
          f"(seed=42, proporções por classe preservadas)")

    results, proba_by_model = [], {}

    # --- candidato 1: TF-IDF + LogReg -------------------------------------
    m1 = make_tfidf_logreg()
    m1.fit(Xtr, ytr)
    p1 = m1.predict_proba(Xte)
    results.append(evaluate(yte, m1.classes_[p1.argmax(1)], "tfidf_logreg"))
    proba_by_model["tfidf_logreg"] = (p1, list(m1.classes_))
    print(f"[{time.time()-t0:6.0f}s] tfidf_logreg  f1_macro={results[-1]['f1_macro']:.4f}")

    # --- candidato 2: TF-IDF + LinearSVC calibrado ------------------------
    m2 = make_tfidf_linsvc()
    m2.fit(Xtr, ytr)
    p2 = m2.predict_proba(Xte)
    results.append(evaluate(yte, m2.classes_[p2.argmax(1)], "tfidf_linsvc"))
    proba_by_model["tfidf_linsvc"] = (p2, list(m2.classes_))
    print(f"[{time.time()-t0:6.0f}s] tfidf_linsvc  f1_macro={results[-1]['f1_macro']:.4f}")

    # --- candidato 3: embeddings MiniLM + LogReg ---------------------------
    # embeddings pré-computados por src/embed_corpus.py (resumável), na ordem
    # natural do d2 pós-filtro; mapeamos doc_id -> posição
    from src.data_prep import build_dataset2
    d2 = build_dataset2()
    emb_all = np.load(MODELS_DIR / "embeddings_d2.npy")
    assert len(emb_all) == len(d2), "rode src/embed_corpus.py até DONE"
    pos = pd.Series(np.arange(len(d2)), index=d2["doc_id"].values)
    emb_tr = emb_all[pos[train["doc_id"].values].values]
    emb_te = emb_all[pos[test["doc_id"].values].values]
    m3 = make_embed_logreg()
    m3.fit(emb_tr, ytr)
    p3 = m3.predict_proba(emb_te)
    results.append(evaluate(yte, m3.classes_[p3.argmax(1)], "embed_logreg"))
    proba_by_model["embed_logreg"] = (p3, list(m3.classes_))
    print(f"[{time.time()-t0:6.0f}s] embed_logreg  f1_macro={results[-1]['f1_macro']:.4f}")

    # --- escolha do vencedor (macro-F1; empate ~0,005 -> mais simples) -----
    ranked = sorted(results, key=lambda r: r["f1_macro"], reverse=True)
    best_name = ranked[0]["model"]
    if ranked[0]["f1_macro"] - ranked[1]["f1_macro"] < 0.005:
        simplicity = {"tfidf_logreg": 0, "tfidf_linsvc": 1, "embed_logreg": 2}
        best_name = min(ranked[:2], key=lambda r: simplicity[r["model"]])["model"]
        print(f"Empate técnico (<0,005) -> critério de simplicidade: {best_name}")
    winner = {"tfidf_logreg": m1, "tfidf_linsvc": m2, "embed_logreg": m3}[best_name]
    print(f"VENCEDOR: {best_name}")

    # --- threshold de confiança (gate FASE 4) ------------------------------
    proba_w, classes_w = proba_by_model[best_name]
    curve = coverage_accuracy_curve(proba_w, yte, classes_w)
    thr = pick_threshold(curve, min_accuracy=0.90)
    cov = curve.loc[curve["threshold"] == thr]
    print(f"Threshold p/ accuracy>=90%: {thr} (cobertura {float(cov['coverage'].iloc[0]):.1%})")

    # --- corpus p/ busca semântica: d2 na ordem natural (= emb_all) --------
    corpus = d2

    # --- persistência -------------------------------------------------------
    metrics = {
        "results": [{k: v for k, v in r.items() if k != "confusion"} for r in results],
        "confusions": {r["model"]: r["confusion"] for r in results},
        "winner": best_name,
        "threshold_curve": curve.to_dict(orient="records"),
        "threshold": thr,
        "split": {"train": len(train), "test": len(test), "seed": 42, "stratified": True},
        "train_seconds": round(time.time() - t0, 1),
    }
    if best_name == "embed_logreg":
        # produção precisaria embutir o embedder no pipeline; registrado no doc
        raise SystemExit("embed_logreg venceu — ajustar persistência antes de salvar")
    save_artifacts(winner, thr, corpus, emb_all, metrics)

    preds = test[["doc_id", "Topic_group"]].copy()
    preds["pred"] = classes_w and np.asarray(classes_w)[proba_w.argmax(1)]
    preds["confidence"] = proba_w.max(1)
    preds.to_parquet(MODELS_DIR / "predictions.parquet")
    print(f"Artefatos salvos em {MODELS_DIR} ({time.time()-t0:,.0f}s no total)")


if __name__ == "__main__":
    main()
