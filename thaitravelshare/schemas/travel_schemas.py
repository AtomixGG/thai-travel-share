from ..core.utils import utc_now
from pydantic import Field
"""
Travel plan-related response schemas for the Thai Travel Share API.
"""

from typing import List, Optional
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

from ..models.travel_model import TravelPlan, TravelPlanWithTaxInfo


class TravelPlanResponse(BaseModel):
    """Standard travel plan response."""
    travel_plan: TravelPlan
    message: Optional[str] = None
    estimated_savings: Optional[Decimal] = None


class TravelPlanListResponse(BaseModel):
    """Response for travel plan list."""
    travel_plans: List[TravelPlan]
    total_count: int
    total_estimated_savings: Optional[Decimal] = None
    plans_by_status: dict  # e.g., {"planned": 3, "ongoing": 1, "completed": 2}
    upcoming_trips: List[TravelPlan]


class TravelPlanCreationResponse(BaseModel):
    """Response after creating a travel plan."""
    travel_plan: TravelPlan
    message: str = "Travel plan created successfully"
    tax_benefits: dict
    suggestions: List[str]
    next_steps: List[str] = [
        "Review your itinerary",
        "Book accommodations",
        "Prepare necessary documents",
        "Check weather conditions"
    ]


class TravelPlanUpdateResponse(BaseModel):
    """Response after updating a travel plan."""
    travel_plan: TravelPlan
    message: str = "Travel plan updated successfully"
    updated_fields: List[str]
    tax_benefit_changes: Optional[dict] = None
    timestamp: datetime = Field(default_factory=utc_now)


class TravelPlanTaxInfoResponse(BaseModel):
    """Response with detailed tax information for a travel plan."""
    travel_plan: TravelPlanWithTaxInfo
    detailed_calculations: dict
    potential_additional_savings: List[dict]
    tax_filing_tips: List[str]
    required_documents: List[str]


class TravelPlanStatsResponse(BaseModel):
    """Response with user's travel statistics."""
    total_plans: int
    completed_trips: int
    total_spent: Decimal
    total_tax_savings: Decimal
    favorite_regions: List[str]
    upcoming_trips_count: int
    monthly_breakdown: List[dict]
    year_summary: dict


class TravelPlanRecommendationResponse(BaseModel):
    """Response with travel plan recommendations."""
    recommended_provinces: List[dict]
    budget_optimization_tips: List[str]
    seasonal_suggestions: List[dict]
    tax_maximization_strategies: List[str]
    similar_user_preferences: List[dict]


class TravelPlanDeleteResponse(BaseModel):
    """Response after deleting a travel plan."""
    message: str = "Travel plan deleted successfully"
    deleted_plan_id: str
    timestamp: datetime = Field(default_factory=utc_now)
    impact_summary: dict  # e.g., {"lost_tax_savings": 1500.00}
