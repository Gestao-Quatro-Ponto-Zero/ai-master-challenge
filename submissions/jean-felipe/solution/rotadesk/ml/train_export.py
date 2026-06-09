"""
Treina e exporta o classificador DS2 para o RotaDesk.
Gera ml/pipeline.joblib a partir do dataset local.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SCRIPT_DIR.parents[5]  # g4-challenge/
DEFAULT_DATASET = (
    WORKSPACE_ROOT
    / "data/dataset2-it-classification/all_tickets_processed_improved_v3.csv"
)
OUTPUT = SCRIPT_DIR / "pipeline.joblib"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    args = parser.parse_args()

    if not args.dataset.exists():
        raise FileNotFoundError(f"Dataset nao encontrado: {args.dataset}")

    df = pd.read_csv(args.dataset)
    X = df["Document"].astype(str)
    y = df["Topic_group"]

    pipe = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    max_features=50_000,
                    ngram_range=(1, 2),
                    min_df=2,
                    sublinear_tf=True,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=1_000,
                    C=1.0,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )
    pipe.fit(X, y)
    joblib.dump(pipe, OUTPUT)
    print(f"Modelo salvo em {OUTPUT} ({len(df):,} amostras)")


if __name__ == "__main__":
    main()
