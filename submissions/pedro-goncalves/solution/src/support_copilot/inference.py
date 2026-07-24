from __future__ import annotations

import hashlib
from pathlib import Path

import joblib
import numpy as np


class TicketClassifier:
    def __init__(self, model_path: str | Path):
        self.model_path = Path(model_path)
        self.model_sha256 = hashlib.sha256(self.model_path.read_bytes()).hexdigest()
        self.pipeline = joblib.load(self.model_path)
        self.classes = self.pipeline.named_steps["classifier"].classes_

    def predict(self, text: str) -> dict:
        probabilities = self.pipeline.predict_proba([text])[0]
        order = np.argsort(probabilities)[::-1]
        top = [
            {"category": str(self.classes[index]), "probability": float(probabilities[index])}
            for index in order[:3]
        ]
        return {
            "category": top[0]["category"],
            "confidence": top[0]["probability"],
            "top_predictions": top,
        }
