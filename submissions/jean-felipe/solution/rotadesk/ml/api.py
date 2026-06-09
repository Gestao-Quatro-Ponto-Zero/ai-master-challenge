"""API HTTP do classificador sklearn — deploy no Render."""
from __future__ import annotations

import json
import os
from pathlib import Path

import joblib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

MODEL_PATH = Path(__file__).resolve().parent / "pipeline.joblib"

app = FastAPI(title="RotaDesk Classifier", version="1.0.0")

origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_pipe = None


def get_pipeline():
    global _pipe
    if _pipe is None:
        if not MODEL_PATH.exists():
            raise HTTPException(
                status_code=503,
                detail="pipeline.joblib ausente. Rode train_export.py no build ou inclua o modelo.",
            )
        _pipe = joblib.load(MODEL_PATH)
    return _pipe


class ClassifyRequest(BaseModel):
    text: str = Field(..., min_length=1)


class ClassifyResponse(BaseModel):
    topic_group: str
    confidence: float
    probabilities: dict[str, float]


@app.get("/")
def root():
    return {
        "service": "rotadesk-classifier",
        "endpoints": ["/health", "POST /classify"],
        "model_loaded": MODEL_PATH.exists(),
    }


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": MODEL_PATH.exists()}


@app.post("/classify", response_model=ClassifyResponse)
def classify(body: ClassifyRequest):
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="texto vazio")

    pipe = get_pipeline()
    proba = pipe.predict_proba([text])[0]
    classes = list(pipe.classes_)
    idx = int(proba.argmax())

    return ClassifyResponse(
        topic_group=classes[idx],
        confidence=round(float(proba[idx]) * 100, 2),
        probabilities={
            classes[i]: round(float(proba[i]) * 100, 2) for i in range(len(classes))
        },
    )


# compatível com stdin/stdout local (classify.py)
if __name__ == "__main__":
    import sys

    raw = sys.stdin.read()
    payload = json.loads(raw)
    result = classify(ClassifyRequest(text=payload.get("text", "")))
    print(result.model_dump_json(ensure_ascii=False))
