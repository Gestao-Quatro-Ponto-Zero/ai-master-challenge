#!/usr/bin/env python3
"""Freeze label-balanced, whole-component IT splits without fitting a classifier.

Exact prefix/length filtering followed by Jaccard verification, not LSH.
Reference: https://www.vldb.org/pvldb/vol9/p636-mann.pdf, section 2.
"""

import argparse
from collections import Counter, defaultdict, deque
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import platform
import re


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("evaluation_audit", Path(__file__).with_name("audit_data.py"))
AUDIT = importlib.util.module_from_spec(spec)
spec.loader.exec_module(AUDIT)
PARTITIONS = ("train", "validation", "final_test")


class Components:
    def __init__(self, size):
        self.parent = list(range(size))

    def find(self, item):
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left, right):
        a, b = self.find(left), self.find(right)
        if a != b:
            self.parent[max(a, b)] = min(a, b)


def jaccard_pairs(sets, numerator=17, denominator=20):
    """Yield all qualifying nonempty set pairs using safe prefix/length filters."""
    if not 0 < numerator <= denominator:
        raise ValueError("Jaccard threshold must be in (0,1]")
    frequency = Counter(token for tokens in sets for token in tokens)
    order = {token: i for i, token in enumerate(sorted(frequency, key=lambda token: (frequency[token], token)))}
    index = defaultdict(deque)
    for i in sorted(range(len(sets)), key=lambda i: (len(sets[i]), i)):
        tokens = sets[i]
        if not tokens:
            continue
        lower = (numerator * len(tokens) + denominator - 1) // denominator
        prefix = sorted(tokens, key=order.__getitem__)[:len(tokens) - lower + 1]
        candidates = set()
        for token in prefix:
            posting = index[token]
            while posting and len(sets[posting[0]]) < lower:
                posting.popleft()
            candidates.update(posting)
        for j in sorted(candidates):
            intersection = len(tokens & sets[j])
            union = len(tokens) + len(sets[j]) - intersection
            if denominator * intersection >= numerator * union:
                yield j, i
        for token in prefix:
            index[token].append(i)


def group_rows(rows, config, source_hash):
    normalized = [AUDIT.normalize(row["Document"]) for row in rows]
    tokens = [frozenset(re.findall(config["split"]["token_pattern"], text)) for text in normalized]
    components = Components(len(rows))
    exact = defaultdict(list)
    same_set = defaultdict(list)
    invalid = set()
    for i, (row, text, token_set) in enumerate(zip(rows, normalized, tokens)):
        exact[text].append(i)
        same_set[token_set].append(i)
        if not text or not token_set or max(len(row["Document"]), len(text)) > config["max_input_chars"]:
            invalid.add(i)
    conflicts = set()
    for ids in exact.values():
        if len({rows[i]["Topic_group"] for i in ids}) > 1:
            conflicts.update(ids)
    representative_ids = []
    representative_sets = []
    pair_count = 0
    for token_set, ids in same_set.items():
        for i in ids[1:]:
            components.union(ids[0], i)
        if token_set:
            representative_ids.append(ids[0])
            representative_sets.append(token_set)
            pair_count += len(ids) * (len(ids) - 1) // 2
    verified_edges = []
    for a, b in jaccard_pairs(representative_sets,
                              config["split"]["near_duplicate_jaccard_numerator"],
                              config["split"]["near_duplicate_jaccard_denominator"]):
        left, right = representative_ids[a], representative_ids[b]
        components.union(left, right)
        pair_count += len(same_set[tokens[left]]) * len(same_set[tokens[right]])
        verified_edges.append((left, right))
    grouped = defaultdict(list)
    for i in range(len(rows)):
        grouped[components.find(i)].append(i)
    groups = []
    for ids in grouped.values():
        payload = source_hash + ":" + ",".join(str(i + 1) for i in ids)
        groups.append({"id": hashlib.sha256(payload.encode()).hexdigest(), "rows": ids,
                       "labels": Counter(rows[i]["Topic_group"] for i in ids),
                       "quarantine": bool(set(ids) & (invalid | conflicts))})
    return groups, normalized, {"qualifying_row_pairs": pair_count, "verified_representative_edges": len(verified_edges),
                                "invalid_input_rows": len(invalid), "exact_conflicting_rows": len(conflicts)}, verified_edges


def allocate(groups, fractions, seed):
    usable = [group for group in groups if not group["quarantine"]]
    labels = sorted({label for group in usable for label in group["labels"]})
    totals = Counter()
    for group in usable:
        totals.update(group["labels"])
    current = {part: Counter() for part in PARTITIONS}
    assignment = {}
    tie = lambda group: hashlib.sha256((seed + group["id"]).encode()).hexdigest()
    for group in sorted(usable, key=lambda group: (-len(group["rows"]), tie(group))):
        def delta(part):
            # Increment of normalized squared class-count imbalance.
            return sum(((current[part][label] + group["labels"][label] - totals[label] * fractions[part]) ** 2 -
                        (current[part][label] - totals[label] * fractions[part]) ** 2) /
                       (totals[label] * fractions[part] + 1) for label in labels)
        part = min(PARTITIONS, key=lambda part: (delta(part), PARTITIONS.index(part)))
        assignment[group["id"]] = part
        current[part].update(group["labels"])
    for group in groups:
        if group["quarantine"]:
            assignment[group["id"]] = "quarantine"
    return assignment


