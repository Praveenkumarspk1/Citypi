"""
Transit Service - Routes, stops, real-time transit data
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, time
from enum import StrEnum
from typing import Any


class TransitSource(StrEnum):
    """Transit data sources"""
    GTFS = "gtfs"
    GTFS_REALTIME = "gtfs_realtime"
    OPENSTREETMAP = "openstreetmap"
    TRANSITLAND = "transitland"
    CITY_API = "city_api"
    CUSTOM = "custom"


class TransitMode(StrEnum):
    """Transit modes"""
    BUS = "bus"
    METRO = "metro"
    SUBWAY = "subway"
    TRAM = "tram"
    LIGHT_RAIL = "light_rail"
    TRAIN = "train"
    COMMUTER_RAIL = "commuter_rail"
    FERRY = "ferry"
    CABLE_CAR = "cable_car"
    GONDOLA = "gondola"
    FUNICULAR = "funicular"


@dataclass(frozen=True)
class Coordinates:
    """Geographic coordinates"""
    latitude: float
    longitude: float

    def to_dict(self) -> dict:
        return {"lat": self.latitude, "lng": self.longitude}


@dataclass(frozen=True)
class TransitStop:
    """Transit stop/station"""
    id: str
    name: str
    coordinates: Coordinates
    code: str | None = None
    zone: str | None = None
    wheelchair_accessible: bool = True
    has_shelter: bool = False
    has_bench: bool = False
    has_realtime_display: bool = False
    routes: list[str] = field(default_factory=list)  # Route IDs serving this stop
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "coordinates": self.coordinates.to_dict(),
            "code": self.code,
            "zone": self.zone,
            "wheelchair_accessible": self.wheelchair_accessible,
            "has_shelter": self.has_shelter,
            "has_bench": self.has_bench,
            "has_realtime_display": self.has_realtime_display,
            "routes": self.routes,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class TransitRoute:
    """Transit route/line"""
    id: str
    short_name: str
    long_name: str
    mode: TransitMode
    color: str | None = None  # Hex color
    text_color: str | None = None  # Hex color for text
    agency_id: str | None = None
    description: str | None = None
    stops: list[str] = field(default_factory=list)  # Stop IDs in order
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "short_name": self.short_name,
            "long_name": self.long_name,
            "mode": self.mode.value,
            "color": self.color,
            "text_color": self.text_color,
            "agency_id": self.agency_id,
            "description": self.description,
            "stops": self.stops,
            "is_active": self.is_active,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class TransitTrip:
    """A specific trip on a route"""
    id: str
    route_id: str
    service_id: str
    headsign: str
    direction_id: int  # 0 or 1
    shape_id: str | None = None
    wheelchair_accessible: bool = True
    bikes_allowed: bool = False
    stop_times: list[dict[str, Any]] = field(default_factory=list)  # stop_id, arrival, departure
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "route_id": self.route_id,
            "service_id": self.service_id,
            "headsign": self.headsign,
            "direction_id": self.direction_id,
            "shape_id": self.shape_id,
            "wheelchair_accessible": self.wheelchair_accessible,
            "bikes_allowed": self.bikes_allowed,
            "stop_times": self.stop_times,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class TransitSchedule:
    """Schedule for a stop"""
    stop_id: str
    route_id: str
    trip_id: str
    arrival_time: time
    departure_time: time
    date: datetime
    realtime: bool = False
    delay_seconds: int = 0
    platform: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "stop_id": self.stop_id,
            "route_id": self.route_id,
            "trip_id": self.trip_id,
            "arrival_time": self.arrival_time.isoformat(),
            "departure_time": self.departure_time.isoformat(),
            "date": self.date.isoformat(),
            "realtime": self.realtime,
            "delay_seconds": self.delay_seconds,
            "platform": self.platform,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class RealtimeArrival:
    """Real-time arrival prediction"""
    stop_id: str
    route_id: str
    trip_id: str
    headsign: str
    scheduled_arrival: datetime
    predicted_arrival: datetime
    delay_seconds: int
    vehicle_id: str | None = None
    occupancy: str | None = None  # empty, many_seats, few_seats, standing, crushed
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "stop_id": self.stop_id,
            "route_id": self.route_id,
            "trip_id": self.trip_id,
            "headsign": self.headsign,
            "scheduled_arrival": self.scheduled_arrival.isoformat(),
            "predicted_arrival": self.predicted_arrival.isoformat(),
            "delay_seconds": self.delay_seconds,
            "vehicle_id": self.vehicle_id,
            "occupancy": self.occupancy,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class TransitAlert:
    """Transit service alert"""
    id: str
    cause: str
    effect: str
    severity: str  # info, warning, severe
    url: str | None = None
    header: str | None = None
    description: str | None = None
    active_period_start: datetime | None = None
    active_period_end: datetime | None = None
    affected_routes: list[str] = field(default_factory=list)
    affected_stops: list[str] = field(default_factory=list)
    informed_entity: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "cause": self.cause,
            "effect": self.effect,
            "severity": self.severity,
            "url": self.url,
            "header": self.header,
            "description": self.description,
            "active_period_start": self.active_period_start.isoformat() if self.active_period_start else None,
            "active_period_end": self.active_period_end.isoformat() if self.active_period_end else None,
            "affected_routes": self.affected_routes,
            "affected_stops": self.affected_stops,
            "informed_entity": self.informed_entity,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class TransitRouteResult:
    """Result of a transit route query"""
    routes: list[TransitRoute]
    total_distance_km: float
    total_duration_minutes: float
    transfers: int
    fare: float | None = None
    currency: str = "USD"
    departure_time: datetime = field(default_factory=datetime.utcnow)
    arrival_time: datetime = field(default_factory=datetime.utcnow)
    walking_distance_m: float = 0
    walking_duration_minutes: float = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "routes": [r.to_dict() for r in self.routes],
            "total_distance_km": self.total_distance_km,
            "total_duration_minutes": self.total_duration_minutes,
            "transfers": self.transfers,
            "fare": self.fare,
            "currency": self.currency,
            "departure_time": self.departure_time.isoformat(),
            "arrival_time": self.arrival_time.isoformat(),
            "walking_distance_m": self.walking_distance_m,
            "walking_duration_minutes": self.walking_duration_minutes,
            "metadata": self.metadata,
        }


class TransitService(ABC):
    """Abstract transit service"""

    @abstractmethod
    async def get_stops_nearby(
        self,
        coordinates: Coordinates,
        radius_meters: float = 500,
        modes: list[TransitMode] | None = None,
    ) -> list[TransitStop]:
        """Get transit stops near coordinates"""
        pass

    @abstractmethod
    async def get_stop_by_id(self, stop_id: str) -> TransitStop | None:
        """Get stop by ID"""
        pass

    @abstractmethod
    async def get_routes_for_stop(self, stop_id: str) -> list[TransitRoute]:
        """Get routes serving a stop"""
        pass

    @abstractmethod
    async def get_route_by_id(self, route_id: str) -> TransitRoute | None:
        """Get route by ID"""
        pass

    @abstractmethod
    async def get_trips_for_route(
        self,
        route_id: str,
        date: datetime | None = None,
        direction_id: int | None = None,
    ) -> list[TransitTrip]:
        """Get trips for a route"""
        pass

    @abstractmethod
    async def get_schedule_for_stop(
        self,
        stop_id: str,
        date: datetime,
        route_ids: list[str] | None = None,
        limit: int = 50,
    ) -> list[TransitSchedule]:
        """Get schedule for a stop"""
        pass

    @abstractmethod
    async def get_realtime_arrivals(
        self,
        stop_id: str,
        route_ids: list[str] | None = None,
        limit: int = 20,
    ) -> list[RealtimeArrival]:
        """Get real-time arrivals for a stop"""
        pass

    @abstractmethod
    async def plan_trip(
        self,
        origin: Coordinates,
        destination: Coordinates,
        departure_time: datetime | None = None,
        arrival_time: datetime | None = None,
        modes: list[TransitMode] | None = None,
        max_walking_distance_m: float = 1000,
        max_transfers: int = 3,
        wheelchair_accessible: bool = False,
    ) -> list[TransitRouteResult]:
        """Plan a transit trip"""
        pass

    @abstractmethod
    async def get_alerts(
        self,
        route_ids: list[str] | None = None,
        stop_ids: list[str] | None = None,
    ) -> list[TransitAlert]:
        """Get transit alerts"""
        pass

    @abstractmethod
    async def get_vehicle_positions(
        self,
        route_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get real-time vehicle positions"""
        pass

    @abstractmethod
    async def get_fare(
        self,
        origin_stop_id: str,
        destination_stop_id: str,
        route_id: str | None = None,
    ) -> float | None:
        """Get fare between stops"""
        pass


