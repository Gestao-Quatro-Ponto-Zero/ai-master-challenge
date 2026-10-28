"""Etapa 4 — Desenho do score: qual combinação coloca mais receita na lista do vendedor?

Depois do 03_backtest mostrar que P(ganhar) é praticamente imprevisível, a
pergunta mudou de "esse deal vai fechar?" para "o que fecha NOS PRÓXIMOS 30
DIAS e vale a pena?". Aqui comparo rankings em 8 segundas-feiras simuladas
(a cada 4 semanas), sempre usando só dados conhecidos até aquela data.

Métricas:
  cap_top20pct            % da receita ganha nos 30 dias seguintes que estava no top 20% do pipeline
  cap_top10_por_vendedor  idem, mas olhando o top 10 de CADA vendedor (uso real da ferramenta)
  hit_rate_top10          % dos deals do top 10 que de fato viraram Won nos 30 dias

Rodado com: python3 04_score_design.py > 04_score_design.out.txt
"""
from pathlib import Path

import numpy as np
import pandas as pd

pd.set_option("display.width", 250)
DATA = Path(__file__).resolve().parents[2] / "solution" / "data"

p = pd.read_csv(DATA / "sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
p["product"] = p["product"].replace({"GTXPro": "GTX Pro"})
p = p.merge(pd.read_csv(DATA / "products.csv"), on="product")
c = p[p.deal_stage.isin(["Won", "Lost"])].copy()
c["won"] = (c.deal_stage == "Won").astype(int)
c["days"] = (c.close_date - c.engage_date).dt.days

out = []
for S in pd.date_range("2017-04-03", "2017-11-27", freq="4W-MON"):
    h = c[c.close_date < S]
    te = c[(c.engage_date <= S) & (c.close_date >= S)].copy()
    te["age"] = (S - te.engage_date).dt.days
    te["rev30"] = np.where((te.won == 1) & (te.close_date < S + pd.Timedelta(days=30)), te.close_value, 0)

    def ripeness(x):  # P(fechar GANHO nos próximos 30 dias | ainda aberto com idade x)
        s = h[h.days > x]
        return ((s.won == 1) & (s.days <= x + 30)).mean() if len(s) >= 30 else np.nan

    def survival(x):  # P(ganhar algum dia | ainda aberto com idade x)
        s = h[h.days > x]
        return s.won.mean() if len(s) >= 30 else np.nan

    te["rip"] = te.age.map(ripeness).fillna(0.02)
    te["pw"] = te.age.map(survival).fillna(h.won.mean())
    lv = np.log(te.sales_price / 55) / np.log(26768 / 55)
    rankings = {
        "aleatório": np.random.default_rng(1).random(len(te)),
        "só valor de lista": te.sales_price,
        "P(win) x valor": te.pw * te.sales_price,
        "ripeness x valor (EV 30d)": te.rip * te.sales_price,
        "60 pts log-valor + 40 pts ripeness": 60 * lv + 40 * te.rip / te.rip.max(),
        "50 pts log-valor + 50 pts ripeness": 50 * lv + 50 * te.rip / te.rip.max(),
    }
    tot = te.rev30.sum()
    for k, s in rankings.items():
        te["s"] = np.asarray(s)
        top10 = te.sort_values("s", ascending=False).groupby("sales_agent").head(10)
        top20 = te.nlargest(int(len(te) * 0.2), "s")
        out.append((S.date(), k, top20.rev30.sum() / tot, top10.rev30.sum() / tot, (top10.rev30 > 0).mean()))

r = pd.DataFrame(out, columns=["S", "ranking", "cap_top20pct", "cap_top10_por_vendedor", "hit_rate_top10"])
print("Média em", r.S.nunique(), "segundas-feiras simuladas:\n")
print(r.groupby("ranking")[["cap_top20pct", "cap_top10_por_vendedor", "hit_rate_top10"]].mean()
      .sort_values("cap_top10_por_vendedor", ascending=False).round(3).to_string())
print("\nPor snapshot (cap_top10_por_vendedor):")
print(r.pivot(index="ranking", columns="S", values="cap_top10_por_vendedor").round(2).to_string())
