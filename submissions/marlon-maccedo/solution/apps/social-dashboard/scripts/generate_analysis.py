#!/usr/bin/env python3
"""
Generate social media analysis JSON from social_media_dataset.csv.

Usage:
    cd apps/social-dashboard
    python scripts/generate_analysis.py

Output:
    data/social_analysis.json
"""

import json
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR    = Path(__file__).parent.parent / 'data'
OUTPUT_FILE = DATA_DIR / 'social_analysis.json'


# ── Data loading ───────────────────────────────────────────────────────────────

def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / 'social_media_dataset.csv')

    df['post_date'] = pd.to_datetime(df['post_date'], format='%m/%d/%y %I:%M %p', errors='coerce')
    df['engagement_rate'] = (
        (df['likes'] + df['shares'] + df['comments_count']).astype(float)
        / df['views'].replace(0, np.nan)
    )
    df['month'] = df['post_date'].dt.to_period('M').astype(str)
    df['day_of_week'] = df['post_date'].dt.day_name()

    print(f'  rows: {len(df):,}')
    print(f'  date range: {df["post_date"].min().date()} → {df["post_date"].max().date()}')
    print(f'  avg engagement rate: {df["engagement_rate"].mean():.3f}')
    return df


# ── Temporal trend ─────────────────────────────────────────────────────────────

def compute_temporal(df: pd.DataFrame) -> list:
    monthly = (
        df.groupby('month')
        .agg(
            avgEngagementRate=('engagement_rate', lambda x: round(x.mean() * 100, 2)),
            totalPosts=('id', 'count'),
            totalViews=('views', 'sum'),
        )
        .reset_index()
        .rename(columns={'month': 'month'})
        .sort_values('month')
    )
    return monthly.to_dict(orient='records')


# ── Hashtag analysis ───────────────────────────────────────────────────────────

def compute_top_hashtags(df: pd.DataFrame, top_n: int = 20) -> list:
    rows = []
    for _, row in df.iterrows():
        raw = row.get('hashtags')
        if not isinstance(raw, str):
            continue
        tags = [t.strip().lower() for t in raw.split(',') if t.strip()]
        for tag in tags:
            rows.append({'hashtag': tag, 'engagement': row['engagement_rate']})

    tag_df = pd.DataFrame(rows)
    if tag_df.empty:
        return []

    result = (
        tag_df.groupby('hashtag')
        .agg(
            avgEngagementRate=('engagement', lambda x: round(x.mean() * 100, 2)),
            totalPosts=('hashtag', 'count'),
        )
        .reset_index()
        .sort_values('totalPosts', ascending=False)
        .head(top_n)
    )
    return result.to_dict(orient='records')


# ── Content length buckets ─────────────────────────────────────────────────────

def compute_content_length_buckets(df: pd.DataFrame) -> list:
    def bucket(n):
        if n < 50:   return 'muito curto (<50)'
        if n < 100:  return 'curto (50-99)'
        if n < 200:  return 'médio (100-199)'
        if n < 500:  return 'longo (200-499)'
        return 'muito longo (500+)'

    df2 = df.copy()
    df2['bucket'] = df2['content_length'].apply(bucket)

    ORDER = ['muito curto (<50)', 'curto (50-99)', 'médio (100-199)', 'longo (200-499)', 'muito longo (500+)']
    result = (
        df2.groupby('bucket')
        .agg(
            avgEngagementRate=('engagement_rate', lambda x: round(x.mean() * 100, 2)),
            totalPosts=('id', 'count'),
            avgContentLength=('content_length', lambda x: round(x.mean(), 1)),
        )
        .reset_index()
        .rename(columns={'bucket': 'lengthBucket'})
    )
    result['_order'] = result['lengthBucket'].apply(lambda x: ORDER.index(x) if x in ORDER else 99)
    return result.sort_values('_order').drop(columns='_order').to_dict(orient='records')


# ── Language performance ───────────────────────────────────────────────────────

def compute_language_performance(df: pd.DataFrame) -> list:
    result = (
        df.groupby('language')
        .agg(
            avgEngagementRate=('engagement_rate', lambda x: round(x.mean() * 100, 2)),
            totalPosts=('id', 'count'),
        )
        .reset_index()
        .sort_values('avgEngagementRate', ascending=False)
    )
    return result.to_dict(orient='records')


# ── Day of week posting patterns ───────────────────────────────────────────────

