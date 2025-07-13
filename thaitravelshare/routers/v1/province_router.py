from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from typing import Annotated, List, Optional

from thaitravelshare.core import deps
from thaitravelshare.core.database import get_session
from thaitravelshare import models, schemas

router = APIRouter(prefix="/provinces", tags=["provinces"])


@router.get("/", response_model=schemas.ProvinceListResponse)
async def get_all_provinces(
    session: Annotated[AsyncSession, Depends(get_session)],
    region: Optional[str] = Query(None, description="Filter by region"),
    secondary_only: Optional[bool] = Query(None, description="Show only secondary provinces"),
) -> schemas.ProvinceListResponse:
    """Get all provinces with optional filtering."""
    
    query = select(models.DBProvince)
    
    if region:
        query = query.where(models.DBProvince.region == region)
    
    if secondary_only is not None:
        query = query.where(models.DBProvince.is_secondary_province == secondary_only)
    
    query = query.order_by(models.DBProvince.tax_reduction_percentage.desc(), models.DBProvince.name_th)
    
    result = await session.exec(query)
    provinces = result.all()
    
    provinces_list = [
        models.Province(
            id=province.id,
            name_th=province.name_th,
            name_en=province.name_en,
            region=province.region,
            is_secondary_province=province.is_secondary_province,
            tax_reduction_percentage=province.tax_reduction_percentage,
            description=province.description
        )
        for province in provinces
    ]
    
    secondary_count = sum(1 for p in provinces if p.is_secondary_province)
    all_regions = list(set(p.region for p in provinces))
    
    return schemas.ProvinceListResponse(
        provinces=provinces_list,
        total_count=len(provinces_list),
        secondary_province_count=secondary_count,
        regions=sorted(all_regions),
        metadata={
            "description": "List of Thai provinces with tax reduction information",
            "last_updated": "2025-07-13",
            "filter_applied": {
                "region": region,
                "secondary_only": secondary_only
            }
        }
    )


@router.get("/secondary", response_model=schemas.SecondaryProvinceResponse)
async def get_secondary_provinces(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> schemas.SecondaryProvinceResponse:
    """Get all secondary provinces with higher tax reduction rates."""
    
    query = select(models.DBProvince).where(
        models.DBProvince.is_secondary_province == True
    ).order_by(models.DBProvince.tax_reduction_percentage.desc())
    
    result = await session.exec(query)
    provinces = result.all()
    
    provinces_list = [
        models.Province(
            id=province.id,
            name_th=province.name_th,
            name_en=province.name_en,
            region=province.region,
            is_secondary_province=province.is_secondary_province,
            tax_reduction_percentage=province.tax_reduction_percentage,
            description=province.description
        )
        for province in provinces
    ]
    
    if provinces_list:
        avg_reduction = sum(p.tax_reduction_percentage for p in provinces_list) / len(provinces_list)
        highest_reduction = max(provinces_list, key=lambda p: p.tax_reduction_percentage)
    else:
        avg_reduction = 0
        highest_reduction = None
    
    return schemas.SecondaryProvinceResponse(
        provinces=provinces_list,
        total_count=len(provinces_list),
        average_tax_reduction=avg_reduction,
        highest_reduction_province=highest_reduction,
        benefits_summary={
            "total_provinces": len(provinces_list),
            "average_savings_rate": f"{avg_reduction:.2f}%",
            "range": f"{min(p.tax_reduction_percentage for p in provinces_list) if provinces_list else 0:.2f}% - {max(p.tax_reduction_percentage for p in provinces_list) if provinces_list else 0:.2f}%"
        }
    )


@router.get("/regions", response_model=List[str])
async def get_regions(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> List[str]:
    """Get all available regions."""
    
    query = select(models.DBProvince.region).distinct()
    result = await session.exec(query)
    regions = result.all()
    
    return sorted(regions)


@router.get("/{province_id}", response_model=models.Province)
async def get_province(
    province_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> models.Province:
    """Get a specific province by ID."""
    
    province = await session.get(models.DBProvince, province_id)
    if not province:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Province not found"
        )
    
    return models.Province(
        id=province.id,
        name_th=province.name_th,
        name_en=province.name_en,
        region=province.region,
        is_secondary_province=province.is_secondary_province,
        tax_reduction_percentage=province.tax_reduction_percentage,
        description=province.description
    )


@router.get("/{province_id}/tax-benefits")
async def get_province_tax_benefits(
    province_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    budget: float = Query(..., description="Travel budget in THB"),
) -> dict:
    """Calculate potential tax benefits for a given budget in this province."""
    
    province = await session.get(models.DBProvince, province_id)
    if not province:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Province not found"
        )
    
    tax_reduction_rate = float(province.tax_reduction_percentage) / 100
    estimated_tax_reduction = budget * tax_reduction_rate
    
    # Calculate comparison with other provinces
    all_provinces_query = select(models.DBProvince)
    result = await session.exec(all_provinces_query)
    all_provinces = result.all()
    
    comparisons = []
    for other_province in all_provinces:
        other_rate = float(other_province.tax_reduction_percentage) / 100
        other_reduction = budget * other_rate
        difference = other_reduction - estimated_tax_reduction
        
        comparisons.append({
            "province_id": other_province.id,
            "province_name": other_province.name_th,
            "tax_reduction_percentage": other_province.tax_reduction_percentage,
            "estimated_reduction": other_reduction,
            "difference": difference,
            "is_better": difference > 0
        })
    
    # Sort by tax reduction amount (highest first)
    comparisons.sort(key=lambda x: x["estimated_reduction"], reverse=True)
    
    return {
        "province": {
            "id": province.id,
            "name_th": province.name_th,
            "name_en": province.name_en,
            "tax_reduction_percentage": province.tax_reduction_percentage,
            "is_secondary_province": province.is_secondary_province
        },
        "budget": budget,
        "estimated_tax_reduction": estimated_tax_reduction,
        "tax_reduction_rate": tax_reduction_rate,
        "comparison_with_other_provinces": comparisons[:10],  # Top 10 alternatives
        "savings_info": {
            "monthly_savings": estimated_tax_reduction / 12,
            "annual_potential": estimated_tax_reduction,
            "is_secondary_province_benefit": province.is_secondary_province
        }
    }
