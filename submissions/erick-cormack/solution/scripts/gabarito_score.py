"""Reimplementa em Pandas a lógica de sql/02_score.sql para conferir o banco.

Uso: python scripts/gabarito_score.py   (lê data_limpa/, gerado por preparar_dados.py)
"""
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
D = RAIZ / "data_limpa"
DATA_REF, CICLO_MAX, FASE_RISCO, RETA_FINAL, AMOSTRA_MIN = pd.Timestamp("2017-12-31"), 138, 14, 104, 100

pipe = pd.read_csv(D / "sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
prod = pd.read_csv(D / "products.csv")
team = pd.read_csv(D / "sales_teams.csv")
df = pipe.merge(team, on="sales_agent").merge(prod, on="product")

fech = df[df.deal_stage.isin(["Won", "Lost"])].copy()
fech["ciclo"] = (fech.close_date - fech.engage_date).dt.days
fech["ganho"] = (fech.deal_stage == "Won").astype(int)
curva = pd.DataFrame({"idade": range(CICLO_MAX + 1)})
curva["n"] = [(fech.ciclo > a).sum() for a in curva.idade]
curva["p"] = [round(fech.loc[fech.ciclo > a, "ganho"].mean(), 4) if (fech.ciclo > a).any() else np.nan for a in curva.idade]
idade_conf = curva.loc[curva.n >= AMOSTRA_MIN, "idade"].max()
taxa_base = round(fech.ganho.mean(), 4)

df["idade_dias"] = (DATA_REF - df.engage_date).dt.days
df["fila"] = np.select(
    [df.deal_stage.isin(["Won", "Lost"]), df.deal_stage == "Prospecting", df.idade_dias > CICLO_MAX],
    ["fechado", "prospectar", "requalificar"], default="focar")
mapa = curva.set_index("idade").p
df["p_ganho"] = np.where(df.fila == "focar", df.idade_dias.clip(upper=idade_conf).map(mapa),
                         np.where(df.fila == "prospectar", taxa_base, np.nan))
df["valor_esperado"] = (df.p_ganho * df.sales_price).round(2)
ln = np.log(df.valor_esperado)
g = ln.groupby(df.fila)
df["score"] = (100 * (ln - g.transform("min")) / (g.transform("max") - g.transform("min"))).round()

print(f"idade confiável máx: {idade_conf} | taxa base: {taxa_base}")
print(df.groupby("fila").agg(deals=("opportunity_id", "count"), valor_lista=("sales_price", "sum"),
                             valor_esperado=("valor_esperado", "sum"), score_medio=("score", "mean")).round(2))
foc = df[df.fila == "focar"]
momento = np.select([foc.idade_dias <= FASE_RISCO, foc.idade_dias >= RETA_FINAL], ["fase de risco", "reta final"], "em andamento")
print("\nmomento (focar):", pd.Series(momento).value_counts().to_dict())
print("\ntop 5 focar:")
print(foc.sort_values(["score", "valor_esperado"], ascending=False)
         .head(5)[["opportunity_id", "sales_agent", "product", "idade_dias", "p_ganho", "valor_esperado", "score"]])
print("\ncurva nos pontos 0, 14, 60, 104, 120, idade_conf:",
      curva.set_index("idade").loc[[0, 14, 60, 104, 120, idade_conf], ["n", "p"]].to_dict("index"))
