"""
Itinerary Types

Type definitions for travel itineraries.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

from .common import Coordinates, Address, PriceLevel, AccessibilityInfo
from .user import TransportMode


class ItineraryStatus(str, Enum):
    """Itinerary status."""
    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ItineraryPace(str, Enum):
    """Itinerary pace."""
    RELAXED = "relaxed"
    MODERATE = "moderate"
    FAST = "fast"


class ItineraryItemType(str, Enum):
    """Itinerary item type."""
    POI = "poi"
    TRANSIT = "transit"
    MEAL = "meal"
    ACTIVITY = "activity"
    REST = "rest"
    ACCOMMODATION = "accommodation"
    TRANSFER = "transfer"
    FREE_TIME = "free_time"


class ItineraryItem(BaseModel):
    """Single itinerary item."""
    id: UUID
    day_id: UUID
    type: ItineraryItemType
    title: str
    description: Optional[str] = None
    start_time: time
    end_time: time
    duration_minutes: int
    poi_id: Optional[UUID] = None
    coordinates: Optional[Coordinates] = None
    address: Optional[Address] = None
    transport_mode: Optional[TransportMode] = None
    transport_details: Dict[str, Any] = Field(default_factory=dict)
    cost_estimate: Optional[float] = None
    currency: str = "USD"
    booking_url: Optional[str] = None
    booking_reference: Optional[str] = None
    notes: Optional[str] = None
    order: int = 0
    is_flexible: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ItineraryDay(BaseModel):
    """Single day in itinerary."""
    id: UUID
    itinerary_id: UUID
    date: date
    title: Optional[str] = None
    notes: Optional[str] = None
    start_time: time = time(9, 0)
    end_time: time = time(22, 0)
    base_location: Optional[Coordinates] = None
    base_address: Optional[Address] = None
    items: List[ItineraryItem] = Field(default_factory=list)
    total_cost: float = 0.0
    currency: str = "USD"
    weather_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Itinerary(BaseModel):
    """Travel itinerary."""
    id: UUID
    user_id: UUID
    title: str
    description: Optional[str] = None
    status: ItineraryStatus = ItineraryStatus.DRAFT
    pace: ItineraryPace = ItineraryPace.MODERATE
    start_date: date
    end_date: date
    city: str
    country: str
    base_location: Optional[Coordinates] = None
    base_address: Optional[Address] = None
    interests: List[str] = Field(default_factory=list)
    budget_level: Optional[PriceLevel] = None
    accessibility_needs: List[str] = Field(default_factory=list)
    dietary_restrictions: List[str] = Field(default_factory=list)
    transport_preferences: List[TransportMode] = Field(default_factory=list)
    total_cost_estimate: float = 0.0
    currency: str = "USD"
    days: List[ItineraryDay] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ItineraryCreate(BaseModel):
    """Itinerary creation request."""
    user_id: UUID
    title: str
    description: Optional[str] = None
    pace: ItineraryPace = ItineraryPace.MODERATE
    start_date: date
    end_date: date
    city: str
    country: str
    base_location: Optional[Coordinates] = None
    base_address: Optional[Address] = None
    interests: List[str] = Field(default_factory=list)
    budget_level: Optional[PriceLevel] = None
    accessibility_needs: List[str] = Field(default_factory=list)
    dietary_restrictions: List[str] = Field(default_factory=list)
    transport_preferences: List[TransportMode] = Field(default_factory=list)


class ItineraryUpdate(BaseModel):
    """Itinerary update request."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ItineraryStatus] = None
    pace: Optional[ItineraryPace] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    base_location: Optional[Coordinates] = None
    base_address: Optional[Address] = None
    interests: Optional[List[str]] = None
    budget_level: Optional[PriceLevel] = None
    accessibility_needs: Optional[List[str]] = None
    dietary_restrictions: Optional[List[str]] = None
    transport_preferences: Optional[List[TransportMode]] = None


class ItineraryResponse(BaseModel):
    """Itinerary response with computed fields."""
    id: UUID
    user_id: UUID
    title: str
    description: Optional[str] = None
    status: ItineraryStatus
    pace: ItineraryPace
    start_date: date
    end_date: date
    city: str
    country: str
    base_location: Optional[Coordinates] = None
    base_address: Optional[Address] = None
    interests: List[str]
    budget_level: Optional[PriceLevel] = None
    accessibility_needs: List[str]
    dietary_restrictions: List[str]
    transport_preferences: List[TransportMode]
    total_cost_estimate: float
    currency: str
    days: List[ItineraryDay]
    day_count: int
    total_items: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ItineraryGenerateRequest(BaseModel):
    """Request to generate an itinerary."""
    user_id: UUID
    title: str
    description: Optional[str] = None
    start_date: date
    end_date: date
    city: str
    country: str
    base_location: Coordinates
    base_address: str
    interests: List[str]
    budget_level: str = "moderate"
    pace: ItineraryPace = ItineraryPace.MODERATE
    accessibility_needs: List[str] = Field(default_factory=list)
    dietary_restrictions: List[str] = Field(default_factory=list)
    transport_preferences: List[TransportMode] = Field(default_factory=list)


class ItineraryShare(BaseModel):
    """Itinerary sharing request."""
    itinerary_id: UUID
    recipient_emails: List[str]
    message: Optional[str] = None
    permission: str = "view"  # view, edit