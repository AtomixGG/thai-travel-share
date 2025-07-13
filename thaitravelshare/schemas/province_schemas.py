"""
Province-related response schemas for the Thai Travel Share API.
"""

from typing import List, Optional
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

from ..models.travel_model import Province


class ProvinceResponse(BaseModel):
    """Standard province response."""
    province: Province
    message: Optional[str] = None


class ProvinceListResponse(BaseModel):
    """Response for province list."""
    provinces: List[Province]
    total_count: int
    secondary_province_count: int
    regions: List[str]
    metadata: dict = {
        "description": "List of Thai provinces with tax reduction information",
        "last_updated": "2025-07-13"
    }


class SecondaryProvinceResponse(BaseModel):
    """Response for secondary provinces with higher tax benefits."""
    provinces: List[Province]
    total_count: int
    average_tax_reduction: Decimal
    highest_reduction_province: Optional[Province] = None
    benefits_summary: dict


class RegionListResponse(BaseModel):
    """Response for region list."""
    regions: List[str]
    region_details: List[dict]  # Each dict contains region info and province count


class TaxBenefitCalculation(BaseModel):
    """Tax benefit calculation response."""
    province: Province
    budget: Decimal
    estimated_tax_reduction: Decimal
    tax_reduction_rate: Decimal
    comparison_with_other_provinces: List[dict]
    savings_info: dict
    recommendations: List[str]


class ProvinceComparisonResponse(BaseModel):
    """Response comparing multiple provinces."""
    comparison_data: List[dict]
    best_value_province: Province
    highest_savings_province: Province
    budget_used: Decimal
    total_provinces_compared: int
    summary: dict


class ProvinceSearchResponse(BaseModel):
    """Response for province search results."""
    provinces: List[Province]
    search_criteria: dict
    total_matches: int
    suggestions: List[str]
