from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from uuid import uuid4
import uuid
from ..core.utils import utc_now


class DBUser(SQLModel, table=True):
    """Database User model."""
    __tablename__ = "users"
    
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    national_id: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: Optional[datetime] = None
    
    # Relationship to travel plans
    travel_plans: List["DBTravelPlan"] = Relationship(back_populates="user")


class User(SQLModel):
    """Public User model for API responses."""
    id: str
    email: str
    username: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    is_active: bool
    created_at: datetime


class RegisteredUser(SQLModel):
    """User registration input model."""
    email: str
    username: str
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    national_id: Optional[str] = None


class UpdatedUser(SQLModel):
    """User update input model."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[datetime] = None


class ChangedPassword(SQLModel):
    """Password change input model."""
    old_password: str
    new_password: str


class UserLogin(SQLModel):
    """User login input model."""
    username: str
    password: str


class Token(SQLModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(SQLModel):
    """Token data for validation."""
    username: Optional[str] = None
