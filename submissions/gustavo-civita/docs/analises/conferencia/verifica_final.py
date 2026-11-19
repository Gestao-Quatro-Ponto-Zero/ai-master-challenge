"""Confere pontos do advogado do diabo da submissão."""
import sys

import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3] / "solution"))
import backtest  # noqa: E402
import scoring  # noqa: E402

deals = scoring.load_pipeline()
REF = scoring.reference_date(deals)

# 1. A ordem da tela (quem "pode fechar este mês" primeiro) contra a ordem testada
rows = []
for date in backtest.SNAPSHOTS:
    as_of = pd.Timestamp(date)
    snap = backtest.snapshot_with_predictions(deals, as_of)
    snap["hot"] = (snap["soon"] >= scoring.SOON_MIN_CHANCE) & (snap["chance"] >= scoring.MIN_CHANCE)

    def top(columns):
        chosen = snap.sort_values(columns, ascending=False).groupby("sales_agent").head(backtest.TOP_N)
        return chosen["revenue_after"].sum()

    rows.append({
        "tri": as_of.quarter,
        "testada": top(["valor_esperado", "sales_price"]),
        "tela": top(["hot", "valor_esperado", "sales_price"]),
        "regra": top(["preco_recentes", "sales_price"]),
    })
table = pd.DataFrame(rows)
summary = table.groupby("tri").sum()
summary["testada_vs_regra"] = (summary["testada"] / summary["regra"] - 1).round(3)
summary["tela_vs_regra"] = (summary["tela"] / summary["regra"] - 1).round(3)
print("1. Ordem testada x ordem da tela, contra a regra simples:")
print(summary.round(0).to_string())
print("   semanas em que a ordem da tela ganha da regra:",
      (table["tela"] > table["regra"]).groupby(table["tri"]).agg(["sum", "size"]).to_dict("index"))

# 2. "Desconto": o valor fechado varia para cima e para baixo da tabela?
won = deals[deals["deal_stage"] == "Won"]
ratio = won["close_value"] / won["sales_price"]
print("\n2. valor fechado ÷ tabela: média", round(ratio.mean(), 4), "| abaixo da tabela", round((ratio < 1).mean(), 3),
      "| 7%+ abaixo", round((ratio <= 0.93).mean(), 3), "| 7%+ acima", round((ratio >= 1.07).mean(), 3),
      "| mínimo", round(ratio.min(), 3), "| máximo", round(ratio.max(), 3))

# 3. Números do plano de piloto
closed = deals[deals["deal_stage"].isin(["Won", "Lost"])]
n_won = (closed["deal_stage"] == "Won").sum()
print("\n3. ganhas ÷ (ganhas + perdidas):", round(n_won / len(closed), 3),
      "| encerrando 987:", round(n_won / (len(closed) + 987), 3),
      "| encerrando 1.291:", round(n_won / (len(closed) + 1291), 3))
started = deals[deals["engage_date"].notna()]
mature = started[started["engage_date"] <= REF - pd.Timedelta(days=138)]
print("   ganhas ÷ iniciadas (todas):", round((started["deal_stage"] == "Won").mean(), 3),
      "| só iniciadas há mais de 138 dias:", round((mature["deal_stage"] == "Won").mean(), 3),
      "| nunca fechadas entre essas:", round(mature["close_date"].isna().mean(), 3), f"(n={len(mature)})")

# 4. Onde a chance zera hoje
scored, model = scoring.score_open_deals(deals, REF)
focus = scored[scored["lista"] == "foco"]
print("\n4. idade máxima com chance hoje:", int(focus["age"].max()), "dias | vendedores com mais de 10 vivas:",
      int((focus.groupby("sales_agent").size() > 10).sum()))
