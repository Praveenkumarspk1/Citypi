"""
Transit Application Use Cases
"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from ...domain.entities.transit import TransitMode, TransitRoute, TransitStop, TransitTrip
from ...domain.repositories.base import PaginatedResult, PaginationParams
from ...domain.repositories.transit_repository import TransitRepository
from ...domain.value_objects.coordinates import Coordinates


@dataclass
class GetRoutesRequest:
    """Request to get transit routes"""
    agency_id: str | None = None
    coordinates: Coordinates | None = None
    radius_meters: float | None = None
    mode: TransitMode | None = None
    pagination: PaginationParams | None = None


@dataclass
class GetStopsRequest:
    """Request to get transit stops"""
    coordinates: Coordinates
    radius_meters: float = 500
    modes: list[TransitMode] | None = None
    accessible_only: bool = False


@dataclass
class GetScheduleRequest:
    """Request to get transit schedule"""
    stop_id: str
    date: date
    route_ids: list[str] | None = None
    limit: int = 50


@dataclass
class GetRealtimeRequest:
    """Request to get real-time transit data"""
    stop_id: str
    route_ids: list[str] | None = None
    limit: int = 20


class TransitUseCases:
    """Transit Application Use Cases"""

    def __init__(
        self,
        transit_repository: TransitRepository,
        transit_service: TransitService,
    ):
        self.transit_repository = transit_repository

    async def get_route(self, route_id: str) -> TransitRoute | None:
        """Get transit route by ID"""
        return await self.transit_repository.get_route_by_id(route_id)

    async def get_routes(self, request: GetRoutesRequest) -> PaginatedResult[TransitRoute]:
        """Get transit routes"""
        return await self.transit_repository.get_routes(
            agency_id=request.agency_id,
            coordinates=request.coordinates,
            radius_meters=request.radius_meters,
            pagination=request.pagination,
        )

    async def get_stop(self, stop_id: str) -> TransitStop | None:
        """Get transit stop by ID"""
        return await self.transit_repository.get_stop_by_id(stop_id)

    async def get_stops_nearby(self, request: GetStopsRequest) -> list[TransitStop]:
        """Get transit stops near coordinates"""
        stops = await self.transit_repository.get_stops_nearby(
            coordinates=request.coordinates,
            radius_meters=request.radius_meters,
            modes=[m.value for m in request.modes] if request.modes else None,
        )

        if request.accessible_only:
            stops = [s for s in stops if s.is_accessible]

        return stops

    async def get_routes_for_stop(self, stop_id: str) -> list[TransitRoute]:
        """Get routes serving a stop"""
        return await self.transit_repository.get_routes_for_stop(stop_id)

    async def get_trips_for_route(
        self,
        route_id: str,
        date: date | None = None,
        direction_id: int | None = None,
    ) -> list[TransitTrip]:
        """Get trips for a route"""
        return await self.transit_repository.get_trips_for_route(
            route_id=route_id,
            date=datetime.combine(date, datetime.min.time()) if date else None,
            direction_id=direction_id,
        )

    async def get_schedule(self, request: GetScheduleRequest) -> list[dict[str, Any]]:
        """Get schedule for a stop"""
        return await self.transit_repository.get_schedule_for_stop(
            stop_id=request.stop_id,
            date=datetime.combine(request.date, datetime.min.time()),
            route_ids=request.route_ids,
            limit=request.limit,
        )

    async def get_realtime_arrivals(self, request: GetRealtimeRequest) -> list[dict[str, Any]]:
        """Get real-time arrivals for a stop"""
        return await self.transit_repository.get_realtime_arrivals(
            stop_id=request.stop_id,
            route_ids=request.route_ids,
            limit=request.limit,
        )

    async def get_alerts(
        self,
        route_ids: list[str] | None = None,
        stop_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get transit alerts"""
        return await self.transit_repository.get_alerts(
            route_ids=route_ids,
            stop_ids=stop_ids,
        )

    async def get_vehicle_positions(
        self,
        route_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get real-time vehicle positions"""
        return await self.transit_repository.get_vehicle_positions(route_ids=route_ids)

    async def plan_trip(
        self,
        origin: Coordinates,
        destination: Coordinates,
        departure_time: datetime | None = None,
        arrival_time: datetime | None = None,
        modes: list[TransitMode] | None = None,
        max_walk_distance: float = 1000,
        wheelchair_accessible: bool = False,
    ) -> list[dict[str, Any]]:
        """Plan a transit trip"""
        return await self.transit_service.plan_trip(
            origin=origin,
            destination=destination,
            departure_time=departure_time,
            arrival_time=arrival_time,
            modes=modes,
            max_walk_distance=max_walk_distance,
            wheelchair_accessible=wheelchair_accessible,
        )

    async def get_next_departures(
        self,
        stop_id: str,
        route_ids: list[str] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get next departures from a stop"""
        return await self.transit_service.get_next_departures(
            stop_id=stop_id,
            route_ids=route_ids,
            limit=limit,
        )

    async def search_routes(
        self,
        query: str,
        coordinates: Coordinates | None = None,
        radius_meters: float | None = None,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[TransitRoute]:
        """Search transit routes"""
        return await self.transit_service.search_routes(
            query=query,
            coordinates=coordinates,
            radius_meters=radius_meters,
            pagination=pagination,
        )
