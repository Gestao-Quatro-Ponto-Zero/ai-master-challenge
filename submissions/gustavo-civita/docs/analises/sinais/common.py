import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3] / "solution"))
import numpy as np, pandas as pd
import scoring
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 50); pd.set_option("display.max_rows", 200)
def load():
    d = scoring.load_pipeline()
    d["closed"] = d.deal_stage.isin(["Won", "Lost"])
    d["won"] = (d.deal_stage == "Won").astype(float)
    d.loc[~d.closed, "won"] = np.nan
    d["cycle"] = (d.close_date - d.engage_date).dt.days
    d["ratio"] = d.close_value / d.sales_price
    d["is_sub"] = d.subsidiary_of.notna()
    return d
TODAY = pd.Timestamp("2017-12-31")
