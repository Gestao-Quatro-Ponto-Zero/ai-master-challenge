"""Pacote de artefatos de uma versão do modelo + pontuação (somente inferência; nunca treina)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from .bands import assign_band, score_from_ev
from .calibration import apply_calibration
from .constants import LOW_CONFIDENCE_AGENT_N
from .reasons import build_reasons

MODEL_FILE = "model.txt"
FEATURES_FILE = "features.json"
CALIBRATION_FILE = "calibration.json"
TABLES_FILE = "history_tables.json"
REFERENCE_FILE = "score_reference.json"
CARD_FILE = "model_card.json"
SCORED_FILE = "scored_deals.parquet"


def _dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass
class ModelBundle:
    version: str
    booster: lgb.Booster
    num: list[str]
    cat: list[str]
    cats: dict[str, list[str]]
    calibration: dict
    tables: dict
    ref_ev: np.ndarray        # valores esperados (ordenados) dos deals não-zumbis, base do percentil
    card: dict

    @property
    def thresholds(self) -> dict:
        return self.card["thresholds"]

    # ------------------------------------------------------------------ persistência
    def save(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        self.booster.save_model(str(directory / MODEL_FILE))
        _dump(directory / FEATURES_FILE, {"num": self.num, "cat": self.cat, "cats": self.cats})
        _dump(directory / CALIBRATION_FILE, self.calibration)
        _dump(directory / TABLES_FILE, self.tables)
        _dump(directory / REFERENCE_FILE, {"ev_sorted": [float(x) for x in self.ref_ev]})
        _dump(directory / CARD_FILE, self.card)

    @classmethod
    def load(cls, directory: Path) -> "ModelBundle":
        feats = _read(directory / FEATURES_FILE)
        card = _read(directory / CARD_FILE)
        return cls(
            version=card["version"],
            booster=lgb.Booster(model_file=str(directory / MODEL_FILE)),
            num=feats["num"], cat=feats["cat"], cats=feats["cats"],
            calibration=_read(directory / CALIBRATION_FILE),
            tables=_read(directory / TABLES_FILE),
            ref_ev=np.asarray(_read(directory / REFERENCE_FILE)["ev_sorted"], dtype=float),
            card=card,
        )

    # ------------------------------------------------------------------ inferência
    def design_matrix(self, feats: pd.DataFrame) -> pd.DataFrame:
        X = feats[self.num + self.cat].copy()
        for col in self.cat:
            X[col] = pd.Categorical(X[col], categories=self.cats[col])
        return X

    def predict_raw(self, feats: pd.DataFrame) -> np.ndarray:
        return np.asarray(self.booster.predict(self.design_matrix(feats)), dtype=float)

    def contributions(self, feats: pd.DataFrame) -> np.ndarray:
        """Contribuição de cada feature em log-odds (última coluna do LightGBM é o viés e é descartada)."""
        return np.asarray(self.booster.predict(self.design_matrix(feats), pred_contrib=True))[:, :-1]

    def score(self, feats: pd.DataFrame, stage: str = "Engaging") -> pd.DataFrame:
        """Pontua deals Engaging. Devolve p_win, valor esperado, score, faixa, confiança e motivos."""
        names = self.num + self.cat
        p_raw = self.predict_raw(feats)
        p_win = apply_calibration(p_raw, self.calibration)
        ev = p_win * feats["price"].to_numpy(dtype=float)
        score = score_from_ev(ev, self.ref_ev)
        contrib = self.contributions(feats)

        rows = []
        for i, (_, f) in enumerate(feats.iterrows()):
            age = float(f["age_days"])
            band = assign_band(stage, age, int(score[i]), self.thresholds)
            reasons = build_reasons(names, [f[n] for n in names], contrib[i])
            rows.append({
                "p_win_raw": float(p_raw[i]), "p_win": float(p_win[i]), "expected_value": float(ev[i]),
                "score": None if band == "review" else int(score[i]),
                "band": band,
                "confidence": "low" if float(f["agent_n"]) < LOW_CONFIDENCE_AGENT_N else "medium",
                "reasons": reasons,
            })
        return pd.DataFrame(rows, index=feats.index)
