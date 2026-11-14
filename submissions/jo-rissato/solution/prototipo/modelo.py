"""Treina e carrega o classificador do protótipo.

Mesmo modelo e mesma separação do relatório (docs/relatorio-classificador.md): regressão
logística com peso por categoria sobre TF-IDF de 1 e 2 palavras, treinada só nos 80% de treino.
Uso: python modelo.py  (gera saida/classificador.joblib)
"""
from __future__ import annotations

import re

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

from config import DATASET2, FRACAO_TESTE, MODELO, SEMENTE


def preparar(texto: str) -> str:
    """Deixa o texto no formato do Dataset 2: minúsculas, só letras e espaços."""
    t = re.sub(r"[^a-z ]", " ", texto.lower())
    return re.sub(r"\s+", " ", t).strip()


def separar() -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    d = pd.read_csv(DATASET2)
    return train_test_split(d["Document"], d["Topic_group"], test_size=FRACAO_TESTE,
                            stratify=d["Topic_group"], random_state=SEMENTE)


def treinar() -> None:
    xtr, _, ytr, _ = separar()
    modelo = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True),
                           LogisticRegression(max_iter=2000, C=10, class_weight="balanced"))
    modelo.fit(xtr, ytr)
    MODELO.parent.mkdir(exist_ok=True)
    joblib.dump(modelo, MODELO)
    print(f"modelo salvo em {MODELO} ({len(xtr)} textos de treino)")


def carregar():
    if not MODELO.exists():
        treinar()
    return joblib.load(MODELO)


def classificar(modelo, texto: str) -> tuple[str, float, list[tuple[str, float]]]:
    """Devolve categoria, confiança e as 3 categorias mais prováveis."""
    p = modelo.predict_proba([preparar(texto)])[0]
    ordem = np.argsort(-p)
    top = [(modelo.classes_[i], float(p[i])) for i in ordem[:3]]
    return top[0][0], top[0][1], top


if __name__ == "__main__":
    treinar()
