"""
Itinerary Domain Entity
"""
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from ..value_objects.coordinates import Coordinates
from .poi import POI


class ItineraryStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class ItineraryItemType(StrEnum):
    POI = "poi"
    TRANSIT = "transit"
    BREAK = "break"
    CUSTOM = "custom"
    ACCOMMODATION = "accommodation"
    MEAL = "meal"

# Alias for backward compatibility
ItemType = ItineraryItemType


class ItineraryVisibility(StrEnum):
    PRIVATE = "private"
    SHARED = "shared"
    PUBLIC = "public"



class TransportMode(StrEnum):
    WALKING = "walking"
    CYCLING = "cycling"
    DRIVING = "driving"
    TRANSIT = "transit"
    TAXI = "taxi"
    RIDESHARE = "rideshare"


@dataclass
class ItineraryItem:
    """Individual item in an itinerary"""
    id: UUID = field(default_factory=uuid4)
    type: ItineraryItemType = ItineraryItemType.POI
    sequence: int = 0

    # POI reference
    poi_id: UUID | None = None
    poi: POI | None = None

    # Custom item details (for non-POI items)
    title: str = ""
    description: str | None = None
    coordinates: Coordinates | None = None
    address: str | None = None

    # Timing
    start_time: time | None = None
    end_time: time | None = None
    duration_minutes: int = 0

    # Transit info (for transit items)
    transport_mode: TransportMode | None = None
    transit_details: dict[str, Any] = field(default_factory=dict)
    from_location: Coordinates | None = None
    to_location: Coordinates | None = None

    # Cost
    estimated_cost: float = 0.0
    currency: str = "USD"

    # Notes
    notes: str | None = None
    is_flexible: bool = True  # Can be moved in schedule
    is_required: bool = False  # Must-visit

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def get_duration(self) -> timedelta:
        """Get duration as timedelta"""
        return timedelta(minutes=self.duration_minutes)

    def set_time_range(self, start: time, end: time) -> None:
        """Set time range and calculate duration"""
        self.start_time = start
        self.end_time = end
        start_dt = datetime.combine(datetime.today(), start)
        end_dt = datetime.combine(datetime.today(), end)
        if end_dt < start_dt:
            end_dt += timedelta(days=1)
        self.duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "type": self.type.value,
            "sequence": self.sequence,
            "poi_id": str(self.poi_id) if self.poi_id else None,
            "poi": self.poi.to_dict() if self.poi else None,
            "title": self.title,
            "description": self.description,
            "coordinates": self.coordinates.to_dict() if self.coordinates else None,
            "address": self.address,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_minutes": self.duration_minutes,
            "transport_mode": self.transport_mode.value if self.transport_mode else None,
            "transit_details": self.transit_details,
            "from_location": self.from_location.to_dict() if self.from_location else None,
            "to_location": self.to_location.to_dict() if self.to_location else None,
            "estimated_cost": self.estimated_cost,
            "currency": self.currency,
            "notes": self.notes,
            "is_flexible": self.is_flexible,
            "is_required": self.is_required,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class ItineraryDay:
    """A single day in an itinerary"""
    id: UUID = field(default_factory=uuid4)
    date: datetime = field(default_factory=datetime.utcnow)
    sequence: int = 0

    # Items for this day
    items: list[ItineraryItem] = field(default_factory=list)

    # Day metadata
    title: str | None = None
    notes: str | None = None
    start_time: time = field(default_factory=lambda: time(9, 0))
    end_time: time = field(default_factory=lambda: time(22, 0))

    # Location context
    base_location: Coordinates | None = None
    base_address: str | None = None

    # Summary
    total_duration_minutes: int = 0
    total_cost: float = 0.0
    total_distance_meters: float = 0.0

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_item(self, item: ItineraryItem) -> None:
        """Add item to day"""
        item.sequence = len(self.items)
        self.items.append(item)
        self._recalculate()

    def remove_item(self, item_id: UUID) -> bool:
        """Remove item from day"""
        for i, item in enumerate(self.items):
            if item.id == item_id:
                self.items.pop(i)
                self._recalculate()
                return True
        return False

    def reorder_items(self, item_ids: list[UUID]) -> None:
        """Reorder items by ID list"""
        item_map = {item.id: item for item in self.items}
        self.items = [item_map[id_] for id_ in item_ids if id_ in item_map]
        for i, item in enumerate(self.items):
            item.sequence = i
        self._recalculate()

    def _recalculate(self) -> None:
        """Recalculate day totals"""
        self.total_duration_minutes = sum(item.duration_minutes for item in self.items)
        self.total_cost = sum(item.estimated_cost for item in self.items)
        self.updated_at = datetime.utcnow()

    def get_available_slots(self, min_duration: int = 30) -> list[tuple[time, time]]:
        """Get available time slots for new items"""
        slots = []
        current = self.start_time

        for item in sorted(self.items, key=lambda x: x.start_time or time(0, 0)):
            if item.start_time and current < item.start_time:
                gap = datetime.combine(datetime.today(), item.start_time) - datetime.combine(datetime.today(), current)
                if gap.total_seconds() / 60 >= min_duration:
                    slots.append((current, item.start_time))
            if item.end_time:
                current = item.end_time

        # Check after last item
        if current < self.end_time:
            gap = datetime.combine(datetime.today(), self.end_time) - datetime.combine(datetime.today(), current)
            if gap.total_seconds() / 60 >= min_duration:
                slots.append((current, self.end_time))

        return slots

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "date": self.date.date().isoformat(),
            "sequence": self.sequence,
            "title": self.title,
            "notes": self.notes,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "base_location": self.base_location.to_dict() if self.base_location else None,
            "base_address": self.base_address,
            "items": [item.to_dict() for item in self.items],
            "total_duration_minutes": self.total_duration_minutes,
            "total_cost": self.total_cost,
            "total_distance_meters": self.total_distance_meters,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class Itinerary:
    """
    Itinerary aggregate root.
    Represents a multi-day travel plan.
    """
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str | None = None
    status: ItineraryStatus = ItineraryStatus.DRAFT

    # Dates
    start_date: datetime = field(default_factory=datetime.utcnow)
    end_date: datetime = field(default_factory=datetime.utcnow)

    # Days
    days: list[ItineraryDay] = field(default_factory=list)

    # Preferences
    budget_level: str = "moderate"  # budget, moderate, luxury
    pace: str = "moderate"  # relaxed, moderate, packed
    interests: list[str] = field(default_factory=list)
    accessibility_needs: list[str] = field(default_factory=list)
    dietary_restrictions: list[str] = field(default_factory=list)
    transport_preferences: list[TransportMode] = field(default_factory=list)

    # Location context
    base_location: Coordinates | None = None
    base_address: str | None = None
    city: str | None = None
    country: str | None = None

    # Sharing
    is_public: bool = False
    share_token: str | None = None
    collaborators: list[UUID] = field(default_factory=list)

    # Metadata
    total_estimated_cost: float = 0.0
    total_distance_meters: float = 0.0
    poi_count: int = 0
    tags: list[str] = field(default_factory=list)

    # AI generation metadata
    generated_by_ai: bool = False
    generation_prompt: str | None = None
    generation_model: str | None = None
    generation_tokens: int = 0

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    published_at: datetime | None = None
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.title:
            raise ValueError("Itinerary title is required")
        if self.end_date < self.start_date:
            raise ValueError("End date must be after start date")

    def add_day(self, date: datetime, **kwargs) -> ItineraryDay:
        """Add a day to the itinerary"""
        day = ItineraryDay(
            date=date,
            sequence=len(self.days),
            **kwargs
        )
        self.days.append(day)
        self._recalculate()
        return day

    def get_day(self, date: datetime) -> ItineraryDay | None:
        """Get day by date"""
        for day in self.days:
            if day.date.date() == date.date():
                return day
        return None

    def get_or_create_day(self, date: datetime) -> ItineraryDay:
        """Get existing day or create new one"""
        day = self.get_day(date)
        if not day:
            day = self.add_day(date)
        return day

    def remove_day(self, day_id: UUID) -> bool:
        """Remove a day"""
        for i, day in enumerate(self.days):
            if day.id == day_id:
                self.days.pop(i)
                self._recalculate()
                return True
        return False

    def _recalculate(self) -> None:
        """Recalculate itinerary totals"""
        self.total_estimated_cost = sum(day.total_cost for day in self.days)
        self.total_distance_meters = sum(day.total_distance_meters for day in self.days)
        self.poi_count = sum(
            1 for day in self.days
            for item in day.items
            if item.type == ItineraryItemType.POI
        )
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Activate itinerary"""
        self.status = ItineraryStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def complete(self) -> None:
        """Mark itinerary as completed"""
        self.status = ItineraryStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def cancel(self) -> None:
        """Cancel itinerary"""
        self.status = ItineraryStatus.CANCELLED
        self.updated_at = datetime.utcnow()

    def archive(self) -> None:
        """Archive itinerary"""
        self.status = ItineraryStatus.ARCHIVED
        self.updated_at = datetime.utcnow()

    def publish(self, share_token: str) -> None:
        """Publish itinerary publicly"""
        self.is_public = True
        self.share_token = share_token
        self.published_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def add_collaborator(self, user_id: UUID) -> None:
        """Add collaborator"""
        if user_id not in self.collaborators:
            self.collaborators.append(user_id)
            self.updated_at = datetime.utcnow()

    def remove_collaborator(self, user_id: UUID) -> None:
        """Remove collaborator"""
        if user_id in self.collaborators:
            self.collaborators.remove(user_id)
            self.updated_at = datetime.utcnow()

    def get_all_items(self) -> list[ItineraryItem]:
        """Get all items across all days"""
        items = []
        for day in self.days:
            items.extend(day.items)
        return items

    def get_pois(self) -> list[POI]:
        """Get all POIs in itinerary"""
        pois = []
        for day in self.days:
            for item in day.items:
                if item.type == ItineraryItemType.POI and item.poi:
                    pois.append(item.poi)
        return pois

    def to_dict(self, include_days: bool = True) -> dict:
        data = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "start_date": self.start_date.date().isoformat(),
            "end_date": self.end_date.date().isoformat(),
            "budget_level": self.budget_level,
            "pace": self.pace,
            "interests": self.interests,
            "accessibility_needs": self.accessibility_needs,
            "dietary_restrictions": self.dietary_restrictions,
            "transport_preferences": [t.value for t in self.transport_preferences],
            "base_location": self.base_location.to_dict() if self.base_location else None,
            "base_address": self.base_address,
            "city": self.city,
            "country": self.country,
            "is_public": self.is_public,
            "share_token": self.share_token,
            "collaborators": [str(uid) for uid in self.collaborators],
            "total_estimated_cost": self.total_estimated_cost,
            "total_distance_meters": self.total_distance_meters,
            "poi_count": self.poi_count,
            "tags": self.tags,
            "generated_by_ai": self.generated_by_ai,
            "generation_prompt": self.generation_prompt,
            "generation_model": self.generation_model,
            "generation_tokens": self.generation_tokens,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
        if include_days:
            data["days"] = [day.to_dict() for day in self.days]
        return data

    def to_geojson(self) -> dict:
        """Export as GeoJSON FeatureCollection"""
        features = []
        for day in self.days:
            for item in day.items:
                if item.coordinates:
                    features.append({
                        "type": "Feature",
                        "geometry": item.coordinates.to_geojson(),
                        "properties": {
                            "id": str(item.id),
                            "day": day.sequence,
                            "sequence": item.sequence,
                            "type": item.type.value,
                            "title": item.title or (item.poi.name if item.poi else ""),
                            "start_time": item.start_time.isoformat() if item.start_time else None,
                            "end_time": item.end_time.isoformat() if item.end_time else None,
                        }
                    })
        return {
            "type": "FeatureCollection",
            "features": features
        }
