"""
train.py — Treina o modelo de scoring de pipeline Pulse Revenue Intelligence

Features:
  1. wr_agent_product : Win Rate histórico do agente x produto  (feature principal)
  2. wr_agent_recent  : Win Rate dos últimos 20 deals fechados  (momento do agente)
  3. wr_agent_sector  : Win Rate histórico do agente x setor    (feature terciária)

Saída: api/model_coefficients.json com coeficientes + lookup tables de WR.
"""

import io
import json
import os
import sys

# Windows: força stdout UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "model_coefficients.json")

MIN_DEALS_FOR_SCORE = 10  # combo com < 10 deals → alerta máximo


# ---------------------------------------------------------------------------
# 1. Carregamento
# ---------------------------------------------------------------------------

def load_data():
    pipeline = pd.read_csv(f"{DATA_DIR}/sales_pipeline.csv")
    accounts = pd.read_csv(f"{DATA_DIR}/accounts.csv")
    products = pd.read_csv(f"{DATA_DIR}/products.csv")
    teams = pd.read_csv(f"{DATA_DIR}/sales_teams.csv")

    # CORREÇÃO OBRIGATÓRIA
    pipeline["product"] = pipeline["product"].str.replace("GTXPro", "GTX Pro", regex=False)

    # Join: sector via accounts
    pipeline = pipeline.merge(accounts[["account", "sector"]], on="account", how="left")

    # Join: manager via teams
    pipeline = pipeline.merge(teams[["sales_agent", "manager", "regional_office"]],
                               on="sales_agent", how="left")

    return pipeline, accounts, products, teams


# ---------------------------------------------------------------------------
# 2. Cálculo das WR lookup tables (calculadas sobre TODOS os closed deals)
# ---------------------------------------------------------------------------

def compute_wr_tables(closed: pd.DataFrame):
    """
    Retorna três DataFrames com Win Rate agregado por grupo.
    Usados tanto no treino (features por deal) quanto no scorer (inference).
    """
    # Feature 1 — agente x produto
    ap = (
        closed.groupby(["sales_agent", "product"])
        .agg(wr_agent_product=("won", "mean"), n_agent_product=("won", "count"))
        .reset_index()
    )

    # Feature 2 — momento: WR dos últimos 20 deals de cada agente
    closed_sorted = closed.sort_values("close_date")
    recent = (
        closed_sorted.groupby("sales_agent")["won"]
        .apply(lambda x: x.tail(20).mean())
        .reset_index()
        .rename(columns={"won": "wr_agent_recent"})
    )

    # Feature 3 — agente x setor
    as_ = (
        closed.groupby(["sales_agent", "sector"])
        .agg(wr_agent_sector=("won", "mean"), n_agent_sector=("won", "count"))
        .reset_index()
    )

    return ap, recent, as_


def build_feature_matrix(df: pd.DataFrame, ap: pd.DataFrame,
                          recent: pd.DataFrame, as_: pd.DataFrame) -> pd.DataFrame:
    """Junta WR stats a qualquer DataFrame de deals."""
    df = df.merge(ap, on=["sales_agent", "product"], how="left")
    df = df.merge(recent, on="sales_agent", how="left")
    df = df.merge(as_, on=["sales_agent", "sector"], how="left")

    # Fallback para wr_agent_sector ausente: média do agente em todos os produtos
    agent_mean_wr = df.groupby("sales_agent")["wr_agent_product"].transform("mean")
    df["wr_agent_sector"] = df["wr_agent_sector"].fillna(agent_mean_wr)

    return df


# ---------------------------------------------------------------------------
# 3. Treino
# ---------------------------------------------------------------------------

FEATURES = ["wr_agent_product", "wr_agent_recent", "wr_agent_sector"]
TARGET = "won"


def train():
    print("=" * 60)
    print("  Pulse Revenue Intelligence — Model Training")
    print("=" * 60)

    pipeline, accounts, products, teams = load_data()

    # Deals históricos
    closed = pipeline[pipeline["deal_stage"].isin(["Won", "Lost"])].copy()
    closed["won"] = (closed["deal_stage"] == "Won").astype(int)

    print(f"\nDataset: {len(closed)} deals históricos  "
          f"(Won={closed['won'].sum()}  Lost={(closed['won']==0).sum()})")

    # Lookup tables
    ap, recent, as_ = compute_wr_tables(closed)

    # Feature matrix (note: os closed deals servem como treino e as WRs
    # são calculadas sobre o dataset completo — aceitável para scores agregados)
    df = build_feature_matrix(closed.copy(), ap, recent, as_)

    df_model = df[FEATURES + [TARGET]].dropna()
    print(f"Rows com todas as features: {len(df_model)} / {len(closed)}")

    X = df_model[FEATURES].values
    y = df_model[TARGET].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    model = LogisticRegression(random_state=42, max_iter=500)
    model.fit(X_train_s, y_train)

    # Métricas
    y_pred = model.predict(X_test_s)
    y_prob = model.predict_proba(X_test_s)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_prob)

    print(f"\n{'-'*40}")
    print(f"  Accuracy : {acc:.4f}")
    print(f"  AUC-ROC  : {auc:.4f}")
    print(f"{'-'*40}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Lost", "Won"]))

    # Coeficientes (em escala padronizada)
    print("Coeficientes LogReg (impacto relativo):")
    for feat, coef in zip(FEATURES, model.coef_[0]):
        print(f"  {feat:30s}: {coef:+.4f}")
    print(f"  {'intercept':30s}: {model.intercept_[0]:+.4f}")

    # ---------------------------------------------------------------------------
    # 4. Serialização
    # ---------------------------------------------------------------------------

    # Cobertura: quantos combos agente x produto têm >= MIN_DEALS_FOR_SCORE
    scoreable = ap[ap["n_agent_product"] >= MIN_DEALS_FOR_SCORE]
    print(f"\nCombos agente×produto com >= {MIN_DEALS_FOR_SCORE} deals: "
          f"{len(scoreable)} / {len(ap)}")

    payload = {
        "intercept": float(model.intercept_[0]),
        "coefficients": {
            feat: float(coef)
            for feat, coef in zip(FEATURES, model.coef_[0])
        },
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_std": scaler.scale_.tolist(),
        "features": FEATURES,
        "min_deals_for_score": MIN_DEALS_FOR_SCORE,
        # Lookup tables (convertidas para JSON-serializable)
        "ap_stats": ap.to_dict(orient="records"),
        "recent_stats": recent.to_dict(orient="records"),
        "sector_stats": as_.to_dict(orient="records"),
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)

    print(f"\nModelo exportado → {OUTPUT_PATH}")
    print("=" * 60)

    return payload


if __name__ == "__main__":
    train()
