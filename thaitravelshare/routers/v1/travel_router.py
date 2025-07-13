from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from datetime import datetime, timezone
from typing import Annotated, List, Optional
from decimal import Decimal

from thaitravelshare.core import deps
from thaitravelshare.core.database import get_session
from thaitravelshare.core.utils import utc_now
from thaitravelshare import models, schemas

router = APIRouter(prefix="/travel-plans", tags=["travel-plans"])


@router.post("/", response_model=schemas.TravelPlanCreationResponse)
async def create_travel_plan(
    travel_plan: models.CreateTravelPlan,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: models.User = Depends(deps.get_current_user),
) -> schemas.TravelPlanCreationResponse:
    """Create a new travel plan."""
    
    # Verify province exists
    province = await session.get(models.DBProvince, travel_plan.province_id)
    if not province:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Province not found"
        )
    
    # Calculate estimated tax reduction
    estimated_tax_reduction = None
    if travel_plan.budget:
        tax_rate = province.tax_reduction_percentage / 100
        estimated_tax_reduction = travel_plan.budget * tax_rate
    
    # Create travel plan
    db_travel_plan = models.DBTravelPlan(
        user_id=current_user.id,
        province_id=travel_plan.province_id,
        start_date=travel_plan.start_date,
        end_date=travel_plan.end_date,
        budget=travel_plan.budget,
        estimated_tax_reduction=estimated_tax_reduction,
        notes=travel_plan.notes
    )
    
    session.add(db_travel_plan)
    await session.commit()
    await session.refresh(db_travel_plan)
    
    # Return with province information
    province_model = models.Province(
        id=province.id,
        name_th=province.name_th,
        name_en=province.name_en,
        region=province.region,
        is_secondary_province=province.is_secondary_province,
        tax_reduction_percentage=province.tax_reduction_percentage,
        description=province.description
    )
    
    travel_plan_model = models.TravelPlan(
        id=db_travel_plan.id,
        user_id=db_travel_plan.user_id,
        province_id=db_travel_plan.province_id,
        province=province_model,
        start_date=db_travel_plan.start_date,
        end_date=db_travel_plan.end_date,
        budget=db_travel_plan.budget,
        estimated_tax_reduction=db_travel_plan.estimated_tax_reduction,
        status=db_travel_plan.status,
        notes=db_travel_plan.notes,
        created_at=db_travel_plan.created_at
    )
    
    return schemas.TravelPlanCreationResponse(
        travel_plan=travel_plan_model,
        message="Travel plan created successfully",
        tax_benefits={
            "estimated_reduction": float(db_travel_plan.estimated_tax_reduction or 0),
            "tax_rate": float(province.tax_reduction_percentage),
            "is_secondary_province": province.is_secondary_province
        },
        suggestions=[
            f"Visit {province.name_th} during off-peak season for better deals",
            "Consider extending your stay to maximize tax benefits",
            "Keep all receipts for tax deduction claims"
        ]
    )


@router.get("/", response_model=schemas.TravelPlanListResponse)
async def get_user_travel_plans(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: models.User = Depends(deps.get_current_user),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
) -> schemas.TravelPlanListResponse:
    """Get current user's travel plans."""
    
    query = select(models.DBTravelPlan, models.DBProvince).join(
        models.DBProvince
    ).where(models.DBTravelPlan.user_id == current_user.id)
    
    if status_filter:
        query = query.where(models.DBTravelPlan.status == status_filter)
    
    query = query.order_by(models.DBTravelPlan.created_at.desc())
    
    result = await session.exec(query)
    travel_plans_with_provinces = result.all()
    
    travel_plans = []
    for travel_plan, province in travel_plans_with_provinces:
        province_model = models.Province(
            id=province.id,
            name_th=province.name_th,
            name_en=province.name_en,
            region=province.region,
            is_secondary_province=province.is_secondary_province,
            tax_reduction_percentage=province.tax_reduction_percentage,
            description=province.description
        )
        
        travel_plans.append(models.TravelPlan(
            id=travel_plan.id,
            user_id=travel_plan.user_id,
            province_id=travel_plan.province_id,
            province=province_model,
            start_date=travel_plan.start_date,
            end_date=travel_plan.end_date,
            budget=travel_plan.budget,
            estimated_tax_reduction=travel_plan.estimated_tax_reduction,
            status=travel_plan.status,
            notes=travel_plan.notes,
            created_at=travel_plan.created_at
        ))
    
    total_savings = sum(
        float(tp.estimated_tax_reduction or 0) for tp in travel_plans
    )
    
    plans_by_status = {}
    for tp in travel_plans:
        status = tp.status
        plans_by_status[status] = plans_by_status.get(status, 0) + 1
    
    upcoming_trips = [
        tp for tp in travel_plans 
        if tp.start_date.replace(tzinfo=timezone.utc) > utc_now() and tp.status in ["planned", "confirmed"]
    ]
    
    return schemas.TravelPlanListResponse(
        travel_plans=travel_plans,
        total_count=len(travel_plans),
        total_estimated_savings=Decimal(str(total_savings)),
        plans_by_status=plans_by_status,
        upcoming_trips=upcoming_trips[:5]  # Show next 5 upcoming trips
    )


