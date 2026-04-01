"""
Dependências compartilhadas entre routers.
Carrega e cacheia dados/benchmarks em memória no processo da API.
"""

import sys
from pathlib import Path
from functools import lru_cache
from typing import Dict, List, Tuple

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.data_loader import load_raw_data, load_benchmarks as _load_benchmarks, preprocess_pipeline


@lru_cache(maxsize=1)
def get_benchmarks() -> Dict:
    return _load_benchmarks()


@lru_cache(maxsize=1)
def get_raw_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return load_raw_data()


@lru_cache(maxsize=1)
def get_pipeline_df() -> pd.DataFrame:
    pipeline_df, _, products_df, teams_df = get_raw_data()
    pipeline_df = preprocess_pipeline(pipeline_df, products_df)
    pipeline_df = pipeline_df.merge(
        teams_df[['sales_agent', 'regional_office', 'manager']],
        on='sales_agent',
        how='left',
    )
    return pipeline_df
