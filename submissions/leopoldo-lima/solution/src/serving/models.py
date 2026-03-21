"""Modelo canónico de oportunidade para a camada HTTP (dataset real)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ServingOpportunity:
    """Oportunidade após ingestão, normalização e joins sobre dimensões oficiais."""

    opportunity_id: str
    sales_agent: str
    manager: str
    regional_office: str
    account_name: str | None
    account_office_location: str | None
    product_canonical: str
    product_series: str
    product_sales_price: float
    deal_stage: str
    engage_date: str
    close_date: str | None
    close_value: float
    account_revenue: str = ""
    account_employees: str = ""

    def to_api_row(self) -> dict[str, Any]:
        """Formato esperado por `src.api.app` (listagem, scoring, KPIs)."""
        region = (self.regional_office or "").strip() or (
            (self.account_office_location or "").strip()
        )
        if (self.account_name or "").strip():
            title = (self.account_name or "").strip()
        elif self.product_canonical:
            title = f"{self.product_canonical} ({self.opportunity_id})"
        else:
            title = self.opportunity_id
        return {
            "id": self.opportunity_id,
            "title": title,
            "seller": self.sales_agent,
            "manager": self.manager,
            "region": region,
            "amount": self.close_value,
            # Campos extras para explainability / futuros endpoints (ignorados pelo contrato mínimo)
            "product": self.product_canonical,
            "product_series": self.product_series,
            "product_sales_price": self.product_sales_price,
            "deal_stage": self.deal_stage,
            "engage_date": self.engage_date,
            "close_date": self.close_date,
            "account_name": (self.account_name or "").strip() or None,
            "account_revenue": (self.account_revenue or "").strip(),
            "account_employees": (self.account_employees or "").strip(),
            "team_regional_office": (self.regional_office or "").strip(),
        }
