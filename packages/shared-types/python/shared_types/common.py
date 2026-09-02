"""
Common Types

Shared common type definitions used across multiple domains.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, time
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class Coordinates(BaseModel):
    """Geographic coordinates."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

    def distance_to(self, other: "Coordinates") -> float:
        """Calculate distance to another coordinate in meters (Haversine formula)."""
        from math import radians, sin, cos, sqrt, atan2

        R = 6371000  # Earth radius in meters
        lat1, lon1 = radians(self.latitude), radians(self.longitude)
        lat2, lon2 = radians(other.latitude), radians(other.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c


class Address(BaseModel):
    """Structured address."""
    street: Optional[str] = None
    street_number: Optional[str] = None
    apartment: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    formatted: Optional[str] = None

    def to_string(self) -> str:
        """Format address as string."""
        parts = []
        if self.street_number and self.street:
            parts.append(f"{self.street_number} {self.street}")
        elif self.street:
            parts.append(self.street)
        if self.apartment:
            parts.append(f"Apt {self.apartment}")
        if self.neighborhood:
            parts.append(self.neighborhood)
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.postal_code:
            parts.append(self.postal_code)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts) if parts else self.formatted or ""


class OpeningHours(BaseModel):
    """Opening hours for a place."""
    monday: Optional[Dict[str, str]] = None  # {"open": "09:00", "close": "18:00"}
    tuesday: Optional[Dict[str, str]] = None
    wednesday: Optional[Dict[str, str]] = None
    thursday: Optional[Dict[str, str]] = None
    friday: Optional[Dict[str, str]] = None
    saturday: Optional[Dict[str, str]] = None
    sunday: Optional[Dict[str, str]] = None
    holidays: Optional[Dict[str, Dict[str, str]]] = None
    timezone: str = "UTC"

    def is_open_now(self) -> Optional[bool]:
        """Check if currently open."""
        from datetime import datetime
        now = datetime.now()
        day = now.strftime("%A").lower()
        hours = getattr(self, day, None)
        if not hours:
            return None
        current_time = now.time()
        open_time = time.fromisoformat(hours.get("open", "00:00"))
        close_time = time.fromisoformat(hours.get("close", "23:59"))
        if open_time <= close_time:
            return open_time <= current_time <= close_time
        else:  # overnight
            return current_time >= open_time or current_time <= close_time


class PriceLevel(str, Enum):
    """Price level categories."""
    FREE = "free"
    BUDGET = "budget"
    MODERATE = "moderate"
    EXPENSIVE = "expensive"
    VERY_EXPENSIVE = "very_expensive"


class AccessibilityInfo(BaseModel):
    """Accessibility information."""
    wheelchair_accessible: Optional[bool] = None
    wheelchair_parking: Optional[bool] = None
    wheelchair_restroom: Optional[bool] = None
    wheelchair_seating: Optional[bool] = None
    visual_aids: Optional[bool] = None
    audio_aids: Optional[bool] = None
    sign_language: Optional[bool] = None
    braille: Optional[bool] = None
    service_animal_friendly: Optional[bool] = None
    sensory_friendly: Optional[bool] = None
    details: Optional[str] = None


class Timezone(str, Enum):
    """Common timezones."""
    UTC = "UTC"
    US_EASTERN = "America/New_York"
    US_CENTRAL = "America/Chicago"
    US_MOUNTAIN = "America/Denver"
    US_PACIFIC = "America/Los_Angeles"
    EUROPE_LONDON = "Europe/London"
    EUROPE_PARIS = "Europe/Paris"
    EUROPE_BERLIN = "Europe/Berlin"
    ASIA_TOKYO = "Asia/Tokyo"
    ASIA_SHANGHAI = "Asia/Shanghai"
    ASIA_SINGAPORE = "Asia/Singapore"
    AUSTRALIA_SYDNEY = "Australia/Sydney"


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class SortParams(BaseModel):
    """Sorting parameters."""
    field: str = "created_at"
    order: str = "desc"  # asc, desc


class FilterParams(BaseModel):
    """Filter parameters."""
    filters: Dict[str, Any] = Field(default_factory=dict)


class DateRange(BaseModel):
    """Date range filter."""
    start: Optional[datetime] = None
    end: Optional[datetime] = None


class GeoBounds(BaseModel):
    """Geographic bounding box."""
    min_latitude: float = Field(..., ge=-90, le=90)
    min_longitude: float = Field(..., ge=-180, le=180)
    max_latitude: float = Field(..., ge=-90, le=90)
    max_longitude: float = Field(..., ge=-180, le=180)

    def contains(self, coords: Coordinates) -> bool:
        return (
            self.min_latitude <= coords.latitude <= self.max_latitude
            and self.min_longitude <= coords.longitude <= self.max_longitude
        )