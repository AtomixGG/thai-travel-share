from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from datetime import timedelta, datetime
from typing import Annotated

from thaitravelshare.core import deps
from thaitravelshare.core.database import get_session
from thaitravelshare.core.security import (
    verify_password, get_password_hash, 
    create_access_token, create_refresh_token
)
from thaitravelshare.core.config import get_settings
from thaitravelshare.core.utils import utc_now
from thaitravelshare import models, schemas

router = APIRouter(prefix="/users", tags=["users"])
settings = get_settings()


@router.post("/register", response_model=schemas.UserRegistrationResponse)
async def register(
    user_info: models.RegisteredUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> schemas.UserRegistrationResponse:
    """Register a new user."""
    
    # Check if email already exists
    result = await session.exec(select(models.DBUser).where(models.DBUser.email == user_info.email))
    if result.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    result = await session.exec(select(models.DBUser).where(models.DBUser.username == user_info.username))
    if result.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_info.password)
    db_user = models.DBUser(
        email=user_info.email,
        username=user_info.username,
        hashed_password=hashed_password,
        first_name=user_info.first_name,
        last_name=user_info.last_name,
        phone=user_info.phone,
        date_of_birth=user_info.date_of_birth,
        national_id=user_info.national_id
    )
    
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    
    # Return public user model with registration response
    user_model = models.User(
        id=db_user.id,
        email=db_user.email,
        username=db_user.username,
        first_name=db_user.first_name,
        last_name=db_user.last_name,
        phone=db_user.phone,
        date_of_birth=db_user.date_of_birth,
        is_active=db_user.is_active,
        created_at=db_user.created_at
    )
    
    return schemas.UserRegistrationResponse(
        user=user_model,
        message="User registered successfully",
        next_steps=[
            "Please verify your email address",
            "Complete your profile information",
            "Start planning your first trip"
        ]
    )


@router.post("/login", response_model=schemas.LoginResponse)
async def login(
    user_login: models.UserLogin,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> schemas.LoginResponse:
    """Login user and return tokens."""
    
    # Get user by username
    result = await session.exec(select(models.DBUser).where(models.DBUser.username == user_login.username))
    user = result.first()
    
    if not user or not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username}, expires_delta=refresh_token_expires
    )
    
    user_model = models.User(
        id=user.id,
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        date_of_birth=user.date_of_birth,
        is_active=user.is_active,
        created_at=user.created_at
    )
    
    return schemas.LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_model
    )


@router.get("/me", response_model=models.User)
def get_me(current_user: models.User = Depends(deps.get_current_user)) -> models.User:
    """Get current user information."""
    return current_user


@router.get("/{user_id}", response_model=models.User)
async def get_user(
    user_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: models.User = Depends(deps.get_current_user),
) -> models.User:
    """Get user by ID."""
    
    user = await session.get(models.DBUser, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Return public user model
    return models.User(
        id=user.id,
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        date_of_birth=user.date_of_birth,
        is_active=user.is_active,
        created_at=user.created_at
    )


@router.put("/{user_id}/change_password")
async def change_password(
    user_id: str,
    password_update: models.ChangedPassword,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: models.User = Depends(deps.get_current_user),
) -> dict:
    """Change user password."""
    
    # Check if user can change this password (must be the same user)
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get user from database
    user = await session.get(models.DBUser, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify old password
    if not verify_password(password_update.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )
    
    # Update password
    user.hashed_password = get_password_hash(password_update.new_password)
    user.updated_at = utc_now()
    
    session.add(user)
    await session.commit()
    
    return {"message": "Password updated successfully"}


@router.put("/{user_id}/update", response_model=models.User)
async def update_user(
    user_id: str,
    user_update: models.UpdatedUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: models.User = Depends(deps.get_current_user),
) -> models.User:
    """Update user information."""
    
    # Check if user can update this profile (must be the same user)
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get user from database
    user = await session.get(models.DBUser, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields if provided
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    user.updated_at = utc_now()
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    # Return updated user
    return models.User(
        id=user.id,
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        date_of_birth=user.date_of_birth,
        is_active=user.is_active,
        created_at=user.created_at
    )
