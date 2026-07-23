import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from experiment_randomization import simulate_assignments,standardized_mean_difference,validate_randomization

def test_simulation_is_seeded_non_operational_and_has_no_outcome():
    frame=pd.DataFrame({"experiment_id":["E"]*4,"account_key":["a","b","c","d"],"mrr_band":["LOW"]*4,"data_confidence":["MEDIUM"]*4,"eligibility_status":["ELIGIBLE"]*4,"exclusion_reason":[""]*4})
    first=simulate_assignments(frame,7); second=simulate_assignments(frame,7)
    pd.testing.assert_frame_equal(first,second); assert validate_randomization(first)["synthetic_outcomes"]==0
    assert set(first.simulated_arm)=={"SIMULATED_CONTROL","SIMULATED_TREATMENT"} and first.simulation_only.all()
    assert standardized_mean_difference(pd.Series([1,2]),pd.Series([1,2]))==0
