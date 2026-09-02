"""
POI Types

Type definitions for Points of Interest.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

from .common import Coordinates, Address, OpeningHours, PriceLevel, AccessibilityInfo


class POICategory(str, Enum):
    """POI categories."""
    ATTRACTION = "attraction"
    RESTAURANT = "restaurant"
    CAFE = "cafe"
    BAR = "bar"
    HOTEL = "hotel"
    HOSTEL = "hostel"
    MUSEUM = "museum"
    PARK = "park"
    SHOPPING = "shopping"
    ENTERTAINMENT = "entertainment"
    HEALTH = "health"
    TRANSPORT = "transport"
    SERVICE = "service"
    LANDMARK = "landmark"
    NATURE = "nature"
    CULTURAL = "cultural"
    RELIGIOUS = "religious"
    EDUCATIONAL = "educational"
    SPORTS = "sports"
    NIGHTLIFE = "nightlife"
    FOOD = "food"
    DRINK = "drink"
    ACCOMMODATION = "accommodation"
    OTHER = "other"


class POIType(str, Enum):
    """POI type classification."""
    POINT = "point"
    AREA = "area"
    BUILDING = "building"
    ENTRANCE = "entrance"
    STOP = "stop"
    STATION = "station"


class POI(BaseModel):
    """Point of Interest entity."""
    id: UUID
    name: str
    description: Optional[str] = None
    category: POICategory
    poi_type: POIType = POIType.POINT
    coordinates: Coordinates
    address: Optional[Address] = None
    opening_hours: Optional[OpeningHours] = None
    price_level: Optional[PriceLevel] = None
    rating: Optional[float] = Field(None, ge=0, le=5)
    review_count: int = 0
    accessibility: Optional[AccessibilityInfo] = None
    tags: List[str] = Field(default_factory=list)
    amenities: List[str] = Field(default_factory=list)
    cuisines: List[str] = Field(default_factory=list)
    dietary_options: List[str] = Field(default_factory=list)
    phone: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    source: str = "manual"
    source_id: Optional[str] = None
    is_verified: bool = False
    is_active: bool = True
    popularity_score: float = 0.0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class POICreate(BaseModel):
    """POI creation request."""
    name: str
    description: Optional[str] = None
    category: POICategory
    poi_type: POIType = POIType.POINT
    coordinates: Coordinates
    address: Optional[Address] = None
    opening_hours: Optional[OpeningHours] = None
    price_level: Optional[PriceLevel] = None
    tags: List[str] = Field(default_factory=list)
    amenities: List[str] = Field(default_factory=list)
    cuisines: List[str] = Field(default_factory=list)
    dietary_options: List[str] = Field(default_factory=list)
    phone: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    accessibility: Optional[AccessibilityInfo] = None


class POIUpdate(BaseModel):
    """POI update request."""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[POICategory] = None
    coordinates: Optional[Coordinates] = None
    address: Optional[Address] = None
    opening_hours: Optional[OpeningHours] = None
    price_level: Optional[PriceLevel] = None
    tags: Optional[List[str]] = None
    amenities: Optional[List[str]] = None
    cuisines: Optional[List[str]] = None
    dietary_options: Optional[List[str]] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    accessibility: Optional[AccessibilityInfo] = None
    is_active: Optional[bool] = None


class POIResponse(BaseModel):
    """POI response with computed fields."""
    id: UUID
    name: str
    description: Optional[str] = None
    category: POICategory
    poi_type: POIType
    coordinates: Coordinates
    address: Optional[Address] = None
    opening_hours: Optional[OpeningHours] = None
    price_level: Optional[PriceLevel] = None
    rating: Optional[float] = None
    review_count: int
    accessibility: Optional[AccessibilityInfo] = None
    tags: List[str]
    amenities: List[str]
    cuisines: List[str]
    dietary_options: List[str]
    phone: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    images: List[str]
    distance_meters: Optional[float] = None
    duration_minutes: Optional[float] = None
    is_open_now: Optional[bool] = None
    popularity_score: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class POISearchParams(BaseModel):
    """POI search parameters."""
    query: Optional[str] = None
    category: Optional[POICategory] = None
    categories: Optional[List[POICategory]] = None
    coordinates: Optional[Coordinates] = None
    radius_meters: int = 5000
    bounds: Optional[Dict[str, float]] = None  # min_lat, min_lng, max_lat, max_lng
    price_levels: Optional[List[PriceLevel]] = None
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    tags: Optional[List[str]] = None
    amenities: Optional[List[str]] = None
    cuisines: Optional[List[str]] = None
    dietary_options: Optional[List[str]] = None
    accessibility_needs: Optional[List[str]] = None
    is_open_now: Optional[bool] = None
    is_verified: Optional[bool] = None
    sort_by: str = "popularity"
    sort_order: str = "desc"
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)