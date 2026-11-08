"""Backtest em DADOS REAIS: em cada data T, treina cada abordagem só com o passado e mede o que aconteceu
nos H dias seguintes. É a evidência principal (os mocks só testam a rotina diária)."""
from __future__ import annotations

import pandas as pd

from .metrics import outcomes, rank_metrics, seller_topk
from .scorers import HORIZON, Challenger, champion, price_only

DEFAULT_SNAPSHOTS = pd.date_range("2017-06-15", "2017-11-30", freq="14D")


def rankings_at(df: pd.DataFrame, T: pd.Timestamp, h: int = HORIZON) -> tuple[dict, pd.DataFrame, dict]:
    ch = champion(df, T)
    cl = Challenger(h).fit(df, T).score(df, T)
    ids = ch.index.intersection(cl.index)
    ranks = {
        "atual_score_lista": ch.loc[ids, "score"].astype("Float64"),        # o que o vendedor vê (zumbi fora)
        "atual_valor_esperado": ch.loc[ids, "expected_value"],
        "so_preco": price_only(df, T).loc[ids],
        "novo_conversao_30d": cl.loc[ids, "p_h"],
        "novo_receita_30d": cl.loc[ids, "ev_h"],
    }
    ctx = pd.DataFrame({"age": ch.loc[ids, "age_days"], "seller": ch.loc[ids, "seller"],
                        "band": ch.loc[ids, "band"], "score_atual": ch.loc[ids, "score"],
                        "score_novo_rev": cl.loc[ids, "score_rev"], "score_novo_conv": cl.loc[ids, "score_conv"]})
    return ranks, ctx, ch.attrs["thresholds"]


def run(df: pd.DataFrame, snapshots=DEFAULT_SNAPSHOTS, h: int = HORIZON, log=print) -> pd.DataFrame:
    rows = []
    for T in snapshots:
        ranks, ctx, thr = rankings_at(df, T, h)
        out = outcomes(df, ctx.index, T, h)
        for name, r in ranks.items():
            m = rank_metrics(r, out, ctx["age"], thr) | seller_topk(r, out, ctx["seller"])
            rows.append({"snapshot": T.date().isoformat(), "abordagem": name, **m})
        log(f"  backtest {T.date()} ok ({len(ctx)} deals abertos)")
    return pd.DataFrame(rows)


def summarize(res: pd.DataFrame) -> pd.DataFrame:
    cols = ["auc_won_h", "precision_top20", "lift_top20", "rev_capture_top20", "stale_share_top20",
            "zombie_share_top20", "seller_top5_win_rate", "seller_top5_revenue"]
    return res.groupby("abordagem")[cols].mean().sort_values("rev_capture_top20", ascending=False)
