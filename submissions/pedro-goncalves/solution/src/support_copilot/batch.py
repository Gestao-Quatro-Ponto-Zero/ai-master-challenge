from __future__ import annotations

import pandas as pd

from src.support_copilot.customer_care import assess_customer_care
from src.support_copilot.policy import Decision, OperatingMode, decide
from src.support_copilot.privacy import mask_pii


CUSTOMER_SUPPORT = "Atendimento ao cliente"
IT_SUPPORT = "Suporte interno de TI"
SUPPORTED_CONTEXTS = {CUSTOMER_SUPPORT, IT_SUPPORT}


def analyze_queue(
    frame: pd.DataFrame,
    *,
    text_column: str,
    id_column: str | None,
    context: str,
    classifier,
    threshold: float,
    kill_switch: bool,
    limit: int,
) -> list[dict]:
    if context not in SUPPORTED_CONTEXTS:
        raise ValueError(f"Contexto inválido: {context}")
    if text_column not in frame.columns:
        raise KeyError(text_column)
    if id_column is not None and id_column not in frame.columns:
        raise KeyError(id_column)

    selected = frame.head(limit)
    masked_rows = [
        mask_pii(raw_text)
        for raw_text in selected[text_column].fillna("").astype(str)
    ]
    masked_texts = [masked_text for masked_text, _ in masked_rows]
    assessments = [
        assess_customer_care(masked_text) for masked_text in masked_texts
    ]
    predictions = (
        [None] * len(selected)
        if context == CUSTOMER_SUPPORT
        else classifier.predict_many(masked_texts)
    )

    results = []
    for position, (prediction, assessment) in enumerate(
        zip(predictions, assessments)
    ):
        if context == CUSTOMER_SUPPORT:
            if kill_switch or assessment.requires_human:
                decision = decide(
                    category="Customer support",
                    confidence=0.0,
                    threshold=threshold,
                    mode=OperatingMode.SHADOW,
                    kill_switch=kill_switch,
                    customer_care_required=assessment.requires_human,
                )
            else:
                decision = Decision(
                    action="HUMAN_REVIEW",
                    reason=(
                        "O tipo informado orienta a fila, mas a decisão "
                        "continua com a equipe."
                    ),
                    requires_human=True,
                    simulated=False,
                )
            audit_prediction = {
                "category": None,
                "confidence": None,
                "source": "customer-care-gate",
            }
        else:
            decision = decide(
                category=prediction["category"],
                confidence=prediction["confidence"],
                threshold=threshold,
                mode=OperatingMode.SHADOW,
                kill_switch=kill_switch,
                customer_care_required=assessment.requires_human,
            )
            audit_prediction = prediction

        results.append(
            {
                "row_id": (
                    position + 1
                    if id_column is None
                    else selected.iloc[position][id_column]
                ),
                "context": context,
                "prediction": audit_prediction,
                "customer_care": assessment.to_dict(),
                "decision": decision.to_dict(),
                "pii_counts": masked_rows[position][1],
            }
        )

    return results
