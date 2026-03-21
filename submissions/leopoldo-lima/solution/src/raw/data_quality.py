from __future__ import annotations

from typing import Any

ALLOWED_DEAL_STAGES = {"Prospecting", "Engaging", "Won", "Lost"}


def _to_float(value: str) -> float:
    try:
        return float((value or "").strip() or "0")
    except ValueError:
        return 0.0


def validate_sales_pipeline_rows(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()

    for idx, row in enumerate(rows, start=2):
        opportunity_id = (row.get("opportunity_id") or "").strip()
        deal_stage = (row.get("deal_stage") or "").strip()
        engage_date = (row.get("engage_date") or "").strip()
        close_date = (row.get("close_date") or "").strip()
        close_value = _to_float(row.get("close_value") or "")

        if not opportunity_id:
            errors.append(f"sales_pipeline.csv:{idx}: opportunity_id vazio")
        elif opportunity_id in seen_ids:
            errors.append(f"sales_pipeline.csv:{idx}: opportunity_id duplicado '{opportunity_id}'")
        else:
            seen_ids.add(opportunity_id)

        if deal_stage not in ALLOWED_DEAL_STAGES:
            errors.append(
                f"sales_pipeline.csv:{idx}: deal_stage invalido '{deal_stage}' "
                f"(permitidos: {sorted(ALLOWED_DEAL_STAGES)})"
            )
            continue

        if deal_stage == "Lost" and close_value != 0:
            errors.append(
                f"sales_pipeline.csv:{idx}: Lost exige close_value = 0 (atual: {close_value})"
            )
        if deal_stage == "Won":
            if close_value <= 0:
                errors.append(
                    f"sales_pipeline.csv:{idx}: Won exige close_value > 0 (atual: {close_value})"
                )
            if not close_date:
                errors.append(f"sales_pipeline.csv:{idx}: Won exige close_date preenchida")
        if deal_stage == "Engaging":
            if not engage_date:
                errors.append(f"sales_pipeline.csv:{idx}: Engaging exige engage_date preenchida")
            if close_date:
                errors.append(f"sales_pipeline.csv:{idx}: Engaging nao deve ter close_date")
        if deal_stage == "Prospecting":
            # Regra permissiva: pode nao ter engage_date, close_date, close_value.
            pass

    return errors


def summarize_validation(errors: list[str]) -> dict[str, Any]:
    return {
        "passed": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
    }