def prepare(root=ROOT):
    config_path = root / "data/evaluation-protocol.json"
    config = json.loads(config_path.read_text())
    fractions = config["split"]["fractions"]
    if set(fractions) != set(PARTITIONS) or any(v <= 0 for v in fractions.values()) or not math.isclose(sum(fractions.values()), 1):
        raise ValueError("Expected positive train/validation/final_test fractions summing to one")
    manifest = json.loads((root / "data/manifest.json").read_text())
    entry = manifest["datasets"]["it_service"]["file"]
    path = (root / entry["path"]).resolve()
    if not path.is_relative_to(root.resolve()) or AUDIT.sha256(path) != entry["sha256"]:
        raise ValueError("IT input path/hash differs from manifest")
    rows = AUDIT.read_csv(path, ["Document", "Topic_group"])
    groups, normalized, diagnostics, edges = group_rows(rows, config, entry["sha256"])
    assignment = allocate(groups, fractions, config["split"]["seed"])
    membership = []
    for group in groups:
        for i in group["rows"]:
            membership.append({"row_index": i + 1, "case_id": f"it:{entry['sha256'][:12]}:{i + 1}",
                               "group_id": group["id"], "partition": assignment[group["id"]],
                               "normalized_text_sha256": hashlib.sha256(normalized[i].encode()).hexdigest()})
    membership.sort(key=lambda row: row["row_index"])
    lookup = {row["row_index"] - 1: row["partition"] for row in membership}
    assert all(lookup[left] == lookup[right] for left, right in edges)
    counts = {part: Counter(rows[i]["Topic_group"] for i in range(len(rows)) if lookup[i] == part)
              for part in (*PARTITIONS, "quarantine")}
    labels = sorted({row["Topic_group"] for row in rows})
    if len(labels) != 8 or any(counts[part][label] == 0 for part in PARTITIONS for label in labels):
        raise ValueError("Each IT partition must support all eight classes; review groups before freezing")
    result = {
        "schema_version": 1, "protocol_id": config["protocol_id"], "python": platform.python_version(),
        "input_sha256": {"data/manifest.json": AUDIT.sha256(root / "data/manifest.json"),
                         entry["path"]: AUDIT.sha256(path), "data/evaluation-protocol.json": AUDIT.sha256(config_path),
                         "solution/prepare_evaluation.py": AUDIT.sha256(Path(__file__)),
                         "solution/audit_data.py": AUDIT.sha256(Path(__file__).with_name("audit_data.py"))},
        "raw_rows": len(rows), "groups": len(groups), "non_singleton_groups": sum(len(g["rows"]) > 1 for g in groups),
        "largest_group": max(map(lambda g: len(g["rows"]), groups), default=0),
        "groups_with_multiple_labels": sum(len(g["labels"]) > 1 for g in groups),
        "partition_rows": {part: sum(count.values()) for part, count in counts.items()},
        "partition_groups": dict(Counter(assignment.values())),
        "partition_class_counts": {part: dict(sorted(count.items())) for part, count in counts.items()},
        "diagnostics": diagnostics,
        "invariants": {"all_rows_assigned_once": len(membership) == len(rows), "whole_groups": True,
                       "verified_near_edges_cross_partitions": 0, "all_eight_classes_in_each_partition": True},
        "limits": ["Exact grouping for the declared token-set similarity, not proof of semantic/entity independence",
                   "Token order/repetition ignored for grouping; conservative transitive components may contain different labels",
                   "Global token frequencies used only for label-blind duplicate grouping, not fitted model features",
                   "Membership/class support inspection is data preparation; no classifier, threshold or test performance evaluated"],
    }
    return result, membership


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/evaluation-manifest.json")
    parser.add_argument("--membership", type=Path, default=ROOT / "data/processed/evaluation-membership.csv")
    args = parser.parse_args()
    result, membership = prepare()
    args.membership.parent.mkdir(parents=True, exist_ok=True)
    with args.membership.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(membership[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(membership)
    result["membership"] = {"path": "data/processed/evaluation-membership.csv", "rows": len(membership),
                            "bytes": args.membership.stat().st_size, "sha256": AUDIT.sha256(args.membership)}
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps({"rows": result["partition_rows"], "groups": result["groups"],
                      "largest_group": result["largest_group"], "near_pairs": result["diagnostics"]["qualifying_row_pairs"]}, indent=2))
