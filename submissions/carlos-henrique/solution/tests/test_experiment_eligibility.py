import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from experiment_eligibility import REFERENCE_DATE,build_eligibility,validate_eligibility
from experiment_hypotheses import build_hypotheses

def test_eligibility_is_cutoff_safe_and_missing_clusters_are_excluded():
    root=Path(__file__).parents[1]; watch=pd.read_parquet(root/"data/processed/intervention_watchlist.parquet")
    frame,_=build_eligibility(watch,build_hypotheses())
    assert validate_eligibility(frame)["rows"]==len(frame)
    assert pd.to_datetime(frame["reference_date"]).le(REFERENCE_DATE).all()
    assert not frame.loc[frame["experiment_id"].eq("EXP003"),"eligibility_status"].eq("ELIGIBLE").any()
