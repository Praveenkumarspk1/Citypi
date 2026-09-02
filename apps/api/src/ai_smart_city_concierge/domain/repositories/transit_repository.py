"""
Transit Repository Interface
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import UUID

from ..entities.transit import (
    Agency,
    Fare,
    RealtimeAlert,
    RealtimeTripUpdate,
    RealtimeVehiclePosition,
    Route,
    ServiceCalendar,
    ServiceException,
    Shape,
    Stop,
    StopTime,
    TransitRoute,
    Trip,
)
from ..value_objects.coordinates import Coordinates
from .base import FilterParams, PaginatedResult, PaginationParams


class TransitRepository(ABC):
    """Transit repository interface"""

    # Agency
    @abstractmethod
    async def get_agency(self, agency_id: str) -> Agency | None:
        pass

    @abstractmethod
    async def get_agencies(self) -> list[Agency]:
        pass

    @abstractmethod
    async def upsert_agency(self, agency: Agency) -> Agency:
        pass

    # Stops
    @abstractmethod
    async def get_stop(self, stop_id: str) -> Stop | None:
        pass

    @abstractmethod
    async def get_stops(
        self,
        pagination: PaginationParams | None = None,
        filters: FilterParams | None = None,
    ) -> PaginatedResult[Stop]:
        pass

    @abstractmethod
    async def get_stops_nearby(
        self,
        coordinates: Coordinates,
        radius_meters: float = 1000,
        limit: int = 50,
    ) -> list[Stop]:
        pass

    @abstractmethod
    async def get_stops_by_route(self, route_id: str) -> list[Stop]:
        pass

    @abstractmethod
    async def upsert_stop(self, stop: Stop) -> Stop:
        pass

    @abstractmethod
    async def bulk_upsert_stops(self, stops: list[Stop]) -> list[Stop]:
        pass

    # Routes
    @abstractmethod
    async def get_route(self, route_id: str) -> Route | None:
        pass

    @abstractmethod
    async def get_routes(
        self,
        agency_id: str | None = None,
        route_type: int | None = None,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Route]:
        pass

    @abstractmethod
    async def get_routes_by_stop(self, stop_id: str) -> list[Route]:
        pass

    @abstractmethod
    async def upsert_route(self, route: Route) -> Route:
        pass

    @abstractmethod
    async def bulk_upsert_routes(self, routes: list[Route]) -> list[Route]:
        pass

    # Trips
    @abstractmethod
    async def get_trip(self, trip_id: str) -> Trip | None:
        pass

    @abstractmethod
    async def get_trips_by_route(self, route_id: str, service_id: str | None = None) -> list[Trip]:
        pass

    @abstractmethod
    async def get_trips_by_stop(self, stop_id: str, date: datetime) -> list[Trip]:
        pass

    @abstractmethod
    async def upsert_trip(self, trip: Trip) -> Trip:
        pass

    @abstractmethod
    async def bulk_upsert_trips(self, trips: list[Trip]) -> list[Trip]:
        pass

    # Stop Times
    @abstractmethod
    async def get_stop_times(self, trip_id: str) -> list[StopTime]:
        pass

    @abstractmethod
    async def upsert_stop_time(self, stop_time: StopTime) -> StopTime:
        pass

    @abstractmethod
    async def bulk_upsert_stop_times(self, stop_times: list[StopTime]) -> list[StopTime]:
        pass

    # Service Calendar
    @abstractmethod
    async def get_service_calendar(self, service_id: str) -> ServiceCalendar | None:
        pass

    @abstractmethod
    async def get_active_services(self, date: datetime) -> list[ServiceCalendar]:
        pass

    @abstractmethod
    async def upsert_service_calendar(self, calendar: ServiceCalendar) -> ServiceCalendar:
        pass

    @abstractmethod
    async def get_service_exceptions(self, service_id: str) -> list[ServiceException]:
        pass

    @abstractmethod
    async def upsert_service_exception(self, exception: ServiceException) -> ServiceException:
        pass

    # Shapes
    @abstractmethod
    async def get_shape(self, shape_id: str) -> Shape | None:
        pass

    @abstractmethod
    async def upsert_shape(self, shape: Shape) -> Shape:
        pass

    # Fares
    @abstractmethod
    async def get_fare(self, fare_id: str) -> Fare | None:
        pass

    @abstractmethod
    async def get_fares_by_route(self, route_id: str) -> list[Fare]:
        pass

    @abstractmethod
    async def upsert_fare(self, fare: Fare) -> Fare:
        pass

    # Real-time
    @abstractmethod
    async def get_vehicle_positions(
        self,
        route_id: str | None = None,
        since: datetime | None = None,
    ) -> list[RealtimeVehiclePosition]:
        pass

    @abstractmethod
    async def upsert_vehicle_position(self, position: RealtimeVehiclePosition) -> RealtimeVehiclePosition:
        pass

    @abstractmethod
    async def bulk_upsert_vehicle_positions(self, positions: list[RealtimeVehiclePosition]) -> list[RealtimeVehiclePosition]:
        pass

    @abstractmethod
    async def get_trip_updates(
        self,
        route_id: str | None = None,
        since: datetime | None = None,
    ) -> list[RealtimeTripUpdate]:
        pass

    @abstractmethod
    async def upsert_trip_update(self, update: RealtimeTripUpdate) -> RealtimeTripUpdate:
        pass

    @abstractmethod
    async def get_alerts(
        self,
        route_id: str | None = None,
        stop_id: str | None = None,
        active_only: bool = True,
    ) -> list[RealtimeAlert]:
        pass

    @abstractmethod
    async def upsert_alert(self, alert: RealtimeAlert) -> RealtimeAlert:
        pass

    # Computed routes
    @abstractmethod
    async def save_computed_route(self, route: TransitRoute) -> TransitRoute:
        pass

    @abstractmethod
    async def get_computed_route(self, route_id: UUID) -> TransitRoute | None:
        pass

    @abstractmethod
    async def get_recent_routes(
        self,
        user_id: UUID | None = None,
        limit: int = 20,
    ) -> list[TransitRoute]:
        pass

    # GTFS Import
    @abstractmethod
    async def import_gtfs_feed(
        self,
        agency_id: str,
        feed_data: dict[str, Any],
    ) -> dict[str, int]:
        pass

    @abstractmethod
    async def clear_agency_data(self, agency_id: str) -> None:
        pass

    @abstractmethod
    async def get_import_stats(self, agency_id: str) -> dict[str, Any]:
        pass
