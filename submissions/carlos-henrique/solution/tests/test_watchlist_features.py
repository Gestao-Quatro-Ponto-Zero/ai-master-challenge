import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from watchlist_features import REFERENCE_DATE, _window

def test_cutoff_and_retrospective_windows():
    frame=pd.DataFrame({"event_time":pd.to_datetime(["2024-12-01","2024-12-31 19:00:00","2025-01-01"], format="mixed")})
    scoped=_window(frame,REFERENCE_DATE,30)
    assert scoped["event_time"].max() == REFERENCE_DATE
    assert not scoped["event_time"].gt(REFERENCE_DATE).any()
