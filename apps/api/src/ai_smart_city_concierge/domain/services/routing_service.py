"""
Routing Service - Multi-modal routing domain service
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum

from ..entities.transit import TransitRoute
from ..value_objects.coordinates import Coordinates
from ..value_objects.transport_mode import TransportMode, TransportModeType


class RoutingStrategy(StrEnum):
    """Routing strategy options"""
    FASTEST = "fastest"
    SHORTEST = "shortest"
    CHEAPEST = "cheapest"
    ECO_FRIENDLY = "eco_friendly"
    MOST_ACCESSIBLE = "most_accessible"
    BALANCED = "balanced"


@dataclass(frozen=True)
class RouteRequest:
    """Route calculation request"""
    origin: Coordinates
    destination: Coordinates
    waypoints: list[Coordinates] = None
    preferred_modes: list[TransportModeType] = None
    avoided_modes: list[TransportModeType] = None
    strategy: RoutingStrategy = RoutingStrategy.BALANCED
    departure_time: str | None = None  # ISO datetime
    arrival_time: str | None = None  # ISO datetime
    max_walking_distance_m: float = 1000
    max_transfers: int = 3
    wheelchair_accessible: bool = False
    avoid_stairs: bool = False
    avoid_high_traffic: bool = False

    def __post_init__(self):
        if self.waypoints is None:
            object.__setattr__(self, 'waypoints', [])
        if self.preferred_modes is None:
            object.__setattr__(self, 'preferred_modes', [])
        if self.avoided_modes is None:
            object.__setattr__(self, 'avoided_modes', [])


@dataclass(frozen=True)
class RouteSegment:
    """A single segment of a route"""
    mode: TransportMode
    origin: Coordinates
    destination: Coordinates
    distance_km: float
    duration_minutes: float
    cost: float
    co2_g: float
    instructions: str
    polyline: str | None = None  # Encoded polyline
    transit_details: dict | None = None  # Route number, stops, etc.

    def to_dict(self) -> dict:
        return {
            "mode": self.mode.to_dict(),
            "origin": self.origin.to_dict(),
            "destination": self.destination.to_dict(),
            "distance_km": self.distance_km,
            "duration_minutes": self.duration_minutes,
            "cost": self.cost,
            "co2_g": self.co2_g,
            "instructions": self.instructions,
            "polyline": self.polyline,
            "transit_details": self.transit_details,
        }


@dataclass(frozen=True)
class RouteResult:
    """Complete route calculation result"""
    request: RouteRequest
    segments: list[RouteSegment]
    total_distance_km: float
    total_duration_minutes: float
    total_cost: float
    total_co2_g: float
    modes_used: list[TransportModeType]
    is_accessible: bool
    warnings: list[str] = None
    alternatives: list["RouteResult"] = None

    def __post_init__(self):
        if self.warnings is None:
            object.__setattr__(self, 'warnings', [])
        if self.alternatives is None:
            object.__setattr__(self, 'alternatives', [])

    @property
    def primary_mode(self) -> TransportModeType:
        """Get the primary transport mode by distance"""
        if not self.segments:
            return TransportModeType.WALKING
        max_segment = max(self.segments, key=lambda s: s.distance_km)
        return max_segment.mode.type

    def to_dict(self) -> dict:
        return {
            "request": {
                "origin": self.request.origin.to_dict(),
                "destination": self.request.destination.to_dict(),
                "strategy": self.request.strategy.value,
            },
            "segments": [s.to_dict() for s in self.segments],
            "total_distance_km": self.total_distance_km,
            "total_duration_minutes": self.total_duration_minutes,
            "total_cost": self.total_cost,
            "total_co2_g": self.total_co2_g,
            "modes_used": [m.value for m in self.modes_used],
            "is_accessible": self.is_accessible,
            "warnings": self.warnings,
            "alternatives_count": len(self.alternatives) if self.alternatives else 0,
        }


class RoutingService(ABC):
    """Abstract routing service for multi-modal route calculation"""

    @abstractmethod
    async def calculate_route(self, request: RouteRequest) -> RouteResult:
        """Calculate optimal route based on request"""
        pass

    @abstractmethod
    async def calculate_alternatives(
        self,
        request: RouteRequest,
        count: int = 3
    ) -> list[RouteResult]:
        """Calculate alternative routes"""
        pass

    @abstractmethod
    async def get_transit_routes(
        self,
        origin: Coordinates,
        destination: Coordinates,
        departure_time: str | None = None,
    ) -> list[TransitRoute]:
        """Get public transit routes between points"""
        pass

    @abstractmethod
    async def get_walking_route(
        self,
        origin: Coordinates,
        destination: Coordinates,
    ) -> RouteSegment:
        """Get walking-only route"""
        pass

    @abstractmethod
    async def get_cycling_route(
        self,
        origin: Coordinates,
        destination: Coordinates,
        avoid_hills: bool = False,
    ) -> RouteSegment:
        """Get cycling route"""
        pass

    @abstractmethod
    async def get_driving_route(
        self,
        origin: Coordinates,
        destination: Coordinates,
        avoid_tolls: bool = False,
        avoid_highways: bool = False,
    ) -> RouteSegment:
        """Get driving route"""
        pass

    @abstractmethod
    async def estimate_fare(
        self,
        origin: Coordinates,
        destination: Coordinates,
        mode: TransportModeType,
    ) -> float:
        """Estimate fare for a route"""
        pass

    @abstractmethod
    async def get_route_polyline(self, route: RouteResult) -> str:
        """Get encoded polyline for route visualization"""
        pass


class RoutingServiceImpl(RoutingService):
    """Default implementation of routing service"""

    def __init__(
        self,
        osm_client=None,  # OpenStreetMap/OSRM client
        gtfs_client=None,  # GTFS transit client
        mapbox_client=None,  # Mapbox client
        google_maps_client=None,  # Google Maps client
    ):
        self.osm_client = osm_client
        self.gtfs_client = gtfs_client
        self.mapbox_client = mapbox_client
        self.google_maps_client = google_maps_client

    async def calculate_route(self, request: RouteRequest) -> RouteResult:
        """Calculate optimal route using available providers"""
        # This is a placeholder implementation
        # In production, this would call external routing APIs

        # For now, return a simple walking route as fallback
        walking_mode = TransportModes.WALKING
        distance_km = request.origin.distance_km_to(request.destination)
        duration = walking_mode.estimate_time(distance_km)

        segment = RouteSegment(
            mode=walking_mode,
            origin=request.origin,
            destination=request.destination,
            distance_km=distance_km,
            duration_minutes=duration,
            cost=0.0,
            co2_g=0.0,
            instructions=f"Walk from {request.origin} to {request.destination}",
        )

        return RouteResult(
            request=request,
            segments=[segment],
            total_distance_km=distance_km,
            total_duration_minutes=duration,
            total_cost=0.0,
            total_co2_g=0.0,
            modes_used=[TransportModeType.WALKING],
            is_accessible=True,
        )

    async def calculate_alternatives(
        self,
        request: RouteRequest,
        count: int = 3
    ) -> list[RouteResult]:
        """Calculate alternative routes"""
        primary = await self.calculate_route(request)
        return [primary]  # Placeholder

    async def get_transit_routes(
        self,
        origin: Coordinates,
        destination: Coordinates,
        departure_time: str | None = None,
    ) -> list[TransitRoute]:
        """Get public transit routes"""
        # Placeholder - would integrate with GTFS/transit APIs
        return []

    async def get_walking_route(
        self,
        origin: Coordinates,
        destination: Coordinates,
    ) -> RouteSegment:
        """Get walking-only route"""
        walking_mode = TransportModes.WALKING
        distance_km = origin.distance_km_to(destination)
        duration = walking_mode.estimate_time(distance_km)

        return RouteSegment(
            mode=walking_mode,
            origin=origin,
            destination=destination,
            distance_km=distance_km,
            duration_minutes=duration,
            cost=0.0,
            co2_g=0.0,
            instructions=f"Walk from {origin} to {destination}",
        )

    async def get_cycling_route(
        self,
        origin: Coordinates,
        destination: Coordinates,
        avoid_hills: bool = False,
    ) -> RouteSegment:
        """Get cycling route"""
        cycling_mode = TransportModes.CYCLING
        distance_km = origin.distance_km_to(destination)
        duration = cycling_mode.estimate_time(distance_km)

        return RouteSegment(
            mode=cycling_mode,
            origin=origin,
            destination=destination,
            distance_km=distance_km,
            duration_minutes=duration,
            cost=0.0,
            co2_g=0.0,
            instructions=f"Cycle from {origin} to {destination}",
        )

    async def get_driving_route(
        self,
        origin: Coordinates,
        destination: Coordinates,
        avoid_tolls: bool = False,
        avoid_highways: bool = False,
    ) -> RouteSegment:
        """Get driving route"""
        driving_mode = TransportModes.CAR
        distance_km = origin.distance_km_to(destination)
        duration = driving_mode.estimate_time(distance_km)
        cost = float(driving_mode.estimate_cost(distance_km))
        co2 = driving_mode.estimate_co2(distance_km)

        return RouteSegment(
            mode=driving_mode,
            origin=origin,
            destination=destination,
            distance_km=distance_km,
            duration_minutes=duration,
            cost=cost,
            co2_g=co2,
            instructions=f"Drive from {origin} to {destination}",
        )

    async def estimate_fare(
        self,
        origin: Coordinates,
        destination: Coordinates,
        mode: TransportModeType,
    ) -> float:
        """Estimate fare for a route"""
        transport_mode = TransportModes.by_type(mode)
        if not transport_mode:
            return 0.0

        distance_km = origin.distance_km_to(destination)
        return float(transport_mode.estimate_cost(distance_km))

    async def get_route_polyline(self, route: RouteResult) -> str:
        """Get encoded polyline for route visualization"""
        # Placeholder - would generate actual polyline from segments
        return ""


# Import at bottom to avoid circular imports
from ..value_objects.transport_mode import TransportModes
