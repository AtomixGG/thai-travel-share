from ..core.utils import utc_now
from pydantic import Field
"""
Additional API endpoint schemas for health checks and API information.
"""

from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from .common_schemas import StatusEnum


class HealthEndpointResponse(BaseModel):
    """Health check endpoint response."""
    service: str = "Thai Travel Share API"
    status: StatusEnum = StatusEnum.SUCCESS
    timestamp: datetime = Field(default_factory=utc_now)
    version: str = "1.0.0"
    database: dict = {"status": "connected", "tables": ["users", "provinces", "travel_plans"]}
    dependencies: dict = {"fastapi": "0.115.14", "sqlmodel": "0.0.24"}
    uptime: str = "0 days, 0 hours, 0 minutes"


class ApiDocsResponse(BaseModel):
    """API documentation response."""
    api_name: str = "Thai Travel Share API"
    version: str = "1.0.0"
    description: str = "API for planning travel in Thailand with tax reduction calculations"
    base_url: str
    endpoints: dict
    authentication: dict = {
        "type": "Bearer Token (JWT)",
        "login_endpoint": "/v1/users/login",
        "register_endpoint": "/v1/users/register"
    }
    rate_limits: dict = {
        "authenticated": "1000 requests/hour",
        "unauthenticated": "100 requests/hour"
    }


class StatsEndpointResponse(BaseModel):
    """API statistics response."""
    total_users: int
    total_provinces: int
    total_travel_plans: int
    total_tax_savings_calculated: float
    most_popular_provinces: List[dict]
    user_activity_stats: dict
    system_stats: dict
    last_updated: datetime = Field(default_factory=utc_now)
