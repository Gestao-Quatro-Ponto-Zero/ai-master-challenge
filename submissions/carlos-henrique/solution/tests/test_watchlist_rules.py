import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from watchlist_rules import apply_rules, validate_rule_config

def test_real_config_and_broad_behavioral_suppression():
    import json
    root=Path(__file__).parents[1]; config=json.loads((root/"config/watchlist_rules.json").read_text())
    assert validate_rule_config(config)["rule_count"] == 16
    rule={**config["rules"][0],"rule_id":"W999","minimum_support":1,"minimum_group_size":1,"minimum_quality_coverage":0,"required_conditions":[],"queue":"ADOPTION_REVIEW"}
    frame=pd.DataFrame({"account_id":[str(i) for i in range(10)],"account_key":[f"a{i}" for i in range(10)],"quality_coverage_ratio":[1]*10,"stability_status":["ROBUST"]*10})
    out,runs=apply_rules(frame,{"config_version":"x","rules":[rule]})
    assert out.empty and runs[0]["status"] == "BROAD_RULE_NOT_PROMOTED"
