"""Build and evaluate the triage prototype model on Dataset 2 (challenge 002). Local only, no API calls.

Steps: stratified 80/20 split; on the training part only, out-of-fold predictions choose the confidence threshold
for 95% accuracy and measure how accuracy falls on short tickets; the final model is fit on the training part and
evaluated once on the held-out test part, with the rules of the prototype applied.

Usage:
  python 007-triage-model.py <csv> [--cache-dir DIR] [--results-dir DIR]
"""
import argparse
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
TEST_SHARE = 0.20
TARGET_ACCURACY = 0.95
WORD_LIMITS = [3, 5, 8, 10, 15, 20]
# Set after measuring the word limits on the training part (audit item 173): accuracy only falls below 5 words
# (79.0% against 84.6%); from 5 to 19 words short tickets are classified as well as the rest. Adjustable in the app.
MIN_WORDS = 5
EXAMPLE_TRIAGE_MINUTES = 3
TICKETS_PER_BLOCK = 1000
MINUTES_PER_HOUR = 60
BUNDLE_FILE = "003-triage-model.joblib"
EVALUATION_FILE = "006-triage-test-evaluation.json"
DECISIONS_FILE = "007-triage-test-decisions.csv"
# Files exported by script 010 so the page runs without the Kaggle datasets and without the pickle above.
TRAIN_TICKETS_FILE = "011-triage-train-tickets.csv.gz"
TEST_TICKETS_FILE = "012-triage-test-tickets.csv.gz"
SETTINGS_FILE = "013-triage-settings.json"
DECISION_STANDARD = "Fluxo de mensagem padronizada"
DECISION_INFO = "Pedir mais informação"
DECISION_AUTO = "Encaminhado automaticamente"
DECISION_HUMAN = "Fila humana com sugestões"