class TransitServiceImpl(TransitService):
    """Default implementation of transit service"""

    def __init__(
        self,
        gtfs_client=None,
        gtfs_realtime_client=None,
        transitland_client=None,
        city_api_clients: dict[str, Any] = None,
    ):
        self.gtfs_client = gtfs_client
        self.gtfs_realtime_client = gtfs_realtime_client
        self.transitland_client = transitland_client
        self.city_api_clients = city_api_clients or {}

    async def get_stops_nearby(
        self,
        coordinates: Coordinates,
        radius_meters: float = 500,
        modes: list[TransitMode] | None = None,
    ) -> list[TransitStop]:
        """Get transit stops near coordinates"""
        # Placeholder - would query GTFS/Transitland
        return []

    async def get_stop_by_id(self, stop_id: str) -> TransitStop | None:
        """Get stop by ID"""
        return None

    async def get_routes_for_stop(self, stop_id: str) -> list[TransitRoute]:
        """Get routes serving a stop"""
        return []

    async def get_route_by_id(self, route_id: str) -> TransitRoute | None:
        """Get route by ID"""
        return None

    async def get_trips_for_route(
        self,
        route_id: str,
        date: datetime | None = None,
        direction_id: int | None = None,
    ) -> list[TransitTrip]:
        """Get trips for a route"""
        return []

    async def get_schedule_for_stop(
        self,
        stop_id: str,
        date: datetime,
        route_ids: list[str] | None = None,
        limit: int = 50,
    ) -> list[TransitSchedule]:
        """Get schedule for a stop"""
        return []

    async def get_realtime_arrivals(
        self,
        stop_id: str,
        route_ids: list[str] | None = None,
        limit: int = 20,
    ) -> list[RealtimeArrival]:
        """Get real-time arrivals for a stop"""
        return []

    async def plan_trip(
        self,
        origin: Coordinates,
        destination: Coordinates,
        departure_time: datetime | None = None,
        arrival_time: datetime | None = None,
        modes: list[TransitMode] | None = None,
        max_walking_distance_m: float = 1000,
        max_transfers: int = 3,
        wheelchair_accessible: bool = False,
    ) -> list[TransitRouteResult]:
        """Plan a transit trip"""
        # Placeholder - would use OTP, RAPTOR, or similar algorithm
        return []

    async def get_alerts(
        self,
        route_ids: list[str] | None = None,
        stop_ids: list[str] | None = None,
    ) -> list[TransitAlert]:
        """Get transit alerts"""
        return []

    async def get_vehicle_positions(
        self,
        route_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get real-time vehicle positions"""
        return []

    async def get_fare(
        self,
        origin_stop_id: str,
        destination_stop_id: str,
        route_id: str | None = None,
    ) -> float | None:
        """Get fare between stops"""
        return None
