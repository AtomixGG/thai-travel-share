from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from uuid import uuid4
from decimal import Decimal
import uuid
from ..core.utils import utc_now


class DBProvince(SQLModel, table=True):
    """Database Province model."""
    __tablename__ = "provinces"
    
    id: int = Field(primary_key=True)
    name_th: str = Field(unique=True, index=True)
    name_en: str = Field(unique=True, index=True)
    region: str  # North, Northeast, Central, South
    is_secondary_province: bool = Field(default=False)
    tax_reduction_percentage: Decimal = Field(default=Decimal("0.00"))
    description: Optional[str] = None
    
    # Relationship to travel plans
    travel_plans: List["DBTravelPlan"] = Relationship(back_populates="province")


class Province(SQLModel):
    """Public Province model for API responses."""
    id: int
    name_th: str
    name_en: str
    region: str
    is_secondary_province: bool
    tax_reduction_percentage: Decimal
    description: Optional[str] = None


class DBTravelPlan(SQLModel, table=True):
    """Database Travel Plan model."""
    __tablename__ = "travel_plans"
    
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    province_id: int = Field(foreign_key="provinces.id")
    start_date: datetime
    end_date: datetime
    budget: Optional[Decimal] = None
    estimated_tax_reduction: Optional[Decimal] = None
    status: str = Field(default="planned")  # planned, ongoing, completed, cancelled
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: Optional[datetime] = None
    
    # Relationships
    user: "DBUser" = Relationship(back_populates="travel_plans")
    province: DBProvince = Relationship(back_populates="travel_plans")


class TravelPlan(SQLModel):
    """Public Travel Plan model for API responses."""
    id: str
    user_id: str
    province_id: int
    province: Province
    start_date: datetime
    end_date: datetime
    budget: Optional[Decimal] = None
    estimated_tax_reduction: Optional[Decimal] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime


class CreateTravelPlan(SQLModel):
    """Travel Plan creation input model."""
    province_id: int
    start_date: datetime
    end_date: datetime
    budget: Optional[Decimal] = None
    notes: Optional[str] = None


class UpdateTravelPlan(SQLModel):
    """Travel Plan update input model."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[Decimal] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class TravelPlanWithTaxInfo(SQLModel):
    """Travel Plan with detailed tax reduction information."""
    id: str
    user_id: str
    province: Province
    start_date: datetime
    end_date: datetime
    budget: Optional[Decimal] = None
    estimated_tax_reduction: Optional[Decimal] = None
    actual_tax_savings: Optional[Decimal] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime
