from __future__ import annotations

from pathlib import Path
from typing import Any
import json

import pandas as pd


class OutputRepository:
    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_dataframe(self, df: pd.DataFrame, filename: str) -> Path:
        path = self.output_dir / filename
        df.to_csv(path, index=False)
        return path

    def save_text(self, text: str, filename: str) -> Path:
        path = self.output_dir / filename
        path.write_text(text, encoding="utf-8")
        return path

    def save_json(self, obj: dict[str, Any], filename: str) -> Path:
        path = self.output_dir / filename
        path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
        return path
