"""
API Response Schemas
Pydantic models for API response serialization.
"""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: UUID
    email: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    locale: str = "en"
    timezone: str = "UTC"
    email_verified: bool = False
    role: str = "user"
    status: str = "active"
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    content_type: str = "text"
    metadata: dict[str, Any] = {}
    created_at: datetime


class ConversationResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: Optional[str] = None
    status: str = "active"
    message_count: int = 0
    last_message_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ItineraryResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    description: Optional[str] = None
    status: str = "draft"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class POIResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    category: str
    latitude: float
    longitude: float
    address: Optional[dict[str, Any]] = None
    rating: Optional[float] = None
    review_count: int = 0
    tags: list[str] = []


class TransitRouteResponse(BaseModel):
    route_id: str
    duration_minutes: int
    transfers: int
    steps: list[dict[str, Any]]
    fare: Optional[float] = None


class WeatherResponse(BaseModel):
    lat: float
    lng: float
    temperature: Optional[float] = None
    humidity: Optional[int] = None
    wind_speed: Optional[float] = None
    weather_description: Optional[str] = None
    forecast: list[dict[str, Any]] = []


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    timestamp: datetime


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


class ErrorResponse(BaseModel):
    error: dict[str, Any]


class WSMessageResponse(BaseModel):
    type: str
    payload: dict[str, Any]
