"""Roteador: o mesmo TF-IDF + regressão logística validado em 03_ds2_core.py (86,1% no teste por grupo)."""
import re
from dataclasses import dataclass

import joblib
import numpy as np

from . import config

SENSIVEIS = ("HR Support", "Administrative rights")


@dataclass
class Rota:
    fila: str
    conf: float
    limiar: float
    top3: list[tuple[str, float]]
    p_sens: float          # probabilidade somada das filas sensíveis


class Router:
    def __init__(self, path=config.MODEL_PATH):
        if not path.exists():
            raise FileNotFoundError(f"{path} não existe. Gere com: python solution/analysis/03_ds2_core.py "
                                    "<all_tickets_processed_improved_v3.csv> solution/outputs")
        m = joblib.load(path)
        self.vec, self.clf = m["vectorizer"], m["clf"]
        self.limiar = {q: v["thr"] for q, v in m["per_queue_threshold_95"].items()}
        self.classes = list(self.clf.classes_)

    def prever(self, texto_ingles: str) -> Rota:
        # o Dataset 2 está em minúsculas, sem números nem pontuação: normaliza igual
        t = re.sub(r"[^a-z ]+", " ", texto_ingles.lower())
        p = self.clf.predict_proba(self.vec.transform([t]))[0]
        ordem = np.argsort(-p)
        fila = self.classes[ordem[0]]
        return Rota(fila=fila, conf=float(p[ordem[0]]), limiar=self.limiar[fila],
                    top3=[(self.classes[i], float(p[i])) for i in ordem[:3]],
                    p_sens=float(sum(p[self.classes.index(q)] for q in SENSIVEIS)))
