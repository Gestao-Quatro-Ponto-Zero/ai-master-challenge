from __future__ import annotations

from pathlib import Path
import re
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.support_copilot.privacy import mask_pii


OUTPUT_DIR = ROOT / "artifacts/demo"
SAMPLE_ROWS = 5000

SOURCES = (
    (
        ROOT / "data/raw/customer-support/customer_support_tickets.csv",
        OUTPUT_DIR / "customer_support_case_sample.csv",
        (
            "Ticket ID",
            "Customer Name",
            "Customer Email",
            "Customer Age",
            "Customer Gender",
        ),
    ),
    (
        ROOT / "data/raw/it-service/all_tickets_processed_improved_v3.csv",
        OUTPUT_DIR / "it_service_case_sample.csv",
        (),
    ),
)


def systematic_sample(frame: pd.DataFrame, rows: int = SAMPLE_ROWS) -> pd.DataFrame:
    if len(frame) <= rows:
        return frame.copy()
    positions = [
        ((len(frame) - 1) * index) // (rows - 1)
        for index in range(rows)
    ]
    return frame.iloc[positions].copy()


def sanitize_text_columns(frame: pd.DataFrame) -> pd.DataFrame:
    sanitized = frame.copy()
    text_columns = [
        column
        for column in ("Ticket Description", "Resolution", "Document")
        if column in sanitized
    ]
    for column in text_columns:
        sanitized[column] = sanitized[column].map(
            lambda value: sanitize_text(str(value)) if pd.notna(value) else value
        )
    return sanitized


def sanitize_text(value: str) -> str:
    masked, _ = mask_pii(value)
    masked = re.sub(r"(?<!\w)@[A-Za-z0-9_]+", "[HANDLE_MASKED]", masked)
    return re.sub(r"https?://\S+", "[URL_MASKED]", masked)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for source, destination, sensitive_columns in SOURCES:
        frame = pd.read_csv(source)
        frame = frame.drop(
            columns=[column for column in sensitive_columns if column in frame],
        )
        sample = sanitize_text_columns(systematic_sample(frame))
        sample.to_csv(destination, index=False)
        print(f"{destination.name}: {len(sample)} linhas")


if __name__ == "__main__":
    main()
