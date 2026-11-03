"""Export the data the prototype page needs, so it runs without the Kaggle datasets (challenge 002). Local, no API.

Reads the model bundle built by script 007 and Dataset 2, and writes to results/:
  011-triage-train-tickets.csv.gz  training texts and labels; the page refits the same model from them
  012-triage-test-tickets.csv.gz   the held-out test tickets, in the order the page draws them
  013-triage-settings.json         threshold, minimum words and the standardized openings
Then refits the model from the exported files, exactly as the page does, and checks it against the bundle's model
and against results/007 on every test ticket.

Usage:
  python 010-triage-demo-data.py <csv> [--cache-dir DIR] [--results-dir DIR]
"""
import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

GZIP = {"method": "gzip", "compresslevel": 9, "mtime": 0}  # mtime 0: same bytes on every run


def load_model_script():
    spec = importlib.util.spec_from_file_location("triage_model", Path(__file__).with_name("007-triage-model.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    import joblib

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv")
    parser.add_argument("--cache-dir", default="cache")
    parser.add_argument("--results-dir", default="results")
    args = parser.parse_args()
    model_script = load_model_script()
    results_dir = Path(args.results_dir)
    bundle = joblib.load(Path(args.cache_dir) / model_script.BUNDLE_FILE)
    frame = pd.read_csv(args.csv)
    rows = bundle["test_rows"]
    pd.DataFrame({"text": bundle["train_texts"], "label": bundle["train_labels"]}).to_csv(
        results_dir / model_script.TRAIN_TICKETS_FILE, index=False, compression=GZIP)
    pd.DataFrame({"row": rows, "text": frame.loc[rows, "Document"].fillna("").to_numpy(),
                  "label": frame.loc[rows, "Topic_group"].to_numpy()}).to_csv(
        results_dir / model_script.TEST_TICKETS_FILE, index=False, compression=GZIP)
    settings = {"threshold": bundle["threshold"], "min_words": bundle["min_words"],
                "prefix_words": bundle["prefix_words"], "standard_openings": sorted(bundle["standard_openings"]),
                "source_bundle_built_at": bundle["built_at"]}
    (results_dir / model_script.SETTINGS_FILE).write_text(json.dumps(settings, ensure_ascii=False, indent=2))
    for name in (model_script.TRAIN_TICKETS_FILE, model_script.TEST_TICKETS_FILE, model_script.SETTINGS_FILE):
        print(f"{results_dir / name}: {(results_dir / name).stat().st_size / 1e6:.2f} MB")

    page_bundle = model_script.load_page_bundle(results_dir)
    test_texts = page_bundle["test_tickets"].loc[rows, "text"].tolist()
    refit = page_bundle["model"].predict_proba(test_texts)
    original = bundle["model"].predict_proba(test_texts)
    decisions = pd.read_csv(results_dir / model_script.DECISIONS_FILE)
    same_category = page_bundle["model"].classes_[refit.argmax(axis=1)] == decisions.set_index("row").loc[rows, "predicted"]
    matrix_gap = abs(page_bundle["train_matrix"] - bundle["train_matrix"]).max()
    print(f"\nModelo remontado a partir dos arquivos, como a página faz:")
    print(f"  maior diferença de probabilidade contra o modelo do pacote: {np.abs(refit - original).max()}")
    print(f"  mesma categoria prevista que results/{model_script.DECISIONS_FILE}: {int(same_category.sum())}"
          f" de {len(rows)}")
    print(f"  maior diferença na matriz dos tickets parecidos: {matrix_gap}")
    print(f"  mesmas configurações: {page_bundle['standard_openings'] == bundle['standard_openings']}"
          f" (aberturas), {page_bundle['threshold'] == bundle['threshold']} (limiar)")


if __name__ == "__main__":
    main()
