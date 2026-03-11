import pickle
from pathlib import Path
from typing import Any

import joblib


def get_memory(cache_dir: str = ".cache/api") -> joblib.Memory:
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    return joblib.Memory(cache_dir, verbose=0)


def save_artifact(obj: Any, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(obj, f)


def load_artifact(path: str) -> Any:
    with open(path, "rb") as f:
        return pickle.load(f)


def artifact_exists(path: str) -> bool:
    return Path(path).exists()
