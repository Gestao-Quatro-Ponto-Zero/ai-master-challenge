"""
DealSignal UI — Cached data loaders.

Loads and caches the scored pipeline results and model metadata from disk.
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

# Path to the dealsignal project root (two levels up from app/ui/)
_ROOT = Path(__file__).parent.parent.parent

RESULTS_PATH  = _ROOT / "data" / "results.csv"
METADATA_PATH = _ROOT / "model" / "artifacts" / "metadata.json"

ALL         = "Todos"
FILTER_KEYS = ["sel_office", "sel_manager", "sel_agent"]


@st.cache_data
def load_results() -> pd.DataFrame:
    """Loads the scored pipeline CSV and coerces numeric columns."""
    if not RESULTS_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(RESULTS_PATH)
    df["win_probability"]  = pd.to_numeric(df["win_probability"],  errors="coerce")
    df["expected_revenue"] = pd.to_numeric(df["expected_revenue"], errors="coerce")
    df["effective_value"]  = pd.to_numeric(df["effective_value"],  errors="coerce")
    return df


@st.cache_data
def load_metadata() -> dict:
    """Loads model metadata JSON (CV AUC, train/score counts, etc.)."""
    if not METADATA_PATH.exists():
        return {}
    with open(METADATA_PATH) as f:
        return json.load(f)
