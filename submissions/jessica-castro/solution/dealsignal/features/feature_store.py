from pathlib import Path

import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)


def save_features(df: pd.DataFrame, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if path.endswith(".parquet"):
        df.to_parquet(path, index=True)
    else:
        df.to_csv(path, index=True)
    logger.info("Saved feature store to %s (%d rows)", path, len(df))


def load_features(path: str) -> pd.DataFrame:
    if path.endswith(".parquet"):
        return pd.read_parquet(path)
    return pd.read_csv(path, index_col=0)
