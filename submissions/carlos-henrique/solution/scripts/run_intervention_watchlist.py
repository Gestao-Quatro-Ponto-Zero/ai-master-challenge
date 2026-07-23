"""Run the deterministic governed Phase 7 intervention watchlist."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

SOLUTION_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = SOLUTION_ROOT / "src"
if str(SRC_ROOT) not in sys.path: sys.path.insert(0, str(SRC_ROOT))

from watchlist_builder import assemble_watchlist, load_graph_evidence  # noqa: E402
from watchlist_features import REFERENCE_DATE, build_retrospective_features  # noqa: E402
from watchlist_reporting import build_aggregates, create_figures, render_reports, write_json  # noqa: E402
from watchlist_rules import load_rule_config  # noqa: E402
from watchlist_validation import validate_aggregate_privacy, validate_watchlist  # noqa: E402

PROCESSED=SOLUTION_ROOT/"data"/"processed"; ARTIFACTS=SOLUTION_ROOT/"artifacts"; REPORTS=SOLUTION_ROOT/"reports"; FIGURES=REPORTS/"figures"
EXPECTED_BASE="1c31ae22632d27ac45137af5b55acee1d6f19f86"
EXPECTED_HASHES={
 "data/processed/account_diagnostic_features.parquet":"cc3a4fb1c90f3bfd8110e35998421b7dd854a1841ac71a11df41b6c247cd7988",
 "data/processed/account_survival_dataset.parquet":"f0e82247f3ca4d4db32886c818881011f9dbd1f18adaab8f1d36291cd6c92c4e",
 "data/processed/account_journeys.parquet":"1d9dc6795a92f2389f315503a38263f24713290d2c74eb4e8823e0eb283faeed",
 "data/processed/account_journey_taxonomy.parquet":"87f5d43bc4503e313084790fb25947c44b9f9362b556a2bf1fb9793edc0f348e",
 "data/processed/event_log.parquet":"0e9e60d06ce6fbd62103924aab7beda6d0eab9ed5a87ea32cee786abcdb0373f",
 "data/processed/journey_instance_graph.graphml":"b9c645109097d589e15703e829eb28357dbf46194702d4b5b6d24ba90ae164dc",
 "data/processed/journey_analytical_graph.graphml":"84e20c30dd2e8674257b1dc737b37f88bccd17c80425bec4b7e58a3c3cbb6775",
 "artifacts/graph_findings.json":"ecb52c72df6b5a498feb0b5269c67c3d0bdfd945c0b83c3eac15c36556a7d360",
 "artifacts/graph_queries.json":"d6fdf02d6553b71757df57490229fc1a9934b20923aecceb4468f211f00e4992",
 "artifacts/journey_findings.json":"58f31818ec28049c334190c10c9405a82b7062d34b4cf0185de90b1ed2c02008",
 "artifacts/survival_findings.json":"0357cb4692d8cb94ef594450d2e2557322c62c8be70c4725dda9fcbf85cc04cc",
}
OUTPUT_NAMES=("watchlist_summary.json","watchlist_rules.json","watchlist_queue_metrics.json","watchlist_priority_metrics.json","watchlist_overlap.json","watchlist_evidence_summary.json","watchlist_graph_evidence.json","watchlist_quality.json","watchlist_findings.json","watchlist_validation.json")

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def validate_inputs() -> dict[str, Any]:
    failures=[]
    for relative,expected in EXPECTED_HASHES.items():
        path=SOLUTION_ROOT/relative
        if not path.is_file() or sha256(path)!=expected: failures.append(relative)
    if failures: raise RuntimeError(f"Phase 7 input gate failed: {failures}")
    return {"expected_base_commit":EXPECTED_BASE,"verified_inputs":len(EXPECTED_HASHES),"all_hashes_match":True,"input_hashes":EXPECTED_HASHES}

def run(reference_date: pd.Timestamp=REFERENCE_DATE) -> dict[str, Any]:
    input_gate=validate_inputs(); config=load_rule_config(SOLUTION_ROOT/"config"/"watchlist_rules.json")
    diagnostic=pd.read_parquet(PROCESSED/"account_diagnostic_features.parquet"); survival=pd.read_parquet(PROCESSED/"account_survival_dataset.parquet")
    journeys=pd.read_parquet(PROCESSED/"account_journeys.parquet"); taxonomy=pd.read_parquet(PROCESSED/"account_journey_taxonomy.parquet"); events=pd.read_parquet(PROCESSED/"event_log.parquet")
    built=build_retrospective_features(events,diagnostic,survival,taxonomy,journeys,pd.Timestamp(reference_date))
    graph,graph_metrics=load_graph_evidence(PROCESSED/"journey_instance_graph.graphml",PROCESSED/"journey_analytical_graph.graphml")
    features=built.frame.merge(graph,on="account_key",how="left")
    for column,default in {"matched_pattern_keys":"[]","matched_graph_finding_ids":"[]","matched_graph_paths":"[]","graph_pattern_count":0,"has_promotable_churn_path":False,"has_promotable_support_churn_path":False,"graph_evidence_stability":"NO_GRAPH_EVIDENCE","graph_evidence_limitation":"NO_ELIGIBLE_PATTERN_MATCH"}.items(): features[column]=features[column].fillna(default)
    items,summary,evidence,executions=assemble_watchlist(features,config)
    validation=validate_watchlist(items,summary,evidence,features,executions,pd.Timestamp(reference_date)); validation["input_gate"]=input_gate
    aggregates=build_aggregates(items,summary,evidence,executions,built.accounting,graph_metrics,validation); validate_aggregate_privacy(aggregates)
    PROCESSED.mkdir(parents=True,exist_ok=True); items.to_parquet(PROCESSED/"intervention_watchlist.parquet",index=False); summary.to_parquet(PROCESSED/"account_watchlist_summary.parquet",index=False); evidence.to_parquet(PROCESSED/"watchlist_evidence.parquet",index=False)
    for name in OUTPUT_NAMES: write_json(ARTIFACTS/name,aggregates[name])
    create_figures(items,summary,FIGURES,pd.Timestamp(reference_date).isoformat()); render_reports(REPORTS,aggregates)
    return {"gate_result":validation["gate_result"],"accounts":len(summary),"items":len(items),"queues":items["queue"].nunique(),"rules_promoted":items["watchlist_rule_id"].nunique(),"reference_date":pd.Timestamp(reference_date).isoformat()}

if __name__=="__main__": print(json.dumps(run(),ensure_ascii=False,indent=2,sort_keys=True))
