"""Deepening of the Dataset 1 diagnosis (challenge 002): stalled share by combinations of channel, priority and
type, and a model of the CSAT with all variables together. Local only, no API calls.

Usage:
  python 006-diagnosis-deepening.py <csv> stall-combinations
  python 006-diagnosis-deepening.py <csv> csat-model

Premise of audit item 95: the time columns only mark that a step happened; the stage comes from the status.
Customer names and e-mails are never read.
"""
import argparse
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

SEED = 42
STALLED_STATUSES = ["Open", "Pending Customer Response"]
COMBINATIONS = [
    ("Ticket Channel", "Ticket Priority"),
    ("Ticket Channel", "Ticket Type"),
    ("Ticket Priority", "Ticket Type"),
    ("Ticket Channel", "Ticket Priority", "Ticket Type"),
]
MIN_GROUP = 30
WORST_CELLS = 3
CV_FOLDS = 5
PERMUTATIONS = 200
FOREST_TREES = 300
FOREST_MIN_LEAF = 5
IMPORTANCE_REPEATS = 10
CATEGORICAL_FEATURES = ["Ticket Channel", "Ticket Priority", "Ticket Type", "Ticket Subject", "Product Purchased",
                        "Customer Gender", "Problema relatado"]
AGE = "Customer Age"
CSAT = "Customer Satisfaction Rating"
COLUMNS = ["Ticket Status", "Ticket Channel", "Ticket Priority", "Ticket Type", "Ticket Subject", "Product Purchased",
           "Customer Gender", AGE, "Ticket Description", CSAT]


def load_sibling(file_name, module_name):
    spec = importlib.util.spec_from_file_location(module_name, Path(__file__).with_name(file_name))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cell_rows(key, stalled, overall_rate, tests):
    rows = []
    for cell, values in stalled.groupby(key):
        if len(values) < MIN_GROUP:
            continue
        result = stats.binomtest(int(values.sum()), len(values), overall_rate)
        rows.append((cell, len(values), values.mean(), min(1.0, result.pvalue * tests)))
    return sorted(rows, key=lambda row: row[2], reverse=True)


def report_stall_combinations(tickets, base):
    stalled = tickets["Ticket Status"].isin(STALLED_STATUSES)
    overall_rate = stalled.mean()
    keys = [tickets[list(columns)].astype(str).agg(" | ".join, axis=1) for columns in COMBINATIONS]
    tests = sum(key.nunique() for key in keys)
    print(f"Parcela parada (aberto + aguardando o cliente) no total: {base.format_percent(overall_rate)}"
          f" de {len(tickets)} tickets | grupos com pelo menos {MIN_GROUP} tickets"
          f" | Bonferroni sobre {tests} grupos")
    summary, worst = {}, []
    for columns, key in zip(COMBINATIONS, keys):
        name = " × ".join(columns)
        strength, p_value = base.cramers_v(pd.crosstab(key, stalled))
        rows = cell_rows(key, stalled, overall_rate, tests)
        sizes = [row[1] for row in rows]
        summary[name] = {"Grupos": len(rows), "Tickets por grupo": f"{min(sizes)} a {max(sizes)}",
                         "V de Cramér": f"{strength:.3f}", "p": f"{p_value:.3f}",
                         "Parcela parada": f"{base.format_percent(rows[-1][2])} a {base.format_percent(rows[0][2])}"}
        worst += [(name, *row) for row in rows[:WORST_CELLS]]
    print("\nAssociação entre cada combinação e a parcela parada:")
    base.print_markdown(pd.DataFrame(summary).T, "Combinação")
    table = pd.DataFrame([{"Combinação": name, "Grupo": cell, "Tickets": size, "Parcela parada": base.format_percent(share),
                           "p (Bonferroni)": f"{p_value:.3f}"} for name, cell, size, share, p_value in worst])
    print(f"\nOs {WORST_CELLS} grupos com maior parcela parada em cada combinação:")
    base.print_markdown(table.set_index("Combinação"), "Combinação")


