"""Build the compact, non-sensitive serving asset used by the public dashboard."""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "processed" / "posts_analytical.csv"
TARGET = ROOT / "dashboard" / "assets" / "dashboard_posts.parquet"

COLUMNS = [
    "id",
    "platform",
    "content_type",
    "content_category",
    "views",
    "creator_size",
    "is_sponsored",
    "audience_age_distribution",
    "audience_gender_distribution",
    "audience_location",
    "engagement_rate_views",
]


def main() -> None:
    frame = pd.read_csv(SOURCE, usecols=COLUMNS)
    if len(frame) != 52_214 or not frame["id"].is_unique:
        raise ValueError("dashboard serving asset failed population checks")
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(TARGET, index=False, compression="zstd")
    print(f"wrote {TARGET} ({len(frame):,} rows, {len(frame.columns)} columns)")


if __name__ == "__main__":
    main()
