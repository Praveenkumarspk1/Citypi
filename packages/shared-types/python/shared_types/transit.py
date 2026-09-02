"""
Transit Types

Type definitions for public transit.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, time
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

from .common import Coordinates, Address


class TransitMode(str, Enum):
    """Transit mode types."""
    BUS = "bus"
    METRO = "metro"
    SUBWAY = "subway"
    TRAM = "tram"
    TRAIN = "train"
    FERRY = "ferry"
    CABLE_CAR = "cable_car"
    GONDOLA = "gondola"
    FUNICULAR = "funicular"
    MONORAIL = "monorail"
    TROLLEYBUS = "trolleybus"


class TransitAgency(BaseModel):
    """Transit agency."""
    id: UUID
    name: str
    short_name: Optional[str] = None
    url: Optional[str] = None
    timezone: str
    language: str
    phone: Optional[str] = None
    email: Optional[str] = None
    fare_url: Optional[str] = None
    gtfs_url: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransitRoute(BaseModel):
    """Transit route."""
    id: UUID
    agency_id: UUID
    short_name: str
    long_name: str
    description: Optional[str] = None
    mode: TransitMode
    color: Optional[str] = None
    text_color: Optional[str] = None
    url: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransitStop(BaseModel):
    """Transit stop/station."""
    id: UUID
    agency_id: UUID
    code: Optional[str] = None
    name: str
    description: Optional[str] = None
    coordinates: Coordinates
    address: Optional[Address] = None
    zone: Optional[str] = None
    wheelchair_boarding: Optional[bool] = None
    location_type: int = 0  # 0=stop, 1=station, 2=entrance, 3=generic node
    parent_station: Optional[UUID] = None
    platform_code: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransitVehicle(BaseModel):
    """Transit vehicle real-time position."""
    id: UUID
    agency_id: UUID
    route_id: UUID
    trip_id: Optional[UUID] = None
    vehicle_id: str
    label: Optional[str] = None
    coordinates: Coordinates
    bearing: float  # degrees
    speed: float  # m/s
    occupancy: Optional[str] = None  # empty, many_seats_available, few_seats_available, standing_room_only, crushed_standing_room_only, full, not_accepting_passengers
    timestamp: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransitPrediction(BaseModel):
    """Arrival/departure prediction."""
    id: UUID
    agency_id: UUID
    stop_id: UUID
    route_id: UUID
    trip_id: Optional[UUID] = None
    vehicle_id: Optional[UUID] = None
    scheduled_arrival: datetime
    predicted_arrival: datetime
    scheduled_departure: datetime
    predicted_departure: datetime
    delay_seconds: int = 0
    is_realtime: bool = True
    direction: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransitAlert(BaseModel):
    """Transit service alert."""
    id: UUID
    agency_id: UUID
    route_ids: List[UUID] = Field(default_factory=list)
    stop_ids: List[UUID] = Field(default_factory=list)
    cause: str  # unknown, other_weather, maintenance, construction, etc.
    effect: str  # no_service, reduced_service, significant_delays, detour, etc.
    severity: str  # info, warning, severe
    url: Optional[str] = None
    header: str
    description: str
    summary: Optional[str] = None
    active_period_start: datetime
    active_period_end: Optional[datetime] = None
    informed_entities: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransitTrip(BaseModel):
    """Transit trip."""
    id: UUID
    agency_id: UUID
    route_id: UUID
    service_id: str
    headsign: Optional[str] = None
    short_name: Optional[str] = None
    direction: int  # 0 or 1
    block_id: Optional[str] = None
    shape_id: Optional[UUID] = None
    wheelchair_accessible: int = 0
    bikes_allowed: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransitStopTime(BaseModel):
    """Transit stop time."""
    id: UUID
    agency_id: UUID
    trip_id: UUID
    stop_id: UUID
    arrival_time: time
    departure_time: time
    stop_sequence: int
    pickup_type: int = 0
    drop_off_type: int = 0
    shape_dist_traveled: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransitPath(BaseModel):
    """Transit path/route between two points."""
    id: UUID
    origin: Coordinates
    destination: Coordinates
    origin_name: Optional[str] = None
    destination_name: Optional[str] = None
    distance_meters: float
    duration_minutes: int
    transfers: int
    fare: Optional[float] = None
    currency: str = "USD"
    legs: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)