"""Etapa 3 — Backtest: qual score realmente ajudaria o vendedor?

Simula "segundas-feiras" passadas: em cada data S, pega os deals que estavam
em Engaging naquele dia (engage <= S < close), calcula as features SÓ com o que
se sabia em S, e mede contra o resultado real que aconteceu depois.

Duas métricas:
  - AUC da probabilidade de ganho (separa Won de Lost?)
  - Captura de receita: % da receita efetivamente ganha que estava no top 20%
    da lista ranqueada (é o que importa pro vendedor com tempo limitado)

Rodado com: python3 03_backtest.py > 03_backtest.out.txt
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

DATA = Path(__file__).resolve().parents[2] / "solution" / "data"

p = pd.read_csv(DATA / "sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
p["product"] = p["product"].replace({"GTXPro": "GTX Pro"})
a = pd.read_csv(DATA / "accounts.csv")
t = pd.read_csv(DATA / "sales_teams.csv")
pr = pd.read_csv(DATA / "products.csv")
d = p.merge(t, on="sales_agent", how="left").merge(pr, on="product", how="left").merge(a, on="account", how="left")
closed = d[d.deal_stage.isin(["Won", "Lost"])].copy()
closed["won"] = (closed.deal_stage == "Won").astype(int)
closed["days"] = (closed.close_date - closed.engage_date).dt.days


def survival_wr(hist, ages):
    """P(win | deal ainda aberto com idade x) = win rate dos deals históricos com duração > x."""
    out = []
    for x in ages:
        s = hist[hist.days > x]
        out.append(s.won.mean() if len(s) >= 30 else np.nan)
    return np.array(out)


def shrunk_rate(hist, key, k=50):
    """Win rate por grupo com shrinkage bayesiano pro base rate (k = força do prior)."""
    base = hist.won.mean()
    g = hist.groupby(key).won.agg(["sum", "count"])
    return ((g["sum"] + k * base) / (g["count"] + k)).to_dict(), base


rows = []
capture = []
for S in pd.to_datetime(["2017-05-01", "2017-06-01", "2017-07-01", "2017-08-01", "2017-09-01", "2017-10-01"]):
    hist = closed[closed.close_date < S]
    test = closed[(closed.engage_date <= S) & (closed.close_date >= S)].copy()
    test["age"] = (S - test.engage_date).dt.days
    if len(hist) < 300 or len(test) < 100:
        continue

    # carga do vendedor em S
    open_at_S = d[(d.engage_date <= S) & ((d.close_date.isna()) | (d.close_date >= S))]
    load = open_at_S.groupby("sales_agent").size()
    test["load"] = test.sales_agent.map(load).fillna(0)

    preds = {}
    preds["base rate (constante)"] = np.full(len(test), hist.won.mean())
    sv = survival_wr(hist, test.age.values)
    sv = np.where(np.isnan(sv), hist.won.mean(), sv)
    preds["idade (sobrevivência)"] = sv

    # 'Tudo que parece óbvio': vendedor + produto + setor + conta (shrunk), combinados em log-odds
    lo = lambda x: np.log(x / (1 - x))
    base = hist.won.mean()
    score = np.full(len(test), lo(base))
    for key in ["sales_agent", "product", "sector", "account", "regional_office"]:
        rates, _ = shrunk_rate(hist, key)
        r = test[key].map(rates).fillna(base).values
        score += lo(r) - lo(base)
    preds["vendedor+produto+setor+conta"] = 1 / (1 + np.exp(-score))
    preds["idade + vendedor+produto+..."] = 1 / (1 + np.exp(-(score + lo(sv) - lo(base))))

    # GBM com tudo (o que um 'jogue no XGBoost' faria) — treino em snapshots anteriores
    feat = ["age", "sales_price", "revenue", "employees", "load"]
    cat = ["sales_agent", "product", "sector", "regional_office"]
    train_frames = []
    for S2 in pd.date_range("2017-03-01", S - pd.Timedelta(days=1), freq="7D"):
        tr = closed[(closed.engage_date <= S2) & (closed.close_date >= S2) & (closed.close_date < S)].copy()
        tr["age"] = (S2 - tr.engage_date).dt.days
        o2 = d[(d.engage_date <= S2) & ((d.close_date.isna()) | (d.close_date >= S2))]
        tr["load"] = tr.sales_agent.map(o2.groupby("sales_agent").size()).fillna(0)
        train_frames.append(tr)
    tr = pd.concat(train_frames)
    X = lambda df: pd.concat([df[feat], pd.get_dummies(df[cat].astype("category"))], axis=1)
    Xtr = X(tr)
    Xte = X(test).reindex(columns=Xtr.columns, fill_value=0)
    gbm = HistGradientBoostingClassifier(max_depth=3, max_iter=150, learning_rate=0.05, random_state=0)
    gbm.fit(Xtr, tr.won)
    preds["GBM com todas as features"] = gbm.predict_proba(Xte)[:, 1]

    for name, pw in preds.items():
        rows.append((S.date(), name, len(test), roc_auc_score(test.won, pw)))

    # captura de receita no top 20% da lista
    test["won_value"] = test.close_value * test.won
    total = test.won_value.sum()
    n = int(len(test) * 0.2)
    rankings = {
        "ordem aleatória": np.random.default_rng(0).random(len(test)),
        "só valor de lista": test.sales_price.values,
        "só P(win) [idade]": preds["idade (sobrevivência)"],
        "valor esperado = P(win) x valor": preds["idade (sobrevivência)"] * test.sales_price.values,
        "valor esperado GBM": preds["GBM com todas as features"] * test.sales_price.values,
    }
    for name, s in rankings.items():
        top = test.iloc[np.argsort(-s)[:n]]
        capture.append((S.date(), name, top.won_value.sum() / total, top.won.mean()))

r = pd.DataFrame(rows, columns=["snapshot", "modelo", "n_deals", "auc"])
print("=== AUC por snapshot (0.5 = chute) ===")
print(r.pivot(index="modelo", columns="snapshot", values="auc").round(3).to_string())
print("\nAUC média:")
print(r.groupby("modelo").auc.mean().sort_values(ascending=False).round(3).to_string())

cp = pd.DataFrame(capture, columns=["snapshot", "ranking", "receita_capturada_top20", "win_rate_top20"])
print("\n=== Top 20% da lista: quanto da receita ganha depois estava ali? ===")
print(cp.groupby("ranking")[["receita_capturada_top20", "win_rate_top20"]].mean().sort_values(
    "receita_capturada_top20", ascending=False).round(3).to_string())