@router.get("/{plan_id}", response_model=models.TravelPlan)
async def get_travel_plan(
    plan_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: models.User = Depends(deps.get_current_user),
) -> models.TravelPlan:
    """Get a specific travel plan."""
    
    query = select(models.DBTravelPlan, models.DBProvince).join(
        models.DBProvince
    ).where(
        models.DBTravelPlan.id == plan_id,
        models.DBTravelPlan.user_id == current_user.id
    )
    
    result = await session.exec(query)
    travel_plan_with_province = result.first()
    
    if not travel_plan_with_province:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel plan not found"
        )
    
    travel_plan, province = travel_plan_with_province
    
    province_model = models.Province(
        id=province.id,
        name_th=province.name_th,
        name_en=province.name_en,
        region=province.region,
        is_secondary_province=province.is_secondary_province,
        tax_reduction_percentage=province.tax_reduction_percentage,
        description=province.description
    )
    
    return models.TravelPlan(
        id=travel_plan.id,
        user_id=travel_plan.user_id,
        province_id=travel_plan.province_id,
        province=province_model,
        start_date=travel_plan.start_date,
        end_date=travel_plan.end_date,
        budget=travel_plan.budget,
        estimated_tax_reduction=travel_plan.estimated_tax_reduction,
        status=travel_plan.status,
        notes=travel_plan.notes,
        created_at=travel_plan.created_at
    )


@router.put("/{plan_id}", response_model=models.TravelPlan)
async def update_travel_plan(
    plan_id: str,
    travel_plan_update: models.UpdateTravelPlan,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: models.User = Depends(deps.get_current_user),
) -> models.TravelPlan:
    """Update a travel plan."""
    
    # Get existing travel plan
    travel_plan = await session.get(models.DBTravelPlan, plan_id)
    if not travel_plan or travel_plan.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel plan not found"
        )
    
    # Update fields if provided
    update_data = travel_plan_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(travel_plan, field, value)
    
    # Recalculate tax reduction if budget was updated
    if "budget" in update_data and travel_plan.budget:
        province = await session.get(models.DBProvince, travel_plan.province_id)
        if province:
            tax_rate = province.tax_reduction_percentage / 100
            travel_plan.estimated_tax_reduction = travel_plan.budget * tax_rate
    
    travel_plan.updated_at = utc_now()
    
    session.add(travel_plan)
    await session.commit()
    await session.refresh(travel_plan)
    
    # Get province information
    province = await session.get(models.DBProvince, travel_plan.province_id)
    province_model = models.Province(
        id=province.id,
        name_th=province.name_th,
        name_en=province.name_en,
        region=province.region,
        is_secondary_province=province.is_secondary_province,
        tax_reduction_percentage=province.tax_reduction_percentage,
        description=province.description
    )
    
    return models.TravelPlan(
        id=travel_plan.id,
        user_id=travel_plan.user_id,
        province_id=travel_plan.province_id,
        province=province_model,
        start_date=travel_plan.start_date,
        end_date=travel_plan.end_date,
        budget=travel_plan.budget,
        estimated_tax_reduction=travel_plan.estimated_tax_reduction,
        status=travel_plan.status,
        notes=travel_plan.notes,
        created_at=travel_plan.created_at
    )


@router.delete("/{plan_id}")
async def delete_travel_plan(
    plan_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: models.User = Depends(deps.get_current_user),
) -> dict:
    """Delete a travel plan."""
    
    travel_plan = await session.get(models.DBTravelPlan, plan_id)
    if not travel_plan or travel_plan.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel plan not found"
        )
    
    await session.delete(travel_plan)
    await session.commit()
    
    return {"message": "Travel plan deleted successfully"}


@router.get("/{plan_id}/tax-info", response_model=models.TravelPlanWithTaxInfo)
async def get_travel_plan_tax_info(
    plan_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: models.User = Depends(deps.get_current_user),
) -> models.TravelPlanWithTaxInfo:
    """Get detailed tax reduction information for a travel plan."""
    
    query = select(models.DBTravelPlan, models.DBProvince).join(
        models.DBProvince
    ).where(
        models.DBTravelPlan.id == plan_id,
        models.DBTravelPlan.user_id == current_user.id
    )
    
    result = await session.exec(query)
    travel_plan_with_province = result.first()
    
    if not travel_plan_with_province:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel plan not found"
        )
    
    travel_plan, province = travel_plan_with_province
    
    # Calculate potential tax savings based on different scenarios
    actual_tax_savings = None
    if travel_plan.budget and travel_plan.status == "completed":
        # For completed trips, show actual savings
        tax_rate = province.tax_reduction_percentage / 100
        actual_tax_savings = travel_plan.budget * tax_rate
    
    province_model = models.Province(
        id=province.id,
        name_th=province.name_th,
        name_en=province.name_en,
        region=province.region,
        is_secondary_province=province.is_secondary_province,
        tax_reduction_percentage=province.tax_reduction_percentage,
        description=province.description
    )
    
    return models.TravelPlanWithTaxInfo(
        id=travel_plan.id,
        user_id=travel_plan.user_id,
        province=province_model,
        start_date=travel_plan.start_date,
        end_date=travel_plan.end_date,
        budget=travel_plan.budget,
        estimated_tax_reduction=travel_plan.estimated_tax_reduction,
        actual_tax_savings=actual_tax_savings,
        status=travel_plan.status,
        notes=travel_plan.notes,
        created_at=travel_plan.created_at
    )
