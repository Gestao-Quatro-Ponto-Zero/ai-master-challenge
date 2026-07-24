from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data/raw/it-service/all_tickets_processed_improved_v3.csv"
ARTIFACTS = ROOT / "artifacts"
MODELS = ARTIFACTS / "models"
TABLES = ARTIFACTS / "tables"
DOCS = ROOT / "docs/gate-2"
RANDOM_STATE = 42
TARGET_SELECTIVE_ACCURACY = 0.95
THRESHOLD_GRID = np.arange(0.50, 0.96, 0.05)


def expected_calibration_error(
    probabilities: np.ndarray, labels: np.ndarray, bins: int = 10
) -> float:
    confidence = probabilities.max(axis=1)
    predictions = probabilities.argmax(axis=1)
    correct = predictions == labels
    edges = np.linspace(0.0, 1.0, bins + 1)
    ece = 0.0
    for lower, upper in zip(edges[:-1], edges[1:]):
        include = (confidence > lower) & (confidence <= upper)
        if include.any():
            ece += include.mean() * abs(
                correct[include].mean() - confidence[include].mean()
            )
    return float(ece)


def selective_metrics(
    labels: pd.Series,
    predictions: np.ndarray,
    confidence: np.ndarray,
    threshold: float,
) -> dict:
    covered = confidence >= threshold
    return {
        "threshold": round(float(threshold), 2),
        "coverage": float(covered.mean()),
        "covered_tickets": int(covered.sum()),
        "accuracy_when_covered": (
            float(accuracy_score(labels.loc[covered], predictions[covered]))
            if covered.any()
            else None
        ),
        "macro_f1_when_covered": (
            float(
                f1_score(
                    labels.loc[covered],
                    predictions[covered],
                    average="macro",
                    zero_division=0,
                )
            )
            if covered.any()
            else None
        ),
        "errors_when_covered": (
            int((predictions[covered] != labels.loc[covered].to_numpy()).sum())
            if covered.any()
            else 0
        ),
    }


