"""Build the timed-trial data: 40 unseen test tickets in two matched arms.

The whole design (sample, arms, order) is fixed by a seed, so the trial can be
audited and repeated. The participant sees no feedback during the trial, so the
labels only appear at the end.

Usage: python build_trial_data.py [--data DIR] [--out FILE]
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

import triage_model as tm

HERE = Path(__file__).resolve().parent
TOTAL = 40
MIN_WORDS, MAX_WORDS = 15, 70  # readable in seconds, so 40 tickets fit in about half an hour


def stratified_counts(shares: dict[str, float]) -> dict[str, int]:
    """Proportional to the test mix, with at least 2 per category so both arms see it."""
    counts = {category: max(2, round(share * TOTAL)) for category, share in shares.items()}
    order = sorted(counts, key=lambda category: -shares[category])
    while sum(counts.values()) > TOTAL:
        biggest = max((c for c in order if counts[c] > 2), key=lambda c: counts[c])
        counts[biggest] -= 1
    while sum(counts.values()) < TOTAL:
        counts[order[0]] += 1
    return counts


def top_words(model: tm.TriageModel, text: str, class_index: int, k: int = 4) -> list[str]:
    row = model.vectorizer.transform([text])
    names = model.vectorizer.get_feature_names_out()
    weights = sorted(
        ((model.classifier.coef_[class_index, i] * row[0, i], i) for i in row.nonzero()[1]),
        reverse=True,
    )
    return [names[i] for weight, i in weights[:k] if weight > 0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=HERE.parent / "data", type=Path)
    parser.add_argument("--out", default=HERE.parent / "app" / "ensaio_data.js", type=Path)
    args = parser.parse_args()

    tickets = tm.load_it_tickets(args.data)
    train, validation, test = tm.split_by_order(tickets)
    model = tm.train_model(train, validation)

    pool = test.assign(words=test["Document"].str.split().str.len())
    pool = pool[(pool["words"] >= MIN_WORDS) & (pool["words"] <= MAX_WORDS)]
    counts = stratified_counts(pool["Topic_group"].value_counts(normalize=True).to_dict())

    selections: list[tuple[str, str]] = []
    chosen_index: list = []
    for category in sorted(counts):
        group = pool[pool["Topic_group"] == category]
        sampled = group.sample(n=min(counts[category], len(group)), random_state=0)
        chosen_index.extend(sampled.index)
        selections.extend((text, category) for text in sampled["Document"])
    missing = TOTAL - len(selections)
    if missing > 0:
        extra = pool.drop(index=chosen_index).sample(n=missing, random_state=1)
        selections.extend(zip(extra["Document"], extra["Topic_group"]))

    # Arms alternate inside each category, so both arms get the same mix.
    selections.sort(key=lambda item: item[1])
    arm_sizes = {"manual": 0, "assistido": 0}
    rows = []
    for text, label in selections:
        probabilities = model.probabilities(pd.Series([text]))[0]
        class_index = int(np.argmax(probabilities))
        arm = "manual" if arm_sizes["manual"] <= arm_sizes["assistido"] else "assistido"
        arm_sizes[arm] += 1
        rows.append(
            {
                "text": text,
                "label": label,
                "arm": arm,
                "predicted": str(model.categories[class_index]),
                "confidence": round(float(probabilities[class_index]), 4),
                "words": top_words(model, text, class_index),
            }
        )
    rng = np.random.default_rng(0)
    rng.shuffle(rows)
    assert len(rows) == TOTAL and arm_sizes == {"manual": TOTAL // 2, "assistido": TOTAL // 2}

    payload = {
        "design": {
            "total": TOTAL,
            "perArm": TOTAL // 2,
            "seed": 0,
            "minWords": MIN_WORDS,
            "maxWords": MAX_WORDS,
            "metric": "mediana de segundos por ticket, por braço; secundárias: acerto e uso da sugestão",
        },
        "categories": model.categories.tolist(),
        "tickets": rows,
    }
    args.out.write_text("window.ENSAIO_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(dict(Counter(row["arm"] for row in rows)), dict(Counter(row["label"] for row in rows)))


if __name__ == "__main__":
    main()
