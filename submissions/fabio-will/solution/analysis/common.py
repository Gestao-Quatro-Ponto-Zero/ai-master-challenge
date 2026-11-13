"""Shared paths and loaders for the support analysis."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("G4_DATA_DIR", ROOT.parent / "data"))
OUT_DIR = ROOT / "outputs"
OUT_DIR.mkdir(exist_ok=True)

TICKETS_CSV = DATA_DIR / "customer_support_tickets.csv"
IT_TICKETS_CSV = DATA_DIR / "all_tickets_processed_improved_v3.csv"

SEED = 42


def load_tickets() -> pd.DataFrame:
    """Dataset 1: operational metrics + ticket text (Kaggle suraj520)."""
    if not TICKETS_CSV.exists():
        raise SystemExit(f"Missing {TICKETS_CSV}. See README for the Kaggle download.")
    return pd.read_csv(TICKETS_CSV)


def load_it_tickets() -> pd.DataFrame:
    """Dataset 2: 47.8K real IT tickets labelled in 8 topic groups (Kaggle adisongoh)."""
    if not IT_TICKETS_CSV.exists():
        raise SystemExit(f"Missing {IT_TICKETS_CSV}. See README for the Kaggle download.")
    df = pd.read_csv(IT_TICKETS_CSV)
    df["Document"] = df["Document"].fillna("").astype(str)
    return df


def write_json(name: str, payload: dict) -> Path:
    path = OUT_DIR / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=float), encoding="utf-8")
    return path