def load_it_tool():
    spec = importlib.util.spec_from_file_location("it_tool", Path(__file__).with_name("002-it-ticket-stats.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def opening(text, size):
    tokens = text.split()
    return " ".join(tokens[:size]) if len(tokens) >= size else None


def standard_openings(texts, it_tool):
    prefixes = texts.map(lambda text: opening(text, it_tool.TEMPLATE_PREFIX_WORDS)).value_counts()
    return set(prefixes[prefixes >= it_tool.TEMPLATE_MIN_TICKETS].index)


def threshold_for(confidence, is_correct):
    order = np.argsort(-confidence, kind="stable")
    cumulative = is_correct[order].cumsum() / np.arange(1, len(order) + 1)
    last = np.flatnonzero(cumulative >= TARGET_ACCURACY)[-1]
    return float(confidence[order][last]), (last + 1) / len(order)


def report_word_limits(word_counts, is_correct, it_tool):
    rows = {}
    for limit in WORD_LIMITS:
        short = word_counts < limit
        rows[f"< {limit}"] = {"Tickets": int(short.sum()), "%": it_tool.format_percent(short.mean()),
                              "Acerto nos curtos": it_tool.format_percent(is_correct[short].mean()),
                              "Acerto nos demais": it_tool.format_percent(is_correct[~short].mean())}
    print("\nConteúdo mínimo (só no treino, previsões fora da dobra):")
    it_tool.print_markdown(pd.DataFrame(rows).T, "Palavras")


def decide(texts, confidence, prefixes, threshold, prefix_words):
    # Rules run before the classifier: standardized messages first, then insufficient content.
    decisions = np.full(len(texts), DECISION_HUMAN, dtype=object)
    decisions[confidence >= threshold] = DECISION_AUTO
    decisions[texts.str.split().str.len().to_numpy() < MIN_WORDS] = DECISION_INFO
    decisions[texts.map(lambda text: opening(text, prefix_words) in prefixes).to_numpy()] = DECISION_STANDARD
    return decisions


def evaluate_test(model, test_texts, test_labels, prefixes, threshold, it_tool):
    probabilities = model.predict_proba(test_texts)
    predicted = model.classes_[probabilities.argmax(axis=1)]
    confidence = probabilities.max(axis=1)
    decisions = decide(test_texts, confidence, prefixes, threshold, it_tool.TEMPLATE_PREFIX_WORDS)
    correct = predicted == test_labels.to_numpy()
    auto = decisions == DECISION_AUTO
    shares = pd.Series(decisions).value_counts(normalize=True)
    metrics = {
        "test_tickets": len(test_texts), "threshold": threshold, "min_words": MIN_WORDS,
        "accuracy_all": float(correct.mean()), "auto_share": float(auto.mean()),
        "auto_accuracy": float(correct[auto].mean()),
        "decision_shares": {name: float(share) for name, share in shares.items()},
        "hours_per_1000_per_minute": TICKETS_PER_BLOCK * float(auto.mean()) / MINUTES_PER_HOUR,
    }
    per_category = pd.DataFrame({"label": test_labels.to_numpy(), "auto": auto, "correct": correct})
    table = per_category.groupby("label").apply(lambda group: pd.Series({
        "Tickets": len(group), "Encaminhados sozinhos": it_tool.format_percent(group["auto"].mean()),
        "Acerto nos encaminhados": it_tool.format_percent(group.loc[group["auto"], "correct"].mean())
        if group["auto"].any() else "-"}), include_groups=False)
    output = pd.DataFrame({"row": test_texts.index, "label": test_labels.to_numpy(), "predicted": predicted,
                           "confidence": np.round(confidence, 6), "decision": decisions})
    return metrics, table, output


def print_test_report(metrics, table, it_tool):
    print(f"\nTeste ({metrics['test_tickets']} tickets que o modelo nunca viu):")
    print(f"  acerto geral do classificador: {it_tool.format_percent(metrics['accuracy_all'])}")
    print(f"  encaminhados sozinhos: {it_tool.format_percent(metrics['auto_share'])}"
          f" | acerto neles: {it_tool.format_percent(metrics['auto_accuracy'])}")
    print("  decisões: " + " | ".join(f"{name} {it_tool.format_percent(share)}"
                                      for name, share in metrics["decision_shares"].items()))
    coefficient = metrics["hours_per_1000_per_minute"]
    print(f"  horas de triagem a cada {TICKETS_PER_BLOCK} tickets = {coefficient:.2f} × m"
          f" | com m = {EXAMPLE_TRIAGE_MINUTES}: {coefficient * EXAMPLE_TRIAGE_MINUTES:.1f} horas")
    print("\nPor categoria, no teste:")
    it_tool.print_markdown(table, "Categoria")


def main():
    import joblib
    from sklearn.model_selection import train_test_split

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv")
    parser.add_argument("--cache-dir", default="cache")
    parser.add_argument("--results-dir", default="results")
    args = parser.parse_args()
    it_tool = load_it_tool()
    frame = pd.read_csv(args.csv)
    texts, labels = frame["Document"].fillna(""), frame["Topic_group"]
    train_texts, test_texts, train_labels, test_labels = train_test_split(
        texts, labels, test_size=TEST_SHARE, stratify=labels, random_state=SEED)
    print(f"Separação estratificada, semente {SEED}: treino {len(train_texts)} | teste {len(test_texts)}")
    classes, out_of_fold = it_tool.fit_out_of_fold(train_texts, train_labels)
    oof_correct = classes[out_of_fold.argmax(axis=1)] == train_labels.to_numpy()
    threshold, train_coverage = threshold_for(out_of_fold.max(axis=1), oof_correct)
    print(f"Limiar para {it_tool.format_percent(TARGET_ACCURACY)} de acerto, escolhido só no treino: {threshold:.3f}"
          f" (cobertura no treino {it_tool.format_percent(train_coverage)})")
    report_word_limits(train_texts.str.split().str.len().to_numpy(), oof_correct, it_tool)
    model = it_tool_model(it_tool).fit(train_texts, train_labels)
    prefixes = standard_openings(train_texts, it_tool)
    metrics, table, output = evaluate_test(model, test_texts, test_labels, prefixes, threshold, it_tool)
    print_test_report(metrics, table, it_tool)
    metrics["per_category"] = table.to_dict(orient="index")
    vectorizer = model.named_steps["tfidfvectorizer"]
    bundle = {"model": model, "threshold": threshold, "min_words": MIN_WORDS, "standard_openings": prefixes,
              "prefix_words": it_tool.TEMPLATE_PREFIX_WORDS,
              "train_matrix": vectorizer.transform(train_texts), "train_texts": train_texts.tolist(),
              "train_labels": train_labels.tolist(), "test_rows": test_texts.index.tolist(),
              "built_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")}
    Path(args.cache_dir).mkdir(exist_ok=True)
    joblib.dump(bundle, Path(args.cache_dir) / BUNDLE_FILE)
    (Path(args.results_dir) / EVALUATION_FILE).write_text(json.dumps(metrics, ensure_ascii=False, indent=2))
    output.to_csv(Path(args.results_dir) / DECISIONS_FILE, index=False)
    print(f"\nModelo em {Path(args.cache_dir) / BUNDLE_FILE}; avaliação em {Path(args.results_dir) / EVALUATION_FILE}"
          f" e {Path(args.results_dir) / DECISIONS_FILE}")


def it_tool_model(it_tool):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline

    return make_pipeline(
        TfidfVectorizer(ngram_range=it_tool.NGRAM_RANGE, min_df=it_tool.MIN_DOC_FREQ, sublinear_tf=True),
        LogisticRegression(max_iter=it_tool.MAX_ITERATIONS),
    )



def load_page_bundle(results_dir):
    """Refit the page model from the files exported by script 010: same training texts, same settings, no pickle."""
    results_dir = Path(results_dir)
    train = pd.read_csv(results_dir / TRAIN_TICKETS_FILE, keep_default_na=False)
    test = pd.read_csv(results_dir / TEST_TICKETS_FILE, keep_default_na=False)
    settings = json.loads((results_dir / SETTINGS_FILE).read_text())
    model = it_tool_model(load_it_tool()).fit(train["text"], train["label"])
    return {"model": model, "threshold": settings["threshold"], "min_words": settings["min_words"],
            "standard_openings": set(settings["standard_openings"]), "prefix_words": settings["prefix_words"],
            "train_matrix": model.named_steps["tfidfvectorizer"].transform(train["text"]),
            "train_texts": train["text"].tolist(), "train_labels": train["label"].tolist(),
            "test_rows": test["row"].tolist(), "test_tickets": test.set_index("row"),
            "built_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")}


if __name__ == "__main__":
    main()
