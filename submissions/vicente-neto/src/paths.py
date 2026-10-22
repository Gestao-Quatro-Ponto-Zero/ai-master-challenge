"""Caminhos do projeto: data/ (5 CSVs do Kaggle) e outputs/ (tudo o que os scripts geram)."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DATA = str(ROOT / 'data')
OUT  = str(ROOT / 'outputs')
