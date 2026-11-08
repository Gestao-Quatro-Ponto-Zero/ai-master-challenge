"""Features point-in-time: sem vazamento do futuro e idênticas no treino e no what-if."""
import numpy as np
import pandas as pd
import pytest

from lead_core.features import apply_tables, build_history_tables, open_snapshot, what_if_row
from lead_trainer.repository import CsvDealRepository


@pytest.fixture(scope="module")
def df(synthetic_dir):
    return CsvDealRepository(synthetic_dir).load()


T = pd.Timestamp("2017-08-01")


def test_open_snapshot_only_unclosed_engaged(df):
    s = open_snapshot(df, T)
    assert (s["engage_date"] <= T).all()
    assert (s["close_date"].isna() | (s["close_date"] > T)).all()
    assert (s["age_days"] == (T - s["engage_date"]).dt.days).all()
    assert (s["deal_stage"].isin(["Won", "Lost", "Engaging"])).all()


def test_no_future_leakage(df):
    """Alterar desfechos DEPOIS de T não pode mudar nenhuma feature calculada em T."""
    snap = open_snapshot(df, T)
    before = apply_tables(snap, build_history_tables(df, T, snap))

    future = df.copy()
    mask = future["close_date"] > T
    future.loc[mask, "won"] = 1.0 - future.loc[mask, "won"]
    future.loc[mask, "close_date"] = future.loc[mask, "close_date"] + pd.Timedelta(days=500)
    after = apply_tables(snap, build_history_tables(future, T, snap))

    cols = ["agent_wr", "agent_n", "product_wr", "agent_product_wr", "agent_recent_wr", "agent_load"]
    pd.testing.assert_frame_equal(before[cols], after[cols])


def test_history_matches_slow_reference(df):
    """Compara a versão vetorizada com uma implementação ingênua linha a linha."""
    snap = open_snapshot(df, T)
    tables = build_history_tables(df, T, snap)
    out = apply_tables(snap, tables)
    hist = df[df["won"].notna() & (df["close_date"] <= T)]
    base, k = hist["won"].mean(), 30

    for _, r in out.sample(15, random_state=1).iterrows():
        a = hist[hist["sales_agent"] == r["sales_agent"]]["won"]
        ap = hist[(hist["sales_agent"] == r["sales_agent"]) & (hist["product"] == r["product"])]["won"]
        rec = a_recent = hist[(hist["sales_agent"] == r["sales_agent"]) & (hist["close_date"] > T - pd.Timedelta(days=90))]["won"]
        agent_wr = (a.sum() + k * base) / (len(a) + k)
        assert r["agent_wr"] == pytest.approx(agent_wr)
        assert r["agent_product_wr"] == pytest.approx((ap.sum() + k * agent_wr) / (len(ap) + k))
        assert r["agent_recent_wr"] == pytest.approx((rec.sum() + k * agent_wr) / (len(rec) + k))
        assert r["agent_n"] == len(a)


def test_what_if_row_equals_batch_features(df):
    """O mesmo (vendedor, produto, idade) tem as mesmas features em lote e no what-if."""
    snap = open_snapshot(df, T)
    tables = build_history_tables(df, T, snap)
    batch = apply_tables(snap, tables)
    for _, r in batch.sample(10, random_state=2).iterrows():
        one = what_if_row(tables, r["product"], r["sales_agent"], int(r["age_days"])).iloc[0]
        for col in ["price", "series", "manager", "regional_office", "agent_wr", "agent_n", "product_wr",
                    "agent_product_wr", "agent_recent_wr", "agent_load", "age_days"]:
            assert one[col] == pytest.approx(r[col]) if isinstance(r[col], (float, np.floating)) else one[col] == r[col]


def test_unknown_agent_falls_back_to_base_rate(df):
    tables = build_history_tables(df, T)
    row = pd.DataFrame([{"sales_agent": "Ninguém", "product": "Prod Pro"}])
    out = apply_tables(row, tables).iloc[0]
    assert out["agent_wr"] == pytest.approx(tables["base_wr"])
    assert out["agent_n"] == 0


def test_tables_are_json_serializable(df):
    import json
    json.dumps(build_history_tables(df, T, open_snapshot(df, T)))
