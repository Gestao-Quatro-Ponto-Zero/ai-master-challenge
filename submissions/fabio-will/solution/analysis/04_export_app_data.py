"""Exports what the console needs: the router as JSON (runs in the browser), a sample queue with
explanations and similar past tickets, parity fixtures for the JS port, and the analysis results.

Outputs go to ../app/src/data (bundled) and ../app/public/model (fetched on demand).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from common import OUT_DIR, SEED
from router import (
    NEVER_AUTO,
    SEGMENT_SENSITIVE,
    SEGMENT_WORDS,
    SENSITIVE,
    SENSITIVE_MASS,
    fit_router_and_policy,
    make_split,
    max_similarity,
    segment_sensitivity,
    vocabulary_coverage,
    word_pair_coherence,
)

APP = Path(__file__).resolve().parent.parent / "app"
DATA = APP / "src" / "data"
MODEL = APP / "public" / "model"


def dump(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{path.relative_to(APP)}  {path.stat().st_size / 1024:.0f} KB")


def explain(row_tfidf, coef_row: np.ndarray, terms: np.ndarray, k: int = 5) -> list[dict]:
    """Terms that pushed the score of the predicted queue up the most (tf-idf × weight)."""
    idx = row_tfidf.indices
    contrib = row_tfidf.data * coef_row[idx]
    order = np.argsort(-contrib)[:k]
    return [{"term": str(terms[idx[i]]), "weight": round(float(contrib[i]), 3)} for i in order if contrib[i] > 0]


def main() -> None:
    sp = make_split()
    pipe, policy, train_matrix = fit_router_and_policy(sp)
    vec, clf = pipe.named_steps["tfidf"], pipe.named_steps["clf"]
    classes = clf.classes_
    terms = vec.get_feature_names_out()

    # 1. Router for the browser. Same tokenizer contract as scikit-learn's default token_pattern.
    router_payload = {
        "version": 1,
        "classes": classes.tolist(),
        "terms": terms.tolist(),
        "idf": np.round(vec.idf_, 5).tolist(),
        "coef": np.round(clf.coef_, 5).tolist(),
        "intercept": np.round(clf.intercept_, 5).tolist(),
        "ngram": [1, 2],
        "sublinear_tf": True,
        "policy": {
            "t_auto": policy.t_auto,
            "t_assist": policy.t_assist,
            "vocab_floor": policy.c_min,
            "sensitive_mass": SENSITIVE_MASS,
            "coherence_floor": policy.t_coherence,
            "segment_words": SEGMENT_WORDS,
            "segment_sensitive": SEGMENT_SENSITIVE,
            "never_auto": list(NEVER_AUTO),
            "sensitive": list(SENSITIVE),
        },
    }
    # Content-addressed file: safe to cache as immutable, and a retrain can never be shadowed by a stale copy.
    # The browser also checks the bytes against this hash before using the model (integrity pin).
    model_bytes = json.dumps(router_payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    sha = hashlib.sha256(model_bytes).hexdigest()
    for old in MODEL.glob("router*.json"):
        old.unlink()
    MODEL.mkdir(parents=True, exist_ok=True)
    (MODEL / f"router.{sha[:12]}.json").write_bytes(model_bytes)
    print(f"public/model/router.{sha[:12]}.json  {len(model_bytes) / 1024:.0f} KB")
    dump(DATA / "model-meta.json", {"file": f"/model/router.{sha[:12]}.json", "sha256": sha, "bytes": len(model_bytes)})

    # 2. Parity fixtures: the JS port must reproduce these probabilities.
    rng = np.random.default_rng(SEED)
    fx_idx = rng.choice(len(sp.X_test), size=300, replace=False)
    fx_proba = pipe.predict_proba(sp.X_test[fx_idx])
    fx_seg = segment_sensitivity(pipe, sp.X_test[fx_idx])
    fx_coh = word_pair_coherence(pipe, sp.X_test[fx_idx])
    dump(APP / "tests" / "fixtures" / "parity.json", [
        {"text": str(sp.X_test[i]), "proba": np.round(p, 6).tolist(), "segment": round(float(g), 6), "coherence": round(float(c), 6)}
        for i, p, g, c in zip(fx_idx, fx_proba, fx_seg, fx_coh)
    ])

    # 3. Sample queue: real test tickets, stratified by tier and reason so every path shows up.
    proba = pipe.predict_proba(sp.X_test)
    sim = max_similarity(pipe, train_matrix, sp.X_test)
    cov = vocabulary_coverage(pipe, sp.X_test)
    tiers, reasons = policy.decide(proba, sim, cov, segment_sensitivity(pipe, sp.X_test), word_pair_coherence(pipe, sp.X_test))
    X_tfidf = vec.transform(sp.X_test)
    quota = {"confianca_alta": 16, "confianca_media": 8, "fila_privilegiada": 4, "possivel_conteudo_sensivel": 3, "trecho_sensivel": 3,
             "sem_historico_parecido": 3, "sequencia_incomum": 2, "confianca_baixa": 3, "vocabulario_desconhecido": 2}
    picked = []
    for reason, n in quota.items():
        cand = np.where((reasons == reason) & (np.array([len(t.split()) for t in sp.X_test]) >= 6))[0]
        picked += rng.choice(cand, size=min(n, len(cand)), replace=False).tolist()
    rng.shuffle(picked)

    queue = []
    for n, i in enumerate(picked, start=1):
        p = proba[i]
        top = np.argsort(-p)[:3]
        k = int(top[0])
        sims = (X_tfidf[i] @ train_matrix.T).toarray().ravel()
        near = np.argsort(-sims)[:3]
        queue.append({
            "id": f"T-{10240 + n}",
            "text": str(sp.X_test[i]),
            "label": str(sp.y_test[i]),
            "pred": str(classes[k]),
            "top": [{"queue": str(classes[j]), "p": round(float(p[j]), 4)} for j in top],
            "tier": str(tiers[i]),
            "reason": str(reasons[i]),
            "coverage": round(float(cov[i]), 3),
            "similarity": round(float(sim[i]), 3),
            "why": explain(X_tfidf[i], clf.coef_[k], terms),
            "similar": [{"text": str(sp.X_train[j])[:220], "queue": str(sp.y_train[j]), "similarity": round(float(sims[j]), 3)} for j in near],
        })
    dump(DATA / "queue.json", queue)

    # 4. Analysis results for the director's panel, the lab and the stress page.
    for name in ["audit.json", "lab.json", "stress.json", "adversarial.json"]:
        payload = json.loads((OUT_DIR / name).read_text(encoding="utf-8"))
        if name == "lab.json":
            payload.pop("confusion_matrix", None)
        dump(DATA / name, payload)

    overall = {t: int((tiers == t).sum()) for t in ["auto", "assist", "human"]}
    print("queue tiers:", {t: sum(q["tier"] == t for q in queue) for t in ["auto", "assist", "human"]}, "test tiers:", overall)


if __name__ == "__main__":
    main()
