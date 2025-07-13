from ..core.utils import utc_now
from pydantic import Field
"""
Common response schemas used across the Thai Travel Share API.
"""

from typing import Optional, Any, List
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class StatusEnum(str, Enum):
    """Status enum for API responses."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ErrorResponse(BaseModel):
    """Standard error response."""
    status: StatusEnum = StatusEnum.ERROR
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=utc_now)
    path: Optional[str] = None
    suggestions: Optional[List[str]] = None


class SuccessResponse(BaseModel):
    """Standard success response."""
    status: StatusEnum = StatusEnum.SUCCESS
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=utc_now)


class ValidationErrorResponse(BaseModel):
    """Response for validation errors."""
    status: StatusEnum = StatusEnum.ERROR
    detail: str = "Validation error"
    errors: List[dict]  # List of field-specific errors
    timestamp: datetime = Field(default_factory=utc_now)


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    page: int
    per_page: int
    total: int
    pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel):
    """Generic paginated response."""
    data: List[Any]
    meta: PaginationMeta
    status: StatusEnum = StatusEnum.SUCCESS


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=utc_now)
    version: str = "1.0.0"
    database_status: str = "connected"
    uptime_seconds: Optional[int] = None


class ApiInfoResponse(BaseModel):
    """API information response."""
    name: str = "Thai Travel Share API"
    version: str = "1.0.0"
    description: str = "API for Thai travel planning with tax reduction calculations"
    endpoints: dict
    features: List[str] = [
        "User authentication",
        "Province information",
        "Tax reduction calculations",
        "Travel planning",
        "Trip management"
    ]
    support_contact: str = "support@thaitravelshare.com"


class BatchOperationResponse(BaseModel):
    """Response for batch operations."""
    total_processed: int
    successful: int
    failed: int
    errors: List[dict]
    success_items: List[Any]
    failed_items: List[dict]
    processing_time_ms: int


class FileUploadResponse(BaseModel):
    """Response for file upload operations."""
    filename: str
    file_size: int
    file_type: str
    upload_url: str
    status: StatusEnum = StatusEnum.SUCCESS
    message: str = "File uploaded successfully"
    timestamp: datetime = Field(default_factory=utc_now)
