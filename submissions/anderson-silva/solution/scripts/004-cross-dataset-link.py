"""Apply the phase 1 classifier (trained on all of Dataset 2) to the Dataset 1 descriptions and cross the
predicted category with ticket type, priority, channel, status and CSAT. No API calls.

Usage:
  python 004-cross-dataset-link.py <dataset-1-csv> <dataset-2-csv>
"""
import argparse
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

CROSS_COLUMNS = ["Ticket Type", "Ticket Priority", "Ticket Channel", "Ticket Status", "Customer Satisfaction Rating"]
DATASET_1_COLUMNS = ["Ticket Description", "Product Purchased"] + CROSS_COLUMNS
PLACEHOLDER = "{product_purchased}"
PERMUTATIONS = 200
SEED = 42
CONFIDENCE_LEVELS = [0.5, 0.7, 0.9]
MIN_EXPECTED = 5


def load_it_tool():
    # Reuse the phase 1 settings and helpers from the Dataset 2 tool, so both use the same model.
    path = Path(__file__).with_name("002-it-ticket-stats.py")
    spec = importlib.util.spec_from_file_location("it_tool", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fit_full_model(it_tool, documents, labels):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline

    model = make_pipeline(
        TfidfVectorizer(ngram_range=it_tool.NGRAM_RANGE, min_df=it_tool.MIN_DOC_FREQ, sublinear_tf=True),
        LogisticRegression(max_iter=it_tool.MAX_ITERATIONS),
    )
    return model.fit(documents, labels)


def cramers_v(predicted, variable):
    table = pd.crosstab(predicted, variable)
    chi2, p_value, _, expected = stats.chi2_contingency(table, correction=False)
    v = np.sqrt(chi2 / (table.to_numpy().sum() * (min(table.shape) - 1)))
    return v, p_value, (expected < MIN_EXPECTED).mean()


def permutation_p(predicted, variable, observed, rng):
    shuffled = [cramers_v(predicted, pd.Series(rng.permutation(variable.to_numpy()), index=variable.index))[0]
                for _ in range(PERMUTATIONS)]
    return (sum(value >= observed for value in shuffled) + 1) / (PERMUTATIONS + 1)


def report_confidence(it_tool, name, confidence):
    shares = " | ".join(f"≥ {level:.1f}: {it_tool.format_percent((confidence >= level).mean())}"
                        for level in CONFIDENCE_LEVELS)
    print(f"  Confiança (maior probabilidade) {name}: mediana {confidence.median():.3f} | {shares}")


def report_variant(it_tool, name, predicted, confidence, frame, rng):
    print(f"\n## Variante: {name}")
    counts = predicted.value_counts()
    print("Categoria prevista: " + ", ".join(f"{topic} {count} ({it_tool.format_percent(count / len(predicted))})"
                                             for topic, count in counts.items()))
    report_confidence(it_tool, "no Dataset 1", confidence)
    rows = {}
    for column in CROSS_COLUMNS:
        present = frame[column].notna()
        variable = frame.loc[present, column]
        v, p_value, sparse = cramers_v(predicted[present], variable)
        rows[column] = {
            "Tickets": int(present.sum()),
            "V de Cramér": f"{v:.3f}",
            "p (qui-quadrado)": f"{p_value:.3f}",
            "p (Bonferroni)": f"{min(1.0, p_value * len(CROSS_COLUMNS)):.3f}",
            f"p ({PERMUTATIONS} sorteios)": f"{permutation_p(predicted[present], variable, v, rng):.3f}",
            f"Células com esperado < {MIN_EXPECTED}": it_tool.format_percent(sparse),
        }
    print("\nAssociação entre a categoria prevista e cada variável do Dataset 1:")
    it_tool.print_markdown(pd.DataFrame(rows).T, "Variável")
    table = pd.crosstab(predicted, frame["Ticket Type"], normalize="index").map(it_tool.format_percent)
    print("\nTipo do ticket por categoria prevista (% da linha):")
    it_tool.print_markdown(table, "Categoria prevista")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dataset_1_csv")
    parser.add_argument("dataset_2_csv")
    args = parser.parse_args()
    it_tool = load_it_tool()
    it_frame = pd.read_csv(args.dataset_2_csv)
    it_documents, it_labels = it_frame["Document"].fillna(""), it_frame["Topic_group"]
    _, out_of_fold = it_tool.fit_out_of_fold(it_documents, it_labels)
    print("Referência: o mesmo modelo nos tickets do Dataset 2, em validação cruzada:")
    report_confidence(it_tool, "no Dataset 2", pd.Series(out_of_fold.max(axis=1)))
    model = fit_full_model(it_tool, it_documents, it_labels)
    frame = pd.read_csv(args.dataset_1_csv, usecols=DATASET_1_COLUMNS)  # names and e-mails are never read
    descriptions = frame["Ticket Description"].fillna("")
    variants = {
        "descrição como está (o marcador não existe no vocabulário do Dataset 2)": descriptions,
        "marcador trocado pelo nome do produto": pd.Series(
            [text.replace(PLACEHOLDER, product) for text, product in zip(descriptions, frame["Product Purchased"])],
            index=frame.index),
    }
    for name, texts in variants.items():
        probabilities = model.predict_proba(texts)
        predicted = pd.Series(model.classes_[probabilities.argmax(axis=1)], index=frame.index)
        confidence = pd.Series(probabilities.max(axis=1), index=frame.index)
        report_variant(it_tool, name, predicted, confidence, frame, np.random.default_rng(SEED))


if __name__ == "__main__":
    main()
