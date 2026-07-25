from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.support_copilot.customer_care import assess_customer_care
from src.support_copilot.inference import TicketClassifier


DATASET_1 = ROOT / "data/raw/customer-support/customer_support_tickets.csv"
MODEL_PATH = ROOT / "artifacts/models/ticket_classifier.joblib"
OUTPUT = ROOT / "artifacts/cross_dataset_audit.json"
REPORT = ROOT / "docs/gate-2/cross-dataset-validation.md"
THRESHOLD = 0.75


def main() -> None:
    support = pd.read_csv(DATASET_1)
    texts = (
        support["Ticket Subject"].fillna("")
        + " "
        + support["Ticket Description"].fillna("")
    ).str.strip().tolist()

    classifier = TicketClassifier(MODEL_PATH)
    predictions = classifier.predict_many(texts)
    confidences = pd.Series(
        [prediction["confidence"] for prediction in predictions]
    )
    category_counts = Counter(
        prediction["category"] for prediction in predictions
    )
    assessments = [assess_customer_care(text) for text in texts]
    signal_counts = Counter(
        code
        for assessment in assessments
        for code in assessment.signal_codes
    )
    human_care_rows = sum(
        assessment.requires_human for assessment in assessments
    )

    audit = {
        "dataset_1_rows_scored": len(texts),
        "dataset_2_model_sha256": classifier.model_sha256,
        "threshold": THRESHOLD,
        "confidence": {
            "median": float(confidences.median()),
            "p90": float(confidences.quantile(0.90)),
            "share_at_or_above_threshold": float(
                confidences.ge(THRESHOLD).mean()
            ),
        },
        "predicted_categories": dict(category_counts),
        "largest_category_share": float(
            max(category_counts.values()) / len(texts)
        ),
        "customer_care": {
            "rows": int(human_care_rows),
            "share": float(human_care_rows / len(texts)),
            "signal_counts": dict(signal_counts),
        },
        "interpretation": (
            "Exploratory out-of-domain application. Dataset 1 has no labels "
            "compatible with the Dataset 2 taxonomy, so accuracy is unknown."
        ),
    }
    OUTPUT.write_text(
        json.dumps(audit, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    largest_category, largest_count = category_counts.most_common(1)[0]
    report = f"""# Validação cruzada dos datasets

## Pergunta

O classificador treinado nas **47.837 solicitações do Dataset 2** pode ser aplicado diretamente
às **8.469 mensagens do Dataset 1**?

## Teste

O modelo final foi executado sobre `Ticket Subject + Ticket Description` de todas as linhas do
Dataset 1. Esse é um teste fora do domínio: as categorias dos dois arquivos não são equivalentes
e não existe rótulo compatível para calcular acerto.

## Resultado

- {audit['confidence']['share_at_or_above_threshold']:.1%} das mensagens ficaram acima do threshold de {THRESHOLD:.0%};
- a confiança mediana foi {audit['confidence']['median']:.1%};
- **{largest_category}** concentrou {largest_count:,} previsões ({audit['largest_category_share']:.1%});
- o gate de cuidado com o cliente sinalizou {human_care_rows:,} mensagens ({audit['customer_care']['share']:.1%}).

## Interpretação

A confiança aparente não prova transferência. A concentração extrema numa única categoria mostra
que o modelo de suporte interno de TI não deve rotear automaticamente solicitações de clientes.
O cruzamento dos datasets serve para revelar essa fronteira: o Dataset 2 comprova a viabilidade
técnica do classificador em sua própria taxonomia; o Dataset 1 mostra os campos, os riscos de
qualidade e os sinais de cuidado necessários ao fluxo de atendimento.

## Decisão

O protótipo aceita as filas do exercício e processa todas as linhas selecionadas, mas permanece em
modo de observação. A fila de clientes usa seus campos operacionais e o gate de cuidado; a fila de
TI usa o classificador de oito categorias. Uma taxonomia não substitui a outra.
"""
    REPORT.write_text(report, encoding="utf-8")
    print(json.dumps(audit, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
