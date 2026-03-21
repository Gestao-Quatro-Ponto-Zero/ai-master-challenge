from __future__ import annotations

from src.api.contracts import (
    DashboardFilterOptionsResponse,
    DashboardKpisResponse,
    OpportunitiesListResponse,
    OpportunityDetailResponse,
    OpportunityListItemResponse,
    ScoreExplanationResponse,
)
from src.domain.deal_stage import is_pipeline_open_stage
from src.infrastructure.repositories.api_opportunity_repository import OpportunityNotFoundError


class MockOpportunityRepository:
    """Demo repository that mimics API contract without HTTP calls."""

    def __init__(self) -> None:
        self._items = [
            OpportunityListItemResponse(
                id="MOCK-001",
                title="Conta ilustrativa (modo mock)",
                seller="Vendedor Mock",
                manager="Gestor Mock",
                region="Central",
                deal_stage="Engaging",
                amount=1000.0,
                score=55,
                priority_band="medium",
                next_action="agendar contato",
                nextBestAction="agendar contato",
                account="Conta ilustrativa (modo mock)",
                product="Produto-GTX-Mock",
                sales_agent="Vendedor Mock",
                regional_office="Central",
                close_value=1000.0,
            )
        ]

    def list_opportunities(
        self,
        region: str | None = None,
        manager: str | None = None,
        deal_stage: str | None = None,
        q: str | None = None,
        sort_by: str = "score",
        sort_order: str = "desc",
        limit: int = 20,
        page: int | None = None,
        page_size: int | None = None,
    ) -> OpportunitiesListResponse:
        items = self._items
        if region:
            items = [it for it in items if it.region == region]
        if manager:
            items = [it for it in items if it.manager == manager]
        if deal_stage:
            items = [it for it in items if it.deal_stage == deal_stage]
        if q:
            qn = q.strip().lower()
            items = [it for it in items if qn in it.title.lower()]
        # Mock: ordenação/paginação simplificadas (API real aplica regras completas).
        reverse = sort_order.lower() != "asc"
        if sort_by == "score":
            items = sorted(items, key=lambda it: it.score, reverse=reverse)
        elif sort_by == "amount":
            items = sorted(items, key=lambda it: it.amount, reverse=reverse)
        elif sort_by in ("title", "seller", "manager", "region", "deal_stage"):
            items = sorted(items, key=lambda it: getattr(it, sort_by), reverse=reverse)
        if page is not None and page_size is not None and page_size > 0:
            start = max(page - 1, 0) * page_size
            sliced = items[start : start + page_size]
            return OpportunitiesListResponse(total=len(items), items=sliced)
        return OpportunitiesListResponse(total=len(items), items=items[:limit])

    def get_opportunity(self, opportunity_id: str) -> OpportunityDetailResponse:
        for item in self._items:
            if item.id == opportunity_id:
                return OpportunityDetailResponse(
                    id=item.id,
                    title=item.title,
                    seller=item.seller,
                    manager=item.manager,
                    region=item.region,
                    deal_stage=item.deal_stage,
                    amount=item.amount,
                    scoreExplanation=ScoreExplanationResponse(
                        score=item.score,
                        priority_band=item.priority_band,
                        positive_factors=["modo mock ativo"],
                        negative_factors=[],
                        risk_flags=[],
                        next_action=item.next_action,
                    ),
                    account=item.account,
                    product=item.product,
                    sales_agent=item.sales_agent,
                    regional_office=item.regional_office,
                    close_value=item.close_value,
                    engage_date="",
                    close_date=None,
                    product_series="GTX",
                )
        raise OpportunityNotFoundError(f"Opportunity '{opportunity_id}' not found.")

    def get_dashboard_kpis(self) -> DashboardKpisResponse:
        open_count = len([it for it in self._items if is_pipeline_open_stage(it.deal_stage)])
        return DashboardKpisResponse(
            total_opportunities=len(self._items),
            open_opportunities=open_count,
            won_opportunities=len([it for it in self._items if it.deal_stage == "Won"]),
            lost_opportunities=len([it for it in self._items if it.deal_stage == "Lost"]),
            avg_score=round(sum(it.score for it in self._items) / len(self._items), 2),
        )

    def get_dashboard_filter_options(self) -> DashboardFilterOptionsResponse:
        offices = sorted({str(it.region).strip() for it in self._items if it.region})
        mgrs = sorted({str(it.manager).strip() for it in self._items if it.manager})
        stages = sorted({it.deal_stage for it in self._items})
        return DashboardFilterOptionsResponse(
            regional_offices=offices,
            managers=mgrs,
            deal_stages=stages,
            regions=offices,
        )
