from __future__ import annotations

from src.api.contracts import OpportunityDetailResponse, OpportunityListItemResponse
from src.infrastructure.http.dtos import OpportunityDetailDTO, OpportunityListItemDTO


def map_wire_list_item_to_contract(payload: dict) -> OpportunityListItemResponse:
    dto = OpportunityListItemDTO.from_wire(payload)
    return OpportunityListItemResponse.model_validate(dto.model_dump())


def map_wire_detail_to_contract(payload: dict) -> OpportunityDetailResponse:
    dto = OpportunityDetailDTO.model_validate(payload)
    return OpportunityDetailResponse.model_validate(dto.model_dump())
