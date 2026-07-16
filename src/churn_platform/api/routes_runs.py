"""SPEC-10.3: Pipeline execution endpoints."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException

from churn_platform.analysis import descriptive, segmentation
from churn_platform.datamodel import account_view as dv
from churn_platform.pipeline import cleaner, loader, merger, validator
from churn_platform.report import html_report
from churn_platform.scoring import health_score

from . import get_state

logger = logging.getLogger(__name__)
router = APIRouter()


def _convert_numpy(obj):
    if isinstance(obj, dict):
        return {k: _convert_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_numpy(v) for v in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    return obj


def _load_yaml(path: str) -> dict:
    import yaml
    with open(path) as f:
        return yaml.safe_load(f)


@router.post("/run")
async def run_pipeline(config_path: str = "config/ravenstack.yaml"):
    run_id = str(uuid.uuid4())[:8]
    state = get_state()
    state["runs"][run_id] = {"status": "processing", "started_at": datetime.utcnow().isoformat() + "Z"}

    try:
        cfg = _load_yaml(config_path)
        base_dir = str(Path(config_path).resolve().parent.parent)
        output_dir = Path(state.get("output_dir", "output"))
        output_dir.mkdir(parents=True, exist_ok=True)

        sources = loader.load_all_sources(cfg, base_dir)
        sources = cleaner.run(sources)

        schemas = _load_yaml("config/schemas/ravenstack_schema.yaml")
        dqr = validator.run(sources, schemas, str(output_dir))

        merged = merger.run(sources, cfg.get("merges", {}))
        df = dv.build(sources, merged)

        df.to_parquet(output_dir / "account_view.parquet", index=False)
        logger.info("Account View salva: %s contas, %s colunas", len(df), len(df.columns))

        stats = descriptive.overall_stats(df)
        seg_results = segmentation.run(df, cfg)
        desc_results = descriptive.run(df, cfg)
        analysis_data = {
            "overall_stats": stats,
            "segments": seg_results,
            "descriptive": desc_results,
        }

        with open(output_dir / "analysis_results.json", "w") as f:
            json.dump(analysis_data, f, indent=2, default=str)

        scored = health_score.run(df, cfg)
        scored.to_parquet(output_dir / "scored_accounts.parquet", index=False)

        report_path = html_report.build_report(
            account_view=df,
            stats=stats,
            segments=seg_results,
            descriptive=desc_results,
            scored=scored,
            output_path=str(output_dir / "report.html"),
        )

        state["accounts_df"] = df
        state["scored_df"] = scored
        state["analysis_data"] = analysis_data

        health_dist = {
            k: int(v) for k, v in scored["health_tier"].value_counts().to_dict().items()
        }
        result = {
            "run_id": run_id,
            "status": "completed",
            "pipeline_version": "0.1.0",
            "results": {
                "overall_stats": _convert_numpy(stats),
                "segments": _convert_numpy(seg_results),
                "health_distribution": health_dist,
            },
            "output_paths": {
                "report": f"/output/report.html",
                "data": f"/output/account_view.parquet",
            },
            "completed_at": datetime.utcnow().isoformat() + "Z",
        }

        state["runs"][run_id] = result
        return result

    except Exception as e:
        logger.exception("Pipeline run %s falhou", run_id)
        state["runs"][run_id] = {
            "run_id": run_id,
            "status": "failed",
            "error": str(e),
        }
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs")
async def list_runs():
    state = get_state()
    return {"runs": list(state["runs"].values())}


@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    state = get_state()
    run = state["runs"].get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} não encontrada")
    return run
