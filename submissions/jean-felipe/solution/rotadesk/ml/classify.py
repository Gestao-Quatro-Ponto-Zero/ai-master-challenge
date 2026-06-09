"""Classificação via stdin JSON -> stdout JSON."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib

MODEL_PATH = Path(__file__).resolve().parent / "pipeline.joblib"


def main() -> None:
    raw = sys.stdin.read()
    payload = json.loads(raw)
    text = payload.get("text", "")
    if not text.strip():
        print(json.dumps({"error": "texto vazio"}))
        sys.exit(1)
    if not MODEL_PATH.exists():
        print(json.dumps({"error": "modelo nao encontrado. Rode: python ml/train_export.py"}))
        sys.exit(1)

    pipe = joblib.load(MODEL_PATH)
    proba = pipe.predict_proba([text])[0]
    classes = list(pipe.classes_)
    idx = int(proba.argmax())
    result = {
        "topic_group": classes[idx],
        "confidence": round(float(proba[idx]) * 100, 2),
        "probabilities": {
            classes[i]: round(float(proba[i]) * 100, 2) for i in range(len(classes))
        },
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
