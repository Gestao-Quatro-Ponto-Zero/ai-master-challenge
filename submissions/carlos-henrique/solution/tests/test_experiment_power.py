import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from experiment_power import mean_sample_size,proportion_sample_size,survival_sample_size

def test_power_and_attrition_primitives_are_conservative():
    assert proportion_sample_size(.30,.05)>proportion_sample_size(.30,.10)>0
    assert mean_sample_size(2,.5)>mean_sample_size(2,1)>0
    assert survival_sample_size(.40,.80)>0
