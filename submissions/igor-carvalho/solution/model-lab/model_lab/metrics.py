"""Métricas de 'utilidade para o vendedor' sobre o que aconteceu DEPOIS da foto (horizonte H dias)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


def outcomes(df: pd.DataFrame, ids: pd.Index, T: pd.Timestamp, h: int) -> pd.DataFrame:
    d = df.set_index("opportunity_id").loc[ids]
    end = T + pd.Timedelta(days=h)
    won = (d["won"] == 1) & (d["close_date"] > T) & (d["close_date"] <= end)
    closed = d["won"].notna() & (d["close_date"] > T) & (d["close_date"] <= end)
    return pd.DataFrame({"won_h": won.astype(int), "closed_h": closed.astype(int),
                         "rev_h": np.where(won, d["close_value"].fillna(0), 0.0)}, index=ids)


def rank_metrics(rank: pd.Series, out: pd.DataFrame, age: pd.Series, thr: dict, frac: float = 0.2) -> dict:
    """rank: maior = mais prioritário (NaN = fora da lista, vai para o fim)."""
    r = rank.reindex(out.index).astype(float).fillna(-1e18)
    order = np.argsort(-r.to_numpy(), kind="stable")
    k = max(1, int(len(r) * frac))
    top = out.index[order[:k]]
    y = out["won_h"].to_numpy()
    a = age.reindex(out.index)
    return {
        "auc_won_h": float(roc_auc_score(y, r)) if 0 < y.sum() < len(y) else float("nan"),
        "precision_top20": float(out.loc[top, "won_h"].mean()),
        "base_rate_h": float(y.mean()),
        "lift_top20": float(out.loc[top, "won_h"].mean() / max(y.mean(), 1e-9)),
        "rev_capture_top20": float(out.loc[top, "rev_h"].sum() / max(out["rev_h"].sum(), 1e-9)),
        "stale_share_top20": float((a.loc[top] > thr["stale_days"]).mean()),
        "zombie_share_top20": float((a.loc[top] > thr["review_days"]).mean()),
        "n": int(len(r)),
    }


def seller_topk(rank: pd.Series, out: pd.DataFrame, seller: pd.Series, k: int = 5) -> dict:
    """Visão do vendedor: os k primeiros da SUA lista. Quantos viraram ganho em H dias e quanto de receita."""
    d = out.assign(rank=rank.reindex(out.index).astype(float).fillna(-1e18), seller=seller.reindex(out.index))
    top = d.sort_values("rank", ascending=False, kind="stable").groupby("seller").head(k)
    return {"seller_top5_win_rate": float(top["won_h"].mean()), "seller_top5_revenue": float(top["rev_h"].sum())}


def psi(a: np.ndarray, b: np.ndarray, bins: int = 10) -> float:
    """Population Stability Index entre duas distribuições de score 0-100."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a[~np.isnan(a)], b[~np.isnan(b)]
    if len(a) == 0 or len(b) == 0:
        return float("nan")
    edges = np.linspace(0, 100, bins + 1)
    pa = np.histogram(a, edges)[0] / len(a) + 1e-4
    pb = np.histogram(b, edges)[0] / len(b) + 1e-4
    return float(np.sum((pa - pb) * np.log(pa / pb)))
