"""LLM zero-shot no DS2: o modelo recebe só o texto e os nomes das 8 categorias, sem exemplos.

Amostra: 50 tickets de teste por categoria (400), seed 42 — mesmo holdout dos demais métodos.
Compara, NA MESMA amostra, com o baseline TF-IDF + LR, para a comparação ser justa.

Saída: solution/analysis/output/zero_shot_eval.json (inclui as respostas brutas)
Uso: .venv/bin/python solution/analysis/04_zero_shot_eval.py [--model gpt-5.4-mini] [--n 50]
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import load_raw_datasets as raw  # noqa: E402

arg = lambda name, default: sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default  # noqa: E731
MODEL, N = arg("--model", "gpt-5.4-mini"), int(arg("--n", "50"))

raw.load_env()
KEY = os.environ["OPENAI_API_KEY"]
df = raw.ds2()
train, test = df[df.split == "train"], df[df.split == "test"]
classes = sorted(df.topic_group.unique())
sample = test.groupby("topic_group", group_keys=False).apply(lambda g: g.sample(N, random_state=42))

SYSTEM = ("You classify IT service desk tickets. The text is preprocessed (lowercase, stopwords and names removed). "
          f"Choose exactly one category from: {', '.join(classes)}. "
          "Return JSON with the category and your confidence between 0 and 1.")
SCHEMA = {"name": "ticket_class", "strict": True, "schema": {
    "type": "object", "additionalProperties": False, "required": ["category", "confidence"],
    "properties": {"category": {"type": "string", "enum": classes}, "confidence": {"type": "number"}}}}


def classify(text: str) -> dict:
    body = json.dumps({"model": MODEL, "reasoning_effort": "low",
                       "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": text[:6000]}],
                       "response_format": {"type": "json_schema", "json_schema": SCHEMA}}).encode()
    for attempt in range(6):
        req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=body,
                                     headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read())
            out = json.loads(data["choices"][0]["message"]["content"])
            out["usage"] = data["usage"]
            return out
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504):
                raise RuntimeError(e.read().decode()[:300])
            time.sleep(2 ** attempt)
    raise RuntimeError("falhou após 6 tentativas")


if __name__ == "__main__":
    if "--smoke" in sys.argv:
        print(classify(sample.document.iloc[0]), "| real:", sample.topic_group.iloc[0])
        sys.exit()
    t0 = time.time()
    with ThreadPoolExecutor(8) as ex:
        answers = list(ex.map(classify, sample.document.tolist()))
    secs = time.time() - t0
    pred = np.array([a["category"] for a in answers])
    conf = np.array([float(a["confidence"]) for a in answers])
    y = sample.topic_group.values
    usage = {k: sum(a["usage"].get(k, 0) for a in answers) for k in ("prompt_tokens", "completion_tokens")}

    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
    lr = LogisticRegression(max_iter=2000, C=5).fit(vec.fit_transform(train.document), train.topic_group)
    base = lr.predict(vec.transform(sample.document))

    res = {"model": MODEL, "n": len(sample), "per_class": N, "seconds": round(secs, 1), "usage": usage,
           "zero_shot": {"accuracy": round(accuracy_score(y, pred), 4), "f1_macro": round(f1_score(y, pred, average="macro"), 4),
                         "f1_per_class": dict(zip(classes, np.round(f1_score(y, pred, labels=classes, average=None), 4).tolist())),
                         "precision_at_conf_0_9": round(float((pred[conf >= .9] == y[conf >= .9]).mean()), 4) if (conf >= .9).any() else None,
                         "coverage_at_conf_0_9": round(float((conf >= .9).mean()), 4)},
           "tfidf_lr_same_sample": {"accuracy": round(accuracy_score(y, base), 4), "f1_macro": round(f1_score(y, base, average="macro"), 4)},
           "answers": [{"id": int(i), "true": t, "pred": a["category"], "confidence": a["confidence"]}
                       for i, t, a in zip(sample.id, y, answers)]}
    (ROOT / "solution/analysis/output/zero_shot_eval.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    z, b = res["zero_shot"], res["tfidf_lr_same_sample"]
    print(f"{MODEL} zero-shot (n={len(sample)}): acurácia {z['accuracy']:.3f} | F1 macro {z['f1_macro']:.3f} | {secs:.0f}s | tokens {usage}")
    print("  F1/classe:", " ".join(f"{c[:8]}={v:.2f}" for c, v in z["f1_per_class"].items()))
    print(f"  confiança ≥0,9 declarada pelo LLM: cobertura {z['coverage_at_conf_0_9']:.0%} → precisão {z['precision_at_conf_0_9']}")
    print(f"TF-IDF + LR na MESMA amostra: acurácia {b['accuracy']:.3f} | F1 macro {b['f1_macro']:.3f}")
