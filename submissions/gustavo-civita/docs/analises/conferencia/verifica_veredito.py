"""Confere os números centrais do advogado do diabo e do relatório de alternativas."""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3] / "solution"))
import backtest  # noqa: E402
import scoring  # noqa: E402

deals = scoring.load_pipeline()
REF = scoring.reference_date(deals)


def auc(score, label):
    """Probabilidade de um positivo ter score maior que um negativo."""
    order = pd.Series(score).rank().to_numpy()
    label = np.asarray(label, dtype=bool)
    pos, neg = label.sum(), (~label).sum()
    return (order[label].sum() - pos * (pos + 1) / 2) / (pos * neg)


# 1. A chance separa ganho de perda, ou só "fecha" de "fica aberta"?
snaps = pd.concat(
    backtest.snapshot_with_predictions(deals, pd.Timestamp(d)).assign(semana=d) for d in backtest.SNAPSHOTS
)
closed = snaps[snaps["won_after"] | snaps["lost_after"]]
print("1. AUC ganho x perda (entre as que fecharam):", round(auc(closed["chance"], closed["won_after"]), 3))
print("   AUC fecha x fica aberta:", round(auc(snaps["chance"], snaps["won_after"] | snaps["lost_after"]), 3))
high = snaps[snaps["chance"] >= scoring.BAND_HIGH]
print("   faixa alta: ganhas", round(high["won_after"].mean(), 3), "perdidas", round(high["lost_after"].mean(), 3),
      "seguiram abertas", round(1 - high["won_after"].mean() - high["lost_after"].mean(), 3))

# 2. As negociações tiradas da lista: alguém fechou?
parked = snaps[snaps["chance"] < scoring.MIN_CHANCE].drop_duplicates("opportunity_id")
print("\n2. tiradas da lista (distintas):", len(parked), "| ganhas", int(parked["won_after"].sum()),
      "| perdidas", int(parked["lost_after"].sum()),
      "| nunca fechadas", int((~parked["won_after"] & ~parked["lost_after"]).sum()))

# 3. Regra simples de encerramento por idade
engaging = deals[deals["deal_stage"] == "Engaging"].copy()
engaging["age"] = (REF - engaging["engage_date"]).dt.days
won = deals[deals["deal_stage"] == "Won"].copy()
won["cycle"] = (won["close_date"] - won["engage_date"]).dt.days
print("\n3. ganhos com ciclo > 138 dias:", int((won["cycle"] > 138).sum()), "de", len(won))
print("   regra 'mais de 138 dias' encerraria", int((engaging["age"] > 138).sum()), "de", len(engaging), "em Engaging")
scored, _ = scoring.score_open_deals(deals, REF)
dead = scored[scored["lista"].isin(["reativar", "encerrar"])]
print("   a ferramenta tira da lista", len(dead), "| dessas, com mais de 138 dias:", int((dead["age"] > 138).sum()),
      "| entre 97 e 138 dias:", int(((dead["age"] <= 138)).sum()))

# 4. Quanto da receita fecha rápido
print("\n4. receita ganha em até 14 dias do início:", round(won.loc[won["cycle"] <= 14, "close_value"].sum() / won["close_value"].sum(), 3))

# 5. Score x preço entre as vivas de hoje
focus = scored[scored["lista"] == "foco"]
print("\n5. vivas hoje:", len(focus), "| vendedores com alguma:", focus["sales_agent"].nunique(),
      "| correlação score x preço:", round(focus["score"].corr(focus["sales_price"], method="spearman"), 2),
      "| score x chance:", round(focus["score"].corr(focus["chance"], method="spearman"), 2))
print("   receita mensal média ganha em 2017 (mar-dez):", int(won["close_value"].sum() / 10),
      "| valor de tabela das vivas:", int(focus["sales_price"].sum()),
      "| das não iniciadas:", int(scored.loc[scored["lista"] == "abordar", "sales_price"].sum()))

# 6. Entrada de negociações por mês (a base está secando?)
starts = deals[deals["engage_date"] >= "2017-06-01"].groupby(deals["engage_date"].dt.to_period("M")).size()
print("\n6. negociações iniciadas por mês:", starts.to_dict())
