from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, text
from typing import Annotated
import time
from datetime import datetime

from thaitravelshare import models, schemas
from thaitravelshare.core.database import get_session
from thaitravelshare.schemas.endpoint_schemas import HealthEndpointResponse, ApiDocsResponse, StatsEndpointResponse

router = APIRouter(prefix="/system", tags=["system"])

# Store server start time
server_start_time = time.time()


@router.get("/health", response_model=HealthEndpointResponse)
async def health_check(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> HealthEndpointResponse:
    """Check API health status."""
    
    try:
        # Test database connection
        await session.exec(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    # Calculate uptime
    uptime_seconds = int(time.time() - server_start_time)
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    minutes = (uptime_seconds % 3600) // 60
    uptime_str = f"{days} days, {hours} hours, {minutes} minutes"
    
    return HealthEndpointResponse(
        database={"status": db_status, "tables": ["users", "provinces", "travel_plans"]},
        uptime=uptime_str
    )


@router.get("/info", response_model=ApiDocsResponse)
async def api_info() -> ApiDocsResponse:
    """Get API information and documentation."""
    
    endpoints = {
        "authentication": {
            "POST /v1/users/register": "Register a new user",
            "POST /v1/users/login": "User login",
            "GET /v1/users/me": "Get current user info"
        },
        "provinces": {
            "GET /v1/provinces/": "Get all provinces",
            "GET /v1/provinces/secondary": "Get secondary provinces",
            "GET /v1/provinces/{id}/tax-benefits": "Calculate tax benefits"
        },
        "travel_plans": {
            "POST /v1/travel-plans/": "Create travel plan",
            "GET /v1/travel-plans/": "Get user's travel plans",
            "PUT /v1/travel-plans/{id}": "Update travel plan"
        }
    }
    
    return ApiDocsResponse(
        base_url="http://localhost:8000",
        endpoints=endpoints
    )


@router.get("/stats", response_model=StatsEndpointResponse)
async def get_stats(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> StatsEndpointResponse:
    """Get API usage statistics."""
    
    # Count total users
    user_result = await session.exec(select(models.DBUser))
    total_users = len(user_result.all())
    
    # Count total provinces
    province_result = await session.exec(select(models.DBProvince))
    provinces = province_result.all()
    total_provinces = len(provinces)
    
    # Count total travel plans
    travel_plan_result = await session.exec(select(models.DBTravelPlan))
    travel_plans = travel_plan_result.all()
    total_travel_plans = len(travel_plans)
    
    # Calculate total tax savings
    total_savings = sum(
        float(tp.estimated_tax_reduction or 0) for tp in travel_plans
    )
    
    # Most popular provinces (by travel plan count)
    province_counts = {}
    for tp in travel_plans:
        province_counts[tp.province_id] = province_counts.get(tp.province_id, 0) + 1
    
    most_popular = []
    for province in provinces:
        count = province_counts.get(province.id, 0)
        if count > 0:
            most_popular.append({
                "province_id": province.id,
                "name_th": province.name_th,
                "name_en": province.name_en,
                "travel_plan_count": count
            })
    
    most_popular.sort(key=lambda x: x["travel_plan_count"], reverse=True)
    
    return StatsEndpointResponse(
        total_users=total_users,
        total_provinces=total_provinces,
        total_travel_plans=total_travel_plans,
        total_tax_savings_calculated=total_savings,
        most_popular_provinces=most_popular[:5],
        user_activity_stats={
            "active_users": sum(1 for user in user_result.all() if user.is_active),
            "users_with_plans": len(set(tp.user_id for tp in travel_plans))
        },
        system_stats={
            "server_uptime_seconds": int(time.time() - server_start_time),
            "database_tables": 3
        }
    )
