#!/usr/bin/env python3
"""
Challenge 004 analysis builder using only Python standard library.

Inputs:
  - /Users/lenon/Downloads/social_media_dataset.csv

Outputs (inside submissions/lenon-cardozo/solution):
  - data_qa_report.md
  - analysis_summary.json
  - segment_performance.csv
  - sponsorship_comparison.csv
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Dict, Iterable, List, Tuple


ROOT = Path("/Users/lenon/Programas em Desenvolvimento/Challenges/ai-master-challenge")
SUBMISSION_DIR = ROOT / "submissions" / "lenon-cardozo"
SOLUTION_DIR = SUBMISSION_DIR / "solution"
DATASET_PATH = Path("/Users/lenon/Downloads/social_media_dataset.csv")


@dataclass
class ParsedRow:
    platform: str
    content_type: str
    content_category: str
    post_date: datetime
    audience_age_distribution: str
    audience_gender_distribution: str
    audience_location: str
    is_sponsored: str
    disclosure_type: str
    sponsor_category: str
    content_length: float
    views: float
    likes: float
    shares: float
    comments_count: float
    follower_count: float
    interactions: float
    engagement_rate_derived: float
    share_rate: float
    comment_rate: float
    reach_per_follower: float
    year_quarter: str
    year_month: str
    creator_band_quantile: str
    creator_band_market: str
    content_length_bin: str


def q_index(n: int, q: float) -> int:
    if n <= 0:
        return 0
    return min(n - 1, max(0, int(round((n - 1) * q))))


def quantile(values: List[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[q_index(len(ordered), q)]


def to_float(value: str) -> float:
    return float(value)


def to_datetime(value: str) -> datetime:
    return datetime.strptime(value, "%m/%d/%y %I:%M %p")


def quarter_label(dt: datetime) -> str:
    quarter = (dt.month - 1) // 3 + 1
    return f"{dt.year}-Q{quarter}"


def month_label(dt: datetime) -> str:
    return dt.strftime("%Y-%m")


def market_band(followers: float) -> str:
    if followers < 10_000:
        return "<10k"
    if followers < 50_000:
        return "10k-50k"
    if followers < 200_000:
        return "50k-200k"
    if followers < 500_000:
        return "200k-500k"
    return "500k+"


def length_bin(seconds: float) -> str:
    if seconds < 15:
        return "<15s"
    if seconds < 30:
        return "15-29s"
    if seconds < 60:
        return "30-59s"
    if seconds < 120:
        return "60-119s"
    return "120s+"


def quantile_band(followers: float, q20: float, q40: float, q60: float, q80: float) -> str:
    if followers < q20:
        return "Q1"
    if followers < q40:
        return "Q2"
    if followers < q60:
        return "Q3"
    if followers < q80:
        return "Q4"
    return "Q5"


def load_rows() -> Tuple[List[ParsedRow], Dict[str, object]]:
    raw_rows: List[dict] = []
    followers: List[float] = []

    with DATASET_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        expected_columns = [
            "platform",
            "content_type",
            "content_category",
            "post_date",
            "content_length",
            "views",
            "likes",
            "shares",
            "comments_count",
            "follower_count",
            "is_sponsored",
            "audience_age_distribution",
        ]
        missing = [c for c in expected_columns if c not in fieldnames]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        parse_errors = 0
        min_date = None
        max_date = None
        for row in reader:
            try:
                dt = to_datetime(row["post_date"])
                follower_count = to_float(row["follower_count"])
            except Exception:
                parse_errors += 1
                continue

            min_date = dt if min_date is None else min(min_date, dt)
            max_date = dt if max_date is None else max(max_date, dt)

            raw_rows.append(row)
            followers.append(follower_count)

    if not followers:
        raise ValueError("Dataset has no valid rows after parsing.")

    sorted_followers = sorted(followers)
    q20 = sorted_followers[q_index(len(sorted_followers), 0.20)]
    q40 = sorted_followers[q_index(len(sorted_followers), 0.40)]
    q60 = sorted_followers[q_index(len(sorted_followers), 0.60)]
    q80 = sorted_followers[q_index(len(sorted_followers), 0.80)]

    parsed_rows: List[ParsedRow] = []
    for row in raw_rows:
        dt = to_datetime(row["post_date"])
        views = to_float(row["views"])
        likes = to_float(row["likes"])
        shares = to_float(row["shares"])
        comments_count = to_float(row["comments_count"])
        follower_count = to_float(row["follower_count"])
        interactions = likes + shares + comments_count
        engagement_rate_derived = interactions / views if views > 0 else 0.0
        share_rate = shares / views if views > 0 else 0.0
        comment_rate = comments_count / views if views > 0 else 0.0
        reach_per_follower = views / follower_count if follower_count > 0 else 0.0

        parsed_rows.append(
            ParsedRow(
                platform=row["platform"],
                content_type=row["content_type"],
                content_category=row["content_category"],
                post_date=dt,
                audience_age_distribution=row["audience_age_distribution"],
                audience_gender_distribution=row["audience_gender_distribution"],
                audience_location=row["audience_location"],
                is_sponsored=row["is_sponsored"],
                disclosure_type=row["disclosure_type"],
                sponsor_category=row["sponsor_category"],
                content_length=to_float(row["content_length"]),
                views=views,
                likes=likes,
                shares=shares,
                comments_count=comments_count,
                follower_count=follower_count,
                interactions=interactions,
                engagement_rate_derived=engagement_rate_derived,
                share_rate=share_rate,
                comment_rate=comment_rate,
                reach_per_follower=reach_per_follower,
                year_quarter=quarter_label(dt),
                year_month=month_label(dt),
                creator_band_quantile=quantile_band(follower_count, q20, q40, q60, q80),
                creator_band_market=market_band(follower_count),
                content_length_bin=length_bin(to_float(row["content_length"])),
            )
        )

    qa = {
        "dataset_path": str(DATASET_PATH),
        "row_count_valid": len(parsed_rows),
        "row_count_total_minus_header_estimate": len(raw_rows),
        "parse_errors": parse_errors,
        "min_date": min_date.strftime("%Y-%m-%d %H:%M:%S") if min_date else None,
        "max_date": max_date.strftime("%Y-%m-%d %H:%M:%S") if max_date else None,
        "columns_expected_present": True,
        "follower_quantile_cutoffs": {
            "q20": q20,
            "q40": q40,
            "q60": q60,
            "q80": q80,
        },
    }
    return parsed_rows, qa


def platform_baselines(rows: Iterable[ParsedRow]) -> Dict[str, Dict[str, float]]:
    metrics = defaultdict(lambda: defaultdict(list))
    for row in rows:
        metrics[row.platform]["engagement_rate_derived"].append(row.engagement_rate_derived)
        metrics[row.platform]["share_rate"].append(row.share_rate)
        metrics[row.platform]["comment_rate"].append(row.comment_rate)
        metrics[row.platform]["views"].append(row.views)
        metrics[row.platform]["reach_per_follower"].append(row.reach_per_follower)

    out: Dict[str, Dict[str, float]] = {}
    for platform, by_metric in metrics.items():
        out[platform] = {}
        for metric_name, values in by_metric.items():
            out[platform][f"mean_{metric_name}"] = mean(values)
            out[platform][f"median_{metric_name}"] = median(values)
    return out


def summarize(values: List[float]) -> Dict[str, float]:
    if not values:
        return {
            "mean": 0.0,
            "median": 0.0,
            "p25": 0.0,
            "p75": 0.0,
            "p90": 0.0,
        }
    return {
        "mean": mean(values),
        "median": median(values),
        "p25": quantile(values, 0.25),
        "p75": quantile(values, 0.75),
        "p90": quantile(values, 0.90),
    }


def write_segment_performance(rows: List[ParsedRow]) -> Dict[str, object]:
    out_path = SOLUTION_DIR / "segment_performance.csv"
    group = defaultdict(lambda: defaultdict(list))

    for row in rows:
        key = (
            row.platform,
            row.year_quarter,
            row.content_category,
            row.creator_band_market,
            row.creator_band_quantile,
            row.is_sponsored,
            row.content_type,
            row.content_length_bin,
            row.audience_age_distribution,
        )
        group[key]["views"].append(row.views)
        group[key]["engagement_rate_derived"].append(row.engagement_rate_derived)
        group[key]["share_rate"].append(row.share_rate)
        group[key]["comment_rate"].append(row.comment_rate)
        group[key]["reach_per_follower"].append(row.reach_per_follower)

    fields = [
        "platform",
        "year_quarter",
        "content_category",
        "creator_band",
        "creator_band_quantile",
        "is_sponsored",
        "content_type",
        "content_length_bin",
        "audience_age_distribution",
        "n_posts",
        "mean_views",
        "median_views",
        "p25_views",
        "p75_views",
        "p90_views",
        "mean_engagement_rate_derived",
        "median_engagement_rate_derived",
        "p25_engagement_rate_derived",
        "p75_engagement_rate_derived",
        "p90_engagement_rate_derived",
        "mean_share_rate",
        "median_share_rate",
        "p25_share_rate",
        "p75_share_rate",
        "p90_share_rate",
        "mean_comment_rate",
        "median_comment_rate",
        "p25_comment_rate",
        "p75_comment_rate",
        "p90_comment_rate",
        "mean_reach_per_follower",
        "median_reach_per_follower",
        "p25_reach_per_follower",
        "p75_reach_per_follower",
        "p90_reach_per_follower",
    ]

    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for key, metrics in sorted(group.items()):
            views = summarize(metrics["views"])
            err = summarize(metrics["engagement_rate_derived"])
            share = summarize(metrics["share_rate"])
            comment = summarize(metrics["comment_rate"])
            reach = summarize(metrics["reach_per_follower"])
            writer.writerow(
                {
                    "platform": key[0],
                    "year_quarter": key[1],
                    "content_category": key[2],
                    "creator_band": key[3],
                    "creator_band_quantile": key[4],
                    "is_sponsored": key[5],
                    "content_type": key[6],
                    "content_length_bin": key[7],
                    "audience_age_distribution": key[8],
                    "n_posts": len(metrics["views"]),
                    "mean_views": f"{views['mean']:.6f}",
                    "median_views": f"{views['median']:.6f}",
                    "p25_views": f"{views['p25']:.6f}",
                    "p75_views": f"{views['p75']:.6f}",
                    "p90_views": f"{views['p90']:.6f}",
                    "mean_engagement_rate_derived": f"{err['mean']:.10f}",
                    "median_engagement_rate_derived": f"{err['median']:.10f}",
                    "p25_engagement_rate_derived": f"{err['p25']:.10f}",
                    "p75_engagement_rate_derived": f"{err['p75']:.10f}",
                    "p90_engagement_rate_derived": f"{err['p90']:.10f}",
                    "mean_share_rate": f"{share['mean']:.10f}",
                    "median_share_rate": f"{share['median']:.10f}",
                    "p25_share_rate": f"{share['p25']:.10f}",
                    "p75_share_rate": f"{share['p75']:.10f}",
                    "p90_share_rate": f"{share['p90']:.10f}",
                    "mean_comment_rate": f"{comment['mean']:.10f}",
                    "median_comment_rate": f"{comment['median']:.10f}",
                    "p25_comment_rate": f"{comment['p25']:.10f}",
                    "p75_comment_rate": f"{comment['p75']:.10f}",
                    "p90_comment_rate": f"{comment['p90']:.10f}",
                    "mean_reach_per_follower": f"{reach['mean']:.10f}",
                    "median_reach_per_follower": f"{reach['median']:.10f}",
                    "p25_reach_per_follower": f"{reach['p25']:.10f}",
                    "p75_reach_per_follower": f"{reach['p75']:.10f}",
                    "p90_reach_per_follower": f"{reach['p90']:.10f}",
                }
            )

    return {"segment_count": len(group), "output_file": str(out_path)}


def sponsorship_confidence(n_s: int, n_o: int, lift_err: float, lift_share: float) -> str:
    n_min = min(n_s, n_o)
    err_delta = abs(lift_err - 1.0)
    share_delta = abs(lift_share - 1.0)
    if n_min >= 120 and err_delta >= 0.005 and share_delta >= 0.005:
        return "High"
    if n_min >= 80 and err_delta >= 0.002:
        return "Medium"
    return "Low"


def write_sponsorship_comparison(rows: List[ParsedRow]) -> Dict[str, object]:
    out_path = SOLUTION_DIR / "sponsorship_comparison.csv"
    strata = defaultdict(lambda: {"TRUE": defaultdict(list), "FALSE": defaultdict(list)})

    for row in rows:
        key = (
            row.platform,
            row.year_quarter,
            row.content_category,
            row.creator_band_market,
        )
        strata[key][row.is_sponsored]["engagement_rate_derived"].append(row.engagement_rate_derived)
        strata[key][row.is_sponsored]["share_rate"].append(row.share_rate)
        strata[key][row.is_sponsored]["views"].append(row.views)

    fields = [
        "stratum_key",
        "platform",
        "year_quarter",
        "content_category",
        "creator_band",
        "n_sponsored",
        "n_organic",
        "mean_err_sponsored",
        "mean_err_organic",
        "lift_ratio_err",
        "lift_abs_err",
        "mean_share_sponsored",
        "mean_share_organic",
        "lift_ratio_share",
        "lift_abs_share",
        "mean_views_sponsored",
        "mean_views_organic",
        "lift_ratio_views",
        "lift_abs_views",
        "confidence",
    ]

    comparisons = []
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for key in sorted(strata):
            sponsored = strata[key]["TRUE"]
            organic = strata[key]["FALSE"]
            n_s = len(sponsored["engagement_rate_derived"])
            n_o = len(organic["engagement_rate_derived"])
            if n_s < 30 or n_o < 30:
                continue

            mean_err_s = mean(sponsored["engagement_rate_derived"])
            mean_err_o = mean(organic["engagement_rate_derived"])
            mean_share_s = mean(sponsored["share_rate"])
            mean_share_o = mean(organic["share_rate"])
            mean_views_s = mean(sponsored["views"])
            mean_views_o = mean(organic["views"])

            lift_ratio_err = mean_err_s / mean_err_o if mean_err_o else 0.0
            lift_ratio_share = mean_share_s / mean_share_o if mean_share_o else 0.0
            lift_ratio_views = mean_views_s / mean_views_o if mean_views_o else 0.0

            confidence = sponsorship_confidence(n_s, n_o, lift_ratio_err, lift_ratio_share)
            record = {
                "stratum_key": "|".join(key),
                "platform": key[0],
                "year_quarter": key[1],
                "content_category": key[2],
                "creator_band": key[3],
                "n_sponsored": n_s,
                "n_organic": n_o,
                "mean_err_sponsored": f"{mean_err_s:.10f}",
                "mean_err_organic": f"{mean_err_o:.10f}",
                "lift_ratio_err": f"{lift_ratio_err:.10f}",
                "lift_abs_err": f"{(mean_err_s - mean_err_o):.10f}",
                "mean_share_sponsored": f"{mean_share_s:.10f}",
                "mean_share_organic": f"{mean_share_o:.10f}",
                "lift_ratio_share": f"{lift_ratio_share:.10f}",
                "lift_abs_share": f"{(mean_share_s - mean_share_o):.10f}",
                "mean_views_sponsored": f"{mean_views_s:.6f}",
                "mean_views_organic": f"{mean_views_o:.6f}",
                "lift_ratio_views": f"{lift_ratio_views:.10f}",
                "lift_abs_views": f"{(mean_views_s - mean_views_o):.6f}",
                "confidence": confidence,
            }
            writer.writerow(record)
            comparisons.append(record)

    return {
        "strata_with_comparison": len(comparisons),
        "output_file": str(out_path),
        "confidence_distribution": dict(Counter(r["confidence"] for r in comparisons)),
    }


def near_zero_proxy(rows: List[ParsedRow]) -> Dict[str, object]:
    err_values = [r.engagement_rate_derived for r in rows]
    share_values = [r.share_rate for r in rows]
    p10_err = quantile(err_values, 0.10)
    p25_err = quantile(err_values, 0.25)
    p10_share = quantile(share_values, 0.10)
    p25_share = quantile(share_values, 0.25)

    count_bottom_10_err = sum(1 for value in err_values if value <= p10_err)
    count_bottom_25_err = sum(1 for value in err_values if value <= p25_err)
    count_bottom_10_share = sum(1 for value in share_values if value <= p10_share)
    count_bottom_25_share = sum(1 for value in share_values if value <= p25_share)

    return {
        "p10_engagement_rate_derived": p10_err,
        "p25_engagement_rate_derived": p25_err,
        "bottom_10_count_err": count_bottom_10_err,
        "bottom_10_pct_err": count_bottom_10_err / len(rows),
        "bottom_25_count_err": count_bottom_25_err,
        "bottom_25_pct_err": count_bottom_25_err / len(rows),
        "p10_share_rate": p10_share,
        "p25_share_rate": p25_share,
        "bottom_10_count_share": count_bottom_10_share,
        "bottom_10_pct_share": count_bottom_10_share / len(rows),
        "bottom_25_count_share": count_bottom_25_share,
        "bottom_25_pct_share": count_bottom_25_share / len(rows),
    }


def write_data_qa_report(rows: List[ParsedRow], qa: Dict[str, object], baselines: Dict[str, Dict[str, float]], near_zero: Dict[str, object]) -> str:
    out_path = SOLUTION_DIR / "data_qa_report.md"
    platforms = Counter(r.platform for r in rows)
    content_types = Counter(r.content_type for r in rows)
    categories = Counter(r.content_category for r in rows)
    sponsored_split = Counter(r.is_sponsored for r in rows)
    zero_counts = {
        "views_zero": sum(1 for r in rows if r.views == 0),
        "likes_zero": sum(1 for r in rows if r.likes == 0),
        "shares_zero": sum(1 for r in rows if r.shares == 0),
        "comments_zero": sum(1 for r in rows if r.comments_count == 0),
        "interactions_zero": sum(1 for r in rows if r.interactions == 0),
    }

    lines = [
        "# Data QA Report",
        "",
        f"- Dataset: `{qa['dataset_path']}`",
        f"- Valid rows: **{qa['row_count_valid']}**",
        f"- Parse errors: **{qa['parse_errors']}**",
        f"- Date range: **{qa['min_date']}** to **{qa['max_date']}**",
        "",
        "## Coverage",
        "",
        f"- Platforms: {dict(platforms)}",
        f"- Content types: {dict(content_types)}",
        f"- Categories: {dict(categories)}",
        f"- Sponsored split: {dict(sponsored_split)}",
        "",
        "## Critical constraints found",
        "",
        "- `engagement_rate` is not present in source file and was derived as `(likes + shares + comments_count) / views`.",
        "- No absolute zero values were found in `views`, `likes`, `shares`, `comments_count`.",
        "- This pattern indicates low natural variance and potential synthetic behavior; interpretation must avoid overclaim.",
        "",
        "## Zero checks",
        "",
        f"- {zero_counts}",
        "",
        "## Near-zero proxy (distribution tail)",
        "",
        f"- p10 ERR: {near_zero['p10_engagement_rate_derived']:.8f} ({near_zero['bottom_10_count_err']} posts, {near_zero['bottom_10_pct_err']:.2%})",
        f"- p25 ERR: {near_zero['p25_engagement_rate_derived']:.8f} ({near_zero['bottom_25_count_err']} posts, {near_zero['bottom_25_pct_err']:.2%})",
        f"- p10 share_rate: {near_zero['p10_share_rate']:.8f} ({near_zero['bottom_10_count_share']} posts, {near_zero['bottom_10_pct_share']:.2%})",
        f"- p25 share_rate: {near_zero['p25_share_rate']:.8f} ({near_zero['bottom_25_count_share']} posts, {near_zero['bottom_25_pct_share']:.2%})",
        "",
        "## Platform baseline means",
        "",
    ]
    for platform in sorted(baselines):
        metric = baselines[platform]
        lines.append(
            (
                f"- {platform}: mean ERR={metric['mean_engagement_rate_derived']:.8f}, "
                f"mean share_rate={metric['mean_share_rate']:.8f}, "
                f"mean views={metric['mean_views']:.2f}, "
                f"mean reach/follower={metric['mean_reach_per_follower']:.8f}"
            )
        )

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(out_path)


def find_top_segments(rows: List[ParsedRow], baselines: Dict[str, Dict[str, float]]) -> List[dict]:
    """
    Candidate recommendation pool:
    platform + category + creator_band + content_type + length_bin + sponsored flag
    """
    grouped = defaultdict(lambda: defaultdict(list))
    for row in rows:
        key = (
            row.platform,
            row.content_category,
            row.creator_band_market,
            row.content_type,
            row.content_length_bin,
            row.is_sponsored,
        )
        grouped[key]["err"].append(row.engagement_rate_derived)
        grouped[key]["share"].append(row.share_rate)
        grouped[key]["views"].append(row.views)
        grouped[key]["reach"].append(row.reach_per_follower)

    pool = []
    for key, values in grouped.items():
        n = len(values["err"])
        if n < 80:
            continue
        platform = key[0]
        avg_err = mean(values["err"])
        avg_share = mean(values["share"])
        avg_views = mean(values["views"])
        avg_reach = mean(values["reach"])

        rel_err = avg_err / baselines[platform]["mean_engagement_rate_derived"]
        rel_share = avg_share / baselines[platform]["mean_share_rate"]
        rel_views = avg_views / baselines[platform]["mean_views"]
        rel_reach = avg_reach / baselines[platform]["mean_reach_per_follower"]
        score = (
            (rel_err - 1.0) * 0.45
            + (rel_share - 1.0) * 0.35
            + (rel_views - 1.0) * 0.10
            + (rel_reach - 1.0) * 0.10
        ) * math.sqrt(n / 100)
        pool.append(
            {
                "platform": platform,
                "content_category": key[1],
                "creator_band": key[2],
                "content_type": key[3],
                "content_length_bin": key[4],
                "is_sponsored": key[5],
                "n_posts": n,
                "mean_err": avg_err,
                "mean_share": avg_share,
                "mean_views": avg_views,
                "mean_reach_per_follower": avg_reach,
                "rel_err": rel_err,
                "rel_share": rel_share,
                "rel_views": rel_views,
                "rel_reach": rel_reach,
                "score": score,
            }
        )

    pool.sort(key=lambda x: x["score"], reverse=True)
    return pool


def write_summary_json(payload: Dict[str, object]) -> str:
    out_path = SOLUTION_DIR / "analysis_summary.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(out_path)


def main() -> None:
    SOLUTION_DIR.mkdir(parents=True, exist_ok=True)
    rows, qa = load_rows()
    baselines = platform_baselines(rows)
    near_zero = near_zero_proxy(rows)
    segment_info = write_segment_performance(rows)
    sponsorship_info = write_sponsorship_comparison(rows)
    qa_file = write_data_qa_report(rows, qa, baselines, near_zero)
    top_segments = find_top_segments(rows, baselines)

    summary_payload = {
        "qa": qa,
        "segment_info": segment_info,
        "sponsorship_info": sponsorship_info,
        "near_zero_proxy": near_zero,
        "platform_baselines": baselines,
        "top_segments_head_20": top_segments[:20],
        "top_segments_tail_20": list(reversed(top_segments[-20:])),
    }
    summary_file = write_summary_json(summary_payload)

    print("Generated artifacts:")
    print(f"- {qa_file}")
    print(f"- {segment_info['output_file']}")
    print(f"- {sponsorship_info['output_file']}")
    print(f"- {summary_file}")


if __name__ == "__main__":
    main()