def build_features(tickets):
    signals_tool = load_sibling("005-ticket-text-signals.py", "text_signals")
    texts = tickets["Ticket Description"].fillna("").str.replace(signals_tool.PLACEHOLDER, "{x}", regex=True)
    problem = signals_tool.problem_of(signals_tool.find_labels(texts, signals_tool.PROBLEM_TEMPLATES))
    signals = signals_tool.find_labels(texts, signals_tool.SIGNAL_TEMPLATES).astype(int)
    features = tickets[CATEGORICAL_FEATURES[:-1] + [AGE]].copy()
    features["Problema relatado"] = problem
    return pd.concat([features, signals], axis=1), list(signals.columns)


def make_model(estimator, numeric):
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    encoder = ColumnTransformer([("categories", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
                                 ("numbers", StandardScaler(), numeric)])
    return make_pipeline(encoder, estimator)


def fold_importances(model, features, target, folds):
    from sklearn.inspection import permutation_importance

    per_fold = []
    for train, test in folds.split(features, target):
        model.fit(features.iloc[train], target.iloc[train])
        result = permutation_importance(model, features.iloc[test], target.iloc[test], n_repeats=IMPORTANCE_REPEATS,
                                        random_state=SEED, scoring="accuracy")
        per_fold.append(pd.Series(result.importances_mean, index=features.columns))
    return pd.concat(per_fold, axis=1)


def report_csat_model(tickets, base):
    from sklearn.dummy import DummyClassifier
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold, cross_val_score, permutation_test_score

    rated = tickets[tickets[CSAT].notna()].reset_index(drop=True)
    features, signal_columns = build_features(rated)
    target = rated[CSAT].astype(int)
    numeric = [AGE] + signal_columns
    folds = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=SEED)
    print(f"Modelo do CSAT: {len(rated)} tickets fechados, {len(features.columns)} variáveis"
          f" ({len(CATEGORICAL_FEATURES)} de categoria, idade e {len(signal_columns)} sinais do cliente),"
          f" validação cruzada em {CV_FOLDS} partes, semente {SEED}")
    baseline = cross_val_score(DummyClassifier(strategy="most_frequent"), features, target, cv=folds).mean()
    linear = make_model(LogisticRegression(max_iter=2000), numeric)
    score, permuted, p_value = permutation_test_score(linear, features, target, cv=folds, n_permutations=PERMUTATIONS,
                                                      scoring="accuracy", random_state=SEED, n_jobs=-1)
    forest = make_model(RandomForestClassifier(n_estimators=FOREST_TREES, min_samples_leaf=FOREST_MIN_LEAF,
                                               random_state=SEED, n_jobs=-1), numeric)
    forest_score = cross_val_score(forest, features, target, cv=folds).mean()
    print(f"\nAcerto da nota exata (1 a 5):")
    print(f"  chute ingênuo (sempre a nota mais comum): {base.format_percent(baseline)}")
    print(f"  regressão logística: {base.format_percent(score)} | com rótulos embaralhados ({PERMUTATIONS} vezes):"
          f" média {base.format_percent(permuted.mean())}, máximo {base.format_percent(permuted.max())} | p = {p_value:.3f}")
    print(f"  floresta aleatória (capta combinações entre variáveis): {base.format_percent(forest_score)}")
    importances = fold_importances(forest, features, target, folds)
    table = pd.DataFrame({"Queda média no acerto": importances.mean(axis=1).map(base.format_percent),
                          "Desvio entre as partes": importances.std(axis=1).map(base.format_percent)})
    table = table.loc[importances.mean(axis=1).sort_values(ascending=False).index]
    print(f"\nImportância de cada variável na floresta (queda no acerto ao embaralhar a variável no teste,"
          f" {IMPORTANCE_REPEATS} repetições por parte; perto de zero = sem influência):")
    base.print_markdown(table, "Variável")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv")
    parser.add_argument("report", choices=["stall-combinations", "csat-model"])
    args = parser.parse_args()
    base = load_sibling("001-ticket-stats.py", "ticket_stats")
    tickets = pd.read_csv(args.csv, usecols=COLUMNS)
    if args.report == "stall-combinations":
        report_stall_combinations(tickets, base)
        return
    report_csat_model(tickets, base)


if __name__ == "__main__":
    main()
