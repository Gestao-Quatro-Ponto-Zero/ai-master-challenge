"""
Sinais que SOBREVIVEM ao teste fora da amostra (o 04_backtest mostrou que p(win) não diferencia deals).

1. Regra do zumbi: algum deal aberto há mais que o ciclo máximo histórico fechou depois?
2. Momento: p(decisão nos próximos 30 dias | deal aberto com idade a), validado em snapshots.
3. Efeito fim de trimestre: diferença de win rate por mês de fechamento.
Uso:  python 05_timing_and_zombies.py
"""
import numpy as np
import pandas as pd

D = "../data/"
p = pd.read_csv(D + "sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
closed = p[p.deal_stage.isin(["Won", "Lost"])].copy()
closed["won"] = (closed.deal_stage == "Won").astype(int)
closed["days"] = (closed.close_date - closed.engage_date).dt.days
END = p.close_date.max()

print("== 1. Zumbis ==")
for S in pd.to_datetime(["2017-05-01", "2017-07-01", "2017-09-01"]):
    train_max = closed[closed.close_date < S].days.max()
    opened = p[(p.engage_date < S) & ((p.close_date >= S) | p.close_date.isna())].copy()
    opened["age"] = (S - opened.engage_date).dt.days
    z = opened[opened.age > train_max]
    print(f"{S.date()}: ciclo máx conhecido={train_max}d | zumbis={len(z)} | fecharam depois={z.close_date.notna().sum()}")

print("\n== 2. Momento: p(decisão em 30d | idade) ==")
def decide_curve(train, horizon=30):
    out = {}
    for x in range(0, int(train.days.max()) + 1):
        alive = train[train.days > x]
        out[x] = (alive.days <= x + horizon).mean() if len(alive) >= 30 else np.nan
    return pd.Series(out).ffill()

def auc(y, s):
    r = pd.Series(s).rank().values
    n1 = y.sum(); n0 = len(y) - n1
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)

for S in pd.to_datetime(["2017-05-01", "2017-07-01", "2017-09-01"]):
    train = closed[closed.close_date < S]
    curve = decide_curve(train)
    t = closed[(closed.engage_date < S) & (closed.close_date >= S)].copy()
    t["age"] = (S - t.engage_date).dt.days
    t = t[t.age <= train.days.max()]
    t["pred"] = t.age.clip(upper=curve.index.max()).map(curve)
    t["decided30"] = (t.close_date < S + pd.Timedelta(days=30)).astype(int)
    print(f"{S.date()}: n={len(t)} AUC={auc(t.decided30.values, t.pred.values):.3f} "
          f"prev média={t.pred.mean():.2f} real={t.decided30.mean():.2f}")

curve = decide_curve(closed)
print("curva completa (idade -> p decisão 30d):", {k: round(v, 2) for k, v in curve.iloc[::15].items()})

print("\n== 3. Fim de trimestre ==")
closed["qe"] = closed.close_date.dt.month.isin([3, 6, 9, 12])
print(closed.groupby("qe").won.agg(["mean", "count"]))
closed["dom"] = closed.close_date.dt.day
print("win rate por dia do mês (meses de fim de tri):")
print(closed[closed.qe].groupby(pd.cut(closed[closed.qe].dom, [0, 10, 20, 31])).won.mean())
