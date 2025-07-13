from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

from ..models.user_model import User
from ..core.utils import utc_now


class UserResponse(BaseModel):
    """Standard user response."""
    user: User
    message: Optional[str] = None


class UserListResponse(BaseModel):
    """Response for user list (admin use)."""
    users: list[User]
    total_count: int
    active_count: int


class UserRegistrationResponse(BaseModel):
    """Response after successful user registration."""
    user: User
    message: str = "User registered successfully"
    next_steps: list[str] = [
        "Please verify your email address",
        "Complete your profile information",
        "Start planning your first trip"
    ]


class LoginResponse(BaseModel):
    """Response after successful login."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: User


class PasswordChangeResponse(BaseModel):
    """Response after password change."""
    message: str = "Password updated successfully"
    timestamp: datetime = Field(default_factory=utc_now)
    security_tip: str = "Remember to keep your password secure and don't share it with anyone"


class ProfileUpdateResponse(BaseModel):
    """Response after profile update."""
    user: User
    message: str = "Profile updated successfully"
    updated_fields: list[str]
    timestamp: datetime = Field(default_factory=utc_now)
