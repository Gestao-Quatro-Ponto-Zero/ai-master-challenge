"""Every number shown in the prototype and the report comes from here.

Usage: python evaluate.py [--data DIR] [--out FILE]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import cross_val_score

import triage_model as tm

HERE = Path(__file__).resolve().parent
PERMUTATIONS = 2000
COMBO_KEYS = ["Ticket Channel", "Ticket Priority", "Ticket Type"]


def lane_summary(frame: pd.DataFrame, labels: pd.Series) -> dict:
    right = frame["predicted"].to_numpy() == labels.to_numpy()
    second = frame["second"].to_numpy() == labels.to_numpy()
    summary = {}
    for lane in (tm.ROUTE, tm.SUGGEST, tm.HUMAN):
        in_lane = frame["lane"].to_numpy() == lane
        summary[lane] = {
            "share": round(float(in_lane.mean()), 4),
            "accuracy": round(float(right[in_lane].mean()), 4) if in_lane.any() else None,
            "top2": round(float((right | second)[in_lane].mean()), 4) if in_lane.any() else None,
        }
    summary["reasons"] = {key: round(float(value), 4) for key, value in frame["reason"].value_counts(normalize=True).items()}
    return summary


def category_table(frame: pd.DataFrame, labels: pd.Series) -> list[dict]:
    rows = []
    actual, predicted = labels.to_numpy(), frame["predicted"].to_numpy()
    routed = frame["lane"].to_numpy() == tm.ROUTE
    for category in sorted(set(actual)):
        in_class = actual == category
        routed_as = routed & (predicted == category)
        rows.append(
            {
                "category": category,
                "tickets": int(in_class.sum()),
                "recall": round(float((predicted[in_class] == category).mean()), 3),
                "routedShare": round(float(routed[in_class].mean()), 3),
                "routedPrecision": round(float((actual[routed_as] == category).mean()), 3) if routed_as.any() else None,
            }
        )
    return rows


def threshold_curve(frame: pd.DataFrame, labels: pd.Series, guard_on: np.ndarray) -> list[dict]:
    right = frame["predicted"].to_numpy() == labels.to_numpy()
    rows = []
    for threshold in np.arange(0.5, 1.0, 0.05):
        keep = (frame["confidence"].to_numpy() >= threshold) & guard_on
        rows.append({"threshold": round(float(threshold), 2), "coverage": round(float(keep.mean()), 4), "accuracy": round(float(right[keep].mean()), 4)})
    return rows


def random_split_baseline(tickets: pd.DataFrame) -> dict:
    """The optimistic number that a random split would report, kept for comparison."""
    from sklearn.model_selection import train_test_split

    train, test = train_test_split(tickets, test_size=0.2, random_state=0, stratify=tickets["Topic_group"])
    model = tm.train_model(train, train.iloc[:1000])
    return {"accuracy": round(float((model.probabilities(test["Document"]).argmax(axis=1) == model.categories.searchsorted(test["Topic_group"])).mean()), 4)}


def drift_blocks(tickets: pd.DataFrame) -> list[dict]:
    """Train on earlier rows and test on the next tenth of the file."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression

    blocks = pd.cut(np.arange(len(tickets)), 10, labels=False)
    rows = []
    for end in range(3, 10):
        train, test = tickets[blocks < end], tickets[blocks == end]
        vectorizer = TfidfVectorizer(sublinear_tf=True, max_features=tm.VOCABULARY_SIZE)
        classifier = LogisticRegression(max_iter=400, C=10).fit(vectorizer.fit_transform(train["Document"]), train["Topic_group"])
        predicted = classifier.predict(vectorizer.transform(test["Document"]))
        rows.append({"block": end + 1, "accuracy": round(float((predicted == test["Topic_group"]).mean()), 3), "hardwareShare": round(float((test["Topic_group"] == "Hardware").mean()), 3)})
    return rows


