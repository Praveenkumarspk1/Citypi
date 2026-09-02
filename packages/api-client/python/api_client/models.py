"""
Models

Re-exports shared types for convenience.
"""
from shared_types import *

# Additional API-specific models
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class PaginationParams(BaseModel):
    """Pagination parameters for API requests."""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class SortParams(BaseModel):
    """Sorting parameters."""
    field: str = "created_at"
    order: str = "desc"


class FilterParams(BaseModel):
    """Filter parameters."""
    filters: Dict[str, Any] = Field(default_factory=dict)


class DateRange(BaseModel):
    """Date range filter."""
    start: Optional[datetime] = None
    end: Optional[datetime] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error: str
    code: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseModel):
    """Standard success response."""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int