def main() -> None:
    MODELS.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)

    data = pd.read_csv(DATA_PATH)
    data["Document"] = (
        data["Document"].fillna("").str.replace(r"\s+", " ", regex=True).str.strip()
    )

    development, final_test = train_test_split(
        data,
        test_size=0.15,
        random_state=RANDOM_STATE,
        stratify=data["Topic_group"],
    )
    train, threshold_validation = train_test_split(
        development,
        test_size=0.15 / 0.85,
        random_state=RANDOM_STATE,
        stratify=development["Topic_group"],
    )

    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    ngram_range=(1, 2),
                    min_df=2,
                    max_df=0.98,
                    max_features=80_000,
                    sublinear_tf=True,
                ),
            ),
            (
                "classifier",
                CalibratedClassifierCV(
                    estimator=LinearSVC(
                        class_weight="balanced", random_state=RANDOM_STATE
                    ),
                    method="sigmoid",
                    cv=3,
                ),
            ),
        ]
    )
    pipeline.fit(train["Document"], train["Topic_group"])
    classes = pipeline.named_steps["classifier"].classes_

    validation_probabilities = pipeline.predict_proba(
        threshold_validation["Document"]
    )
    validation_predictions = classes[validation_probabilities.argmax(axis=1)]
    validation_confidence = validation_probabilities.max(axis=1)
    threshold_rows = [
        {
            **selective_metrics(
                threshold_validation["Topic_group"],
                validation_predictions,
                validation_confidence,
                threshold,
            ),
            "split": "threshold_validation",
        }
        for threshold in THRESHOLD_GRID
    ]
    thresholds = pd.DataFrame(threshold_rows)
    thresholds.to_csv(TABLES / "classifier_coverage_accuracy.csv", index=False)

    candidates = thresholds[
        thresholds["accuracy_when_covered"].fillna(0)
        >= TARGET_SELECTIVE_ACCURACY
    ].sort_values(["coverage", "threshold"], ascending=[False, True])
    if candidates.empty:
        selected_threshold = float(THRESHOLD_GRID[-1])
    else:
        selected_threshold = float(candidates.iloc[0]["threshold"])
    selected_validation = selective_metrics(
        threshold_validation["Topic_group"],
        validation_predictions,
        validation_confidence,
        selected_threshold,
    )

    test_probabilities = pipeline.predict_proba(final_test["Document"])
    test_predictions = classes[test_probabilities.argmax(axis=1)]
    test_confidence = test_probabilities.max(axis=1)
    selected_test = selective_metrics(
        final_test["Topic_group"],
        test_predictions,
        test_confidence,
        selected_threshold,
    )

    majority_class = train["Topic_group"].mode().iloc[0]
    majority_predictions = np.repeat(majority_class, len(final_test))
    report = classification_report(
        final_test["Topic_group"],
        test_predictions,
        output_dict=True,
        zero_division=0,
    )
    (
        pd.DataFrame(report)
        .T.reset_index()
        .rename(columns={"index": "class"})
        .to_csv(TABLES / "classifier_per_class_metrics.csv", index=False)
    )
    matrix = confusion_matrix(
        final_test["Topic_group"], test_predictions, labels=classes
    )
    pd.DataFrame(matrix, index=classes, columns=classes).to_csv(
        TABLES / "classifier_confusion_matrix.csv"
    )

    final_label_indices = pd.Categorical(
        final_test["Topic_group"], categories=classes
    ).codes
    metrics = {
        "data": {
            "rows": int(len(data)),
            "train_rows": int(len(train)),
            "threshold_validation_rows": int(len(threshold_validation)),
            "final_test_rows": int(len(final_test)),
            "classes": classes.tolist(),
            "random_state": RANDOM_STATE,
            "split": (
                "stratified 70/15/15; threshold selected only on validation; "
                "normalized documents are unique in the source audit"
            ),
        },
        "baseline_final_test": {
            "strategy": f"always predict {majority_class}",
            "accuracy": float(
                accuracy_score(final_test["Topic_group"], majority_predictions)
            ),
            "macro_f1": float(
                f1_score(
                    final_test["Topic_group"],
                    majority_predictions,
                    average="macro",
                    zero_division=0,
                )
            ),
        },
        "model_final_test": {
            "name": (
                "word 1-2 gram TF-IDF + class-balanced LinearSVC "
                "+ sigmoid calibration"
            ),
            "accuracy": float(
                accuracy_score(final_test["Topic_group"], test_predictions)
            ),
            "balanced_accuracy": float(
                balanced_accuracy_score(
                    final_test["Topic_group"], test_predictions
                )
            ),
            "macro_f1": float(
                f1_score(
                    final_test["Topic_group"],
                    test_predictions,
                    average="macro",
                    zero_division=0,
                )
            ),
            "weighted_f1": float(
                f1_score(
                    final_test["Topic_group"],
                    test_predictions,
                    average="weighted",
                    zero_division=0,
                )
            ),
            "ece_10_bins": expected_calibration_error(
                test_probabilities, final_label_indices, bins=10
            ),
        },
        "threshold_selection": {
            "criterion": (
                "maximize validation coverage subject to selective accuracy >= "
                f"{TARGET_SELECTIVE_ACCURACY:.0%}"
            ),
            "selected_threshold": selected_threshold,
            "validation": selected_validation,
            "final_test": selected_test,
        },
    }

    (ARTIFACTS / "classifier_metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    joblib.dump(pipeline, MODELS / "ticket_classifier.joblib")

    model = metrics["model_final_test"]
    baseline = metrics["baseline_final_test"]
    model_card = f"""# Model Card: classificador de tickets de TI

## Propósito

Demonstrar, em dados públicos, uma etapa de triagem com classificação, confiança calibrada e abstenção. O modelo não foi validado para suporte ao cliente da G4 nem para o Dataset 1.

## Dados e protocolo

- Fonte: Dataset 2 do Challenge 002
- Linhas: **{metrics['data']['rows']:,}**
- Treino e calibração interna: **{metrics['data']['train_rows']:,}**
- Validação exclusiva de threshold: **{metrics['data']['threshold_validation_rows']:,}**
- Teste final: **{metrics['data']['final_test_rows']:,}**
- Classes: **{len(classes)}**
- Split: estratificado 70/15/15, seed {RANDOM_STATE}
- Duplicatas normalizadas: nenhuma detectada no data audit

O threshold foi escolhido na validação. O teste final foi usado uma única vez para reportar as métricas abaixo.

## Resultado no teste final

| Métrica | Baseline majoritário | Modelo |
|---|---:|---:|
| Acurácia | {baseline['accuracy']:.3f} | {model['accuracy']:.3f} |
| Macro-F1 | {baseline['macro_f1']:.3f} | {model['macro_f1']:.3f} |
| Balanced accuracy | n/a | {model['balanced_accuracy']:.3f} |
| Weighted-F1 | n/a | {model['weighted_f1']:.3f} |
| ECE, 10 bins | n/a | {model['ece_10_bins']:.3f} |

## Abstenção

Critério pré-aplicado na validação: maximizar cobertura com acurácia seletiva mínima de 95%.

- Threshold selecionado: **{selected_threshold:.2f}**
- Validação: cobertura **{selected_validation['coverage']:.1%}**, acurácia nos cobertos **{selected_validation['accuracy_when_covered']:.1%}**
- Teste final: cobertura **{selected_test['coverage']:.1%}**, acurácia nos cobertos **{selected_test['accuracy_when_covered']:.1%}**

Esse threshold é uma referência técnica para shadow mode. Não autoriza execução em produção.

## Limitações

1. A taxonomia é de suporte interno de TI e não equivale à taxonomia do Dataset 1.
2. O texto já foi pré-processado pela origem.
3. Calibração em dados públicos não representa risco de produção.
4. Não há validação temporal, mudança de domínio nem rótulos da G4.
5. O protótipo deve operar em shadow mode e permitir abstenção, override e kill switch.
"""
    (DOCS / "model-card.md").write_text(model_card, encoding="utf-8")
    print(
        json.dumps(
            {
                "metrics": metrics,
                "selected_threshold": selected_threshold,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