def support_diagnosis(support: pd.DataFrame) -> dict:
    rng = np.random.default_rng(0)
    frame = support.copy()
    frame["first"] = pd.to_datetime(frame["First Response Time"], errors="coerce")
    frame["end"] = pd.to_datetime(frame["Time to Resolution"], errors="coerce")
    frame["hours"] = (frame["end"] - frame["first"]).dt.total_seconds() / 3600
    frame["rating"] = frame["Customer Satisfaction Rating"]
    closed = frame[frame["hours"].notna()]
    valid = closed[closed["hours"] > 0]

    combos = valid.groupby(COMBO_KEYS)["hours"].agg(["mean", "size"]).sort_values("mean")
    observed = float(combos["mean"].max() - combos["mean"].min())
    groups = [valid[key].to_numpy() for key in COMBO_KEYS]
    gaps = []
    for _ in range(PERMUTATIONS):
        means = pd.Series(rng.permutation(valid["hours"].to_numpy())).groupby(groups).mean()
        gaps.append(float(means.max() - means.min()))
    gaps = np.array(gaps)
    counts, edges = np.histogram(gaps, bins=12)

    rated = frame[frame["rating"].notna()]
    features = rated[COMBO_KEYS + ["Ticket Subject", "Customer Gender", "Product Purchased"]].apply(lambda c: c.astype("category").cat.codes)
    features = features.assign(hours=rated["hours"], age=rated["Customer Age"])
    regressor = HistGradientBoostingRegressor(max_depth=3, max_iter=80)
    p_values = {key: float(stats.f_oneway(*[g["rating"].to_numpy() for _, g in rated.groupby(key)]).pvalue) for key in COMBO_KEYS + ["Ticket Subject", "Customer Gender", "Product Purchased"]}

    hours_hist, hours_edges = np.histogram(closed["hours"], bins=np.arange(-24, 25, 6))
    worst, best = combos.iloc[-1], combos.iloc[0]
    rating_counts = rated["rating"].value_counts().sort_index()
    return {
        "rows": len(frame),
        "statusShares": frame["Ticket Status"].value_counts(normalize=True).round(3).to_dict(),
        "closed": len(closed),
        "negativeShare": round(float((closed["hours"] < 0).mean()), 3),
        "firstResponseSpanHours": round(float((frame["first"].max() - frame["first"].min()).total_seconds() / 3600), 1),
        "hoursHistogram": [{"from": int(hours_edges[i]), "to": int(hours_edges[i + 1]), "count": int(hours_hist[i])} for i in range(len(hours_hist))],
        "bottleneck": {
            "worst": {"name": " + ".join(combos.index[-1]), "hours": round(float(worst["mean"]), 1), "tickets": int(worst["size"])},
            "best": {"name": " + ".join(combos.index[0]), "hours": round(float(best["mean"]), 1), "tickets": int(best["size"])},
            "observedGap": round(observed, 2),
            "shuffledMean": round(float(gaps.mean()), 2),
            "pValue": round(float((gaps >= observed).mean()), 3),
            "histogram": [{"from": round(float(edges[i]), 1), "to": round(float(edges[i + 1]), 1), "count": int(counts[i])} for i in range(len(counts))],
        },
        "satisfaction": {
            "distribution": {str(int(k)): int(v) for k, v in rating_counts.items()},
            "uniformP": round(float(stats.chisquare(rating_counts).pvalue), 3),
            "smallestP": round(min(p_values.values()), 3),
            "testsRun": len(p_values),
            "r2": round(float(cross_val_score(regressor, features, rated["rating"], cv=5, scoring="r2").mean()), 3),
            "r2Shuffled": round(float(cross_val_score(regressor, features, rng.permutation(rated["rating"].to_numpy()), cv=5, scoring="r2").mean()), 3),
            "hoursCorrelation": round(float(stats.pearsonr(rated["hours"], rated["rating"])[0]), 3),
        },
        "text": {
            "placeholderShare": round(float(frame["Ticket Description"].str.contains(r"\{product_purchased\}").mean()), 3),
            "exampleResolution": closed["Resolution"].iloc[1],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=HERE.parent / "data", type=Path)
    parser.add_argument("--out", default=HERE / "results.json", type=Path)
    args = parser.parse_args()

    tickets = tm.load_it_tickets(args.data)
    support = tm.load_support_tickets(args.data)
    train, validation, test = tm.split_by_order(tickets)
    model = tm.train_model(train, validation)

    test_frame = tm.triage_frame(model, test["Document"])
    support_frame = tm.triage_frame(model, support["Ticket Description"])
    labels = test["Topic_group"]
    right = test_frame["predicted"].to_numpy() == labels.to_numpy()
    guard_on = test_frame["known"].to_numpy() >= model.guard
    routed = test_frame["lane"].to_numpy() == tm.ROUTE

    results = {
        "tickets": {"it": len(tickets), "train": len(train), "validation": len(validation), "test": len(test)},
        "guard": round(model.guard, 4),
        "routeConfidence": tm.ROUTE_CONFIDENCE,
        "suggestConfidence": tm.SUGGEST_CONFIDENCE,
        "accuracy": {
            "randomSplit": random_split_baseline(tickets)["accuracy"],
            "orderSplit": round(float(right.mean()), 4),
            "majority": round(float(labels.value_counts(normalize=True).iloc[0]), 4),
        },
        "lanes": lane_summary(test_frame, labels),
        "routedErrorsPer100": round(float((1 - right[routed].mean()) * 100), 1),
        "categories": category_table(test_frame, labels),
        "thresholds": threshold_curve(test_frame, labels, guard_on),
        "drift": drift_blocks(tickets),
        "transfer": {
            "tickets": len(support),
            "guardBlocked": round(float((support_frame["known"] < model.guard).mean()), 4),
            "itGuardBlocked": round(float((test_frame["known"] < model.guard).mean()), 4),
            "routedWithoutGuard": round(float((support_frame["confidence"] >= tm.ROUTE_CONFIDENCE).mean()), 4),
            "routedWithGuard": round(float((support_frame["lane"] == tm.ROUTE).mean()), 4),
            "hardwareShare": round(float((support_frame["predicted"] == "Hardware").mean()), 4),
            "byType": pd.crosstab(support["Ticket Type"], support_frame["predicted"], normalize="index")["Hardware"].round(3).to_dict(),
            "lanes": {lane: round(float((support_frame["lane"] == lane).mean()), 4) for lane in (tm.ROUTE, tm.SUGGEST, tm.HUMAN)},
        },
        "support": support_diagnosis(support),
    }
    args.out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
