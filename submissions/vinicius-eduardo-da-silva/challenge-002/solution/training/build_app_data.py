"""Generate the files that let the prototype run in a browser with no server.

app/model.js holds the trained model, and app/data.js holds the results and test tickets.
Usage: python build_app_data.py [--data DIR] [--results FILE] [--app DIR]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import triage_model as tm

HERE = Path(__file__).resolve().parent
SAMPLE_TICKETS = 400
SAMPLE_CUSTOMER_TICKETS = 60
TEXT_LIMIT = 500


def export_model(model: tm.TriageModel) -> dict:
    words = model.vectorizer.get_feature_names_out()
    return {
        "categories": model.categories.tolist(),
        "words": words.tolist(),
        "idf": np.round(model.vectorizer.idf_, 4).tolist(),
        "coef": np.round(model.classifier.coef_.T, 4).tolist(),
        "intercept": np.round(model.classifier.intercept_, 4).tolist(),
        "guard": model.guard,
        "routeConfidence": tm.ROUTE_CONFIDENCE,
        "suggestConfidence": tm.SUGGEST_CONFIDENCE,
        "sensitiveWords": sorted(tm.SENSITIVE_WORDS),
        "neverRoute": sorted(tm.NEVER_ROUTE_CATEGORIES),
    }


def sample_rows(frame: pd.DataFrame, texts: pd.Series, labels: pd.Series | None, size: int) -> list[dict]:
    chosen = frame.sample(n=min(size, len(frame)), random_state=0)
    rows = []
    for index, row in chosen.iterrows():
        rows.append(
            {
                "text": str(texts.loc[index])[:TEXT_LIMIT],
                "label": None if labels is None else labels.loc[index],
                "predicted": row["predicted"],
                "confidence": round(float(row["confidence"]), 4),
                "lane": row["lane"],
                "reason": row["reason"],
                "fullText": len(str(texts.loc[index])) <= TEXT_LIMIT,
            }
        )
    return rows


def pick_example(frame: pd.DataFrame, texts: pd.Series, mask: pd.Series, max_words: int = 45) -> str:
    short = texts.str.split().str.len() <= max_words
    candidates = frame[mask & short]
    return str(texts.loc[candidates.sample(n=1, random_state=1).index[0]])


def build_examples(test_frame, test_text, support_frame, support_text) -> list[dict]:
    return [
        {"label": "Ticket claro de TI", "text": pick_example(test_frame, test_text, (test_frame["lane"] == tm.ROUTE) & (test_frame["confidence"] > 0.98))},
        {"label": "Ticket ambíguo", "text": pick_example(test_frame, test_text, test_frame["reason"] == "confianca_media")},
        {"label": "Assunto sensível", "text": pick_example(test_frame, test_text, test_frame["reason"] == "sensivel", 80)},
        {"label": "Acesso de administrador", "text": pick_example(test_frame, test_text, test_frame["reason"] == "categoria_protegida")},
        {"label": "Ticket de cliente", "text": pick_example(support_frame, support_text, support_frame["reason"] == "desconhecido", 70)},
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=HERE.parent / "data", type=Path)
    parser.add_argument("--results", default=HERE / "results.json", type=Path)
    parser.add_argument("--app", default=HERE.parent / "app", type=Path)
    args = parser.parse_args()

    tickets = tm.load_it_tickets(args.data)
    support = tm.load_support_tickets(args.data)
    train, validation, test = tm.split_by_order(tickets)
    model = tm.train_model(train, validation)
    test_frame = tm.triage_frame(model, test["Document"])
    support_text = support["Ticket Description"].fillna("")
    support_frame = tm.triage_frame(model, support_text)

    categories = model.categories.tolist()
    index_of = {name: i for i, name in enumerate(categories)}
    # One compact row per test ticket: the threshold slider recomputes the policy from these.
    replay = [
        [round(float(c), 4), index_of[p], index_of[y], int(k >= model.guard), int(s)]
        for c, p, y, k, s in zip(test_frame["confidence"], test_frame["predicted"], test["Topic_group"], test_frame["known"], test_frame["sensitive"])
    ]
    payload = {
        "results": json.loads(args.results.read_text(encoding="utf-8")),
        "replay": replay,
        "samples": sample_rows(test_frame, test["Document"], test["Topic_group"], SAMPLE_TICKETS),
        "customerSamples": sample_rows(support_frame, support_text, None, SAMPLE_CUSTOMER_TICKETS),
        "examples": build_examples(test_frame, test["Document"], support_frame, support_text),
    }
    (args.app / "model.js").write_text("window.TRIAGE_MODEL = " + json.dumps(export_model(model), ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    (args.app / "data.js").write_text("window.TRIAGE_DATA = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print({name: len(row["text"]) for name, row in zip(["route", "suggest", "sensitive", "protected", "customer"], payload["examples"])})


if __name__ == "__main__":
    main()