def compute_posting_by_day(df: pd.DataFrame) -> list:
    DAY_ORDER = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    result = (
        df.dropna(subset=['day_of_week'])
        .groupby('day_of_week')
        .agg(
            avgEngagementRate=('engagement_rate', lambda x: round(x.mean() * 100, 2)),
            totalPosts=('id', 'count'),
        )
        .reset_index()
    )
    result['_order'] = result['day_of_week'].apply(lambda x: DAY_ORDER.index(x) if x in DAY_ORDER else 99)
    return result.sort_values('_order').drop(columns='_order').to_dict(orient='records')


# ── Creator efficiency (engagement per 1K followers) ──────────────────────────

def compute_creator_efficiency(df: pd.DataFrame) -> list:
    def tier(n):
        if n < 10_000:    return 'nano (<10K)'
        if n < 100_000:   return 'micro (10K-100K)'
        if n < 1_000_000: return 'macro (100K-1M)'
        return 'mega (>1M)'

    df2 = df.copy()
    df2['tier'] = df2['follower_count'].apply(tier)
    df2['engPer1KFollowers'] = (df2['engagement_rate'] * 1000) / df2['follower_count'].replace(0, np.nan)

    TIER_ORDER = ['nano (<10K)', 'micro (10K-100K)', 'macro (100K-1M)', 'mega (>1M)']
    result = (
        df2.groupby('tier')
        .agg(
            avgEngagementRate=('engagement_rate', lambda x: round(x.mean() * 100, 2)),
            avgEngPer1KFollowers=('engPer1KFollowers', lambda x: round(x.mean(), 4)),
            totalPosts=('id', 'count'),
            avgFollowers=('follower_count', lambda x: round(x.mean())),
        )
        .reset_index()
    )
    result['_order'] = result['tier'].apply(lambda x: TIER_ORDER.index(x) if x in TIER_ORDER else 99)
    return result.sort_values('_order').drop(columns='_order').to_dict(orient='records')


# ── Location performance ───────────────────────────────────────────────────────

def compute_location_performance(df: pd.DataFrame, top_n: int = 15) -> list:
    result = (
        df.dropna(subset=['audience_location'])
        .groupby('audience_location')
        .agg(
            avgEngagementRate=('engagement_rate', lambda x: round(x.mean() * 100, 2)),
            totalPosts=('id', 'count'),
        )
        .reset_index()
        .rename(columns={'audience_location': 'location'})
        .sort_values('totalPosts', ascending=False)
        .head(top_n)
    )
    return result.to_dict(orient='records')


# ── Platform × Day heatmap ────────────────────────────────────────────────────

def compute_platform_day_heatmap(df: pd.DataFrame) -> list:
    result = (
        df.dropna(subset=['day_of_week'])
        .groupby(['platform', 'day_of_week'])
        .agg(
            avgEngagementRate=('engagement_rate', lambda x: round(x.mean() * 100, 2)),
            totalPosts=('id', 'count'),
        )
        .reset_index()
    )
    return result.to_dict(orient='records')


# ── Main ───────────────────────────────────────────────────────────────────────

def to_serializable(obj):
    """Convert numpy scalars to Python native types for JSON serialization."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    raise TypeError(f'Not serializable: {type(obj)}')


def main():
    print('Loading data...')
    df = load_data()

    print('Computing temporal trend...')
    temporal = compute_temporal(df)

    print('Computing hashtag analysis...')
    top_hashtags = compute_top_hashtags(df)

    print('Computing content length buckets...')
    content_length = compute_content_length_buckets(df)

    print('Computing language performance...')
    language = compute_language_performance(df)

    print('Computing day of week patterns...')
    by_day = compute_posting_by_day(df)

    print('Computing creator efficiency...')
    creator_efficiency = compute_creator_efficiency(df)

    print('Computing location performance...')
    location = compute_location_performance(df)

    print('Computing platform × day heatmap...')
    platform_day = compute_platform_day_heatmap(df)

    output = {
        'temporal':          temporal,
        'topHashtags':       top_hashtags,
        'contentLength':     content_length,
        'languagePerf':      language,
        'postingByDay':      by_day,
        'creatorEfficiency': creator_efficiency,
        'locationPerf':      location,
        'platformDayHeatmap': platform_day,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=to_serializable)

    print(f'\nSaved → {OUTPUT_FILE}')
    print(f'  temporal months:   {len(temporal)}')
    print(f'  top hashtags:      {len(top_hashtags)}')
    print(f'  content buckets:   {len(content_length)}')
    print(f'  languages:         {len(language)}')
    print(f'  days of week:      {len(by_day)}')
    print(f'  creator tiers:     {len(creator_efficiency)}')
    print(f'  locations:         {len(location)}')
    print(f'  platform×day:      {len(platform_day)}')


if __name__ == '__main__':
    main()
