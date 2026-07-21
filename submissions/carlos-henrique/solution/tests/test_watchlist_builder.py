from pathlib import Path
import pandas as pd

def test_outputs_preserve_logical_grain_and_consolidation():
    root=Path(__file__).parents[1]
    items=pd.read_parquet(root/"data/processed/intervention_watchlist.parquet"); summary=pd.read_parquet(root/"data/processed/account_watchlist_summary.parquet")
    assert not items.duplicated(["account_key","reference_date","watchlist_rule_id"]).any()
    assert summary["account_key"].is_unique and set(items["account_key"]) == set(summary["account_key"])
    assert "account_id" not in items and items["requires_human_review"].all()
