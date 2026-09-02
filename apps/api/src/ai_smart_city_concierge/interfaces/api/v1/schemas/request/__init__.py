"""
API Request Schemas
Pydantic models for API request validation.
"""
from typing import Optional

from pydantic import BaseModel, Field


class CreateUserRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    display_name: Optional[str] = Field(None, max_length=100)


class UserLoginRequest(BaseModel):
    email: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UpdateUserProfileRequest(BaseModel):
    display_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None
    locale: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)


class UpdateUserPreferencesRequest(BaseModel):
    interests: Optional[list[str]] = None
    budget_level: Optional[str] = Field(None, pattern="^(budget|moderate|luxury)$")
    accessibility_needs: Optional[list[str]] = None
    dietary_restrictions: Optional[list[str]] = None
    preferred_transport_modes: Optional[list[str]] = None


class StartConversationRequest(BaseModel):
    initial_message: str = Field(..., min_length=1, max_length=4000)
    context: Optional[dict] = None


class AddMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=8000)
    content_type: str = Field(default="text", pattern="^(text|voice|image)$")
    attachments: Optional[list[dict]] = None


class UpdateConversationRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, pattern="^(active|archived|deleted)$")


class CreateItineraryRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    timezone: Optional[str] = "UTC"


class UpdateItineraryRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|published|archived)$")


class POISearchRequest(BaseModel):
    query: Optional[str] = None
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lng: Optional[float] = Field(None, ge=-180, le=180)
    radius: float = Field(default=1000, gt=0, le=50000)
    category: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)


class TransitRouteRequest(BaseModel):
    origin_lat: float = Field(..., ge=-90, le=90)
    origin_lng: float = Field(..., ge=-180, le=180)
    destination_lat: float = Field(..., ge=-90, le=90)
    destination_lng: float = Field(..., ge=-180, le=180)
    departure_time: Optional[str] = None
    preferences: Optional[dict] = None


class WeatherRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    days: int = Field(default=7, ge=1, le=16)


class MediaUploadRequest(BaseModel):
    file_type: str = Field(..., pattern="^(audio|image)$")
    mime_type: str = Field(...)


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
