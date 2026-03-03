#!/usr/bin/env python3
"""Validation checks for submission artifacts."""

from __future__ import annotations

import csv
import re
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path("/Users/lenon/Programas em Desenvolvimento/Challenges/ai-master-challenge")
SUB = ROOT / "submissions" / "lenon-cardozo"
SOL = SUB / "solution"
DATA = Path("/Users/lenon/Downloads/social_media_dataset.csv")


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def check_dataset_integrity(results):
    rows = read_csv(DATA)
    required = {
        "platform",
        "content_type",
        "content_category",
        "post_date",
        "views",
        "likes",
        "shares",
        "comments_count",
        "follower_count",
        "is_sponsored",
    }
    missing = sorted(required - set(rows[0].keys()))
    valid_dates = 0
    for row in rows:
        try:
            datetime.strptime(row["post_date"], "%m/%d/%y %I:%M %p")
            valid_dates += 1
        except Exception:
            pass
    results.append(
        (
            "Dataset integrity",
            len(missing) == 0 and valid_dates == len(rows),
            f"rows={len(rows)}, valid_dates={valid_dates}, missing_columns={missing}",
        )
    )
    return rows


def check_formula_reproducibility(rows, results):
    failed = 0
    for row in rows[:2000]:
        views = float(row["views"])
        likes = float(row["likes"])
        shares = float(row["shares"])
        comments = float(row["comments_count"])
        derived = (likes + shares + comments) / views if views else 0.0
        if derived <= 0:
            failed += 1
    results.append(
        (
            "Derived formula reproducibility",
            failed == 0,
            f"sample_checked=2000, non_positive_results={failed}",
        )
    )


def check_segmentation_consistency(rows, results):
    seg_rows = read_csv(SOL / "segment_performance.csv")
    seg_total = sum(int(r["n_posts"]) for r in seg_rows)
    results.append(
        (
            "Segmentation consistency",
            seg_total == len(rows),
            f"segment_total={seg_total}, dataset_rows={len(rows)}",
        )
    )


def check_robustness_threshold(results):
    # Evidence segments used in recommendations and expected minimum n>=80.
    required_segments = [
        ("YouTube", "FALSE", "beauty", "50k-200k", "video", "120s+", 80),
        ("Instagram", "FALSE", "lifestyle", "50k-200k", "video", "120s+", 80),
        ("TikTok", "2024-Q4", "beauty", "50k-200k", None, None, 80),
    ]

    # Tactical counts from source
    tactical_counts = Counter()
    core_counts = Counter()

    with DATA.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            followers = float(row["follower_count"])
            if followers < 10_000:
                band = "<10k"
            elif followers < 50_000:
                band = "10k-50k"
            elif followers < 200_000:
                band = "50k-200k"
            elif followers < 500_000:
                band = "200k-500k"
            else:
                band = "500k+"

            length = float(row["content_length"])
            if length < 15:
                lbin = "<15s"
            elif length < 30:
                lbin = "15-29s"
            elif length < 60:
                lbin = "30-59s"
            elif length < 120:
                lbin = "60-119s"
            else:
                lbin = "120s+"

            dt = datetime.strptime(row["post_date"], "%m/%d/%y %I:%M %p")
            quarter = f"{dt.year}-Q{(dt.month - 1) // 3 + 1}"

            tactical_key = (
                row["platform"],
                row["is_sponsored"],
                row["content_category"],
                band,
                row["content_type"],
                lbin,
            )
            core_key = (
                row["platform"],
                quarter,
                row["content_category"],
                band,
            )
            tactical_counts[tactical_key] += 1
            core_counts[core_key] += 1

    failing = []
    for segment in required_segments:
        min_n = segment[6]
        if segment[4] is None:
            n = core_counts[(segment[0], segment[1], segment[2], segment[3])]
        else:
            n = tactical_counts[(segment[0], segment[1], segment[2], segment[3], segment[4], segment[5])]
        if n < min_n:
            failing.append((segment, n))

    results.append(
        (
            "Robustness threshold on referenced segments",
            len(failing) == 0,
            f"failed={failing if failing else 'none'}",
        )
    )


def check_anti_survivorship(results):
    qa_text = (SOL / "data_qa_report.md").read_text(encoding="utf-8")
    has_p25 = "p25 ERR" in qa_text and "p25 share_rate" in qa_text
    has_zero_check = "Zero checks" in qa_text
    results.append(
        (
            "Anti-survivorship evidence present",
            has_p25 and has_zero_check,
            f"has_p25={has_p25}, has_zero_check={has_zero_check}",
        )
    )


def check_traceability(results):
    recommendations = read_csv(SOL / "recommendations.csv")
    evidence_text = (SOL / "evidence_register.md").read_text(encoding="utf-8")
    evidence_ids = set(re.findall(r"EVID-\d+", evidence_text))
    missing = []
    for row in recommendations:
        ids = [item.strip() for item in row["evidence_reference"].split("|")]
        for evidence_id in ids:
            if evidence_id not in evidence_ids:
                missing.append((row["recommendation_id"], evidence_id))
    results.append(
        (
            "Recommendation traceability",
            len(missing) == 0,
            f"missing_refs={missing if missing else 'none'}",
        )
    )


def check_executive_structure(results):
    brief = (SOL / "executive_brief.md").read_text(encoding="utf-8")
    expected_sections = [
        "## 1. Executive Summary",
        "## 2. Key Insights",
        "## 3. Evidence",
        "## 4. Risks & Bias Checks",
        "## 5. Strategic Recommendations",
        "## 6. Open Questions",
    ]
    missing = [title for title in expected_sections if title not in brief]
    results.append(
        (
            "Executive output structure",
            len(missing) == 0,
            f"missing_sections={missing if missing else 'none'}",
        )
    )


def write_report(results):
    out = SOL / "validation_report.md"
    lines = ["# Validation Report", ""]
    passed = 0
    for name, ok, detail in results:
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        lines.append(f"- **{status}** — {name}: {detail}")
    lines.append("")
    lines.append(f"Summary: {passed}/{len(results)} checks passed.")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    results = []
    rows = check_dataset_integrity(results)
    check_formula_reproducibility(rows, results)
    check_segmentation_consistency(rows, results)
    check_robustness_threshold(results)
    check_anti_survivorship(results)
    check_traceability(results)
    check_executive_structure(results)
    write_report(results)
    for name, ok, detail in results:
        print(("PASS" if ok else "FAIL"), "-", name, "-", detail)


if __name__ == "__main__":
    main()
