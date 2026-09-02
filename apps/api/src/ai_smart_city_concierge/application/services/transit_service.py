"""
Transit Application Service
"""
from datetime import datetime, time
from typing import Any
from uuid import UUID

from ...domain.entities.transit import (
    TransitAgency,
    TransitRoute,
    TransitStop,
    TransitTrip,
    TransitVehicle,
)
from ...domain.events.domain_events import (
    TransitRouteCalculatedEvent,
    TransitRouteViewedEvent,
    TransitTripPlannedEvent,
)
from ...domain.repositories.transit_repository import TransitRepository
from ...domain.services.transit_service import TransitService as DomainTransitService
from ...domain.value_objects.coordinates import Coordinates
from ..ports.cache import CachePort
from ..ports.event_publisher import EventPublisher
from ..ports.external_services import TransitServicePort


class TransitApplicationService:
    """Application service for transit management"""

    def __init__(
        self,
        transit_repository: TransitRepository,
        transit_service: DomainTransitService,
        external_transit: TransitServicePort,
        cache: CachePort,
        event_bus: EventPublisher,
    ):
        self.transit_repository = transit_repository
        self.transit_service = transit_service
        self.external_transit = external_transit
        self.cache = cache
        self.event_bus = event_bus

    # Agency management
    async def create_agency(
        self,
        name: str,
        agency_id: str,
        url: str,
        timezone: str,
        language: str | None = None,
        phone: str | None = None,
        fare_url: str | None = None,
        email: str | None = None,
    ) -> TransitAgency:
        """Create a transit agency"""
        agency = TransitAgency(
            name=name,
            agency_id=agency_id,
            url=url,
            timezone=timezone,
            language=language,
            phone=phone,
            fare_url=fare_url,
            email=email,
        )
        return await self.transit_repository.create_agency(agency)

    async def get_agency(self, agency_id: UUID) -> TransitAgency | None:
        """Get transit agency by ID"""
        return await self.transit_repository.get_agency(agency_id)

    async def list_agencies(self, page: int = 1, page_size: int = 20) -> tuple[list[TransitAgency], int]:
        """List transit agencies"""
        return await self.transit_repository.list_agencies(page, page_size)

    # Stop management
    async def create_stop(
        self,
        stop_id: str,
        name: str,
        coordinates: Coordinates,
        agency_id: UUID,
        code: str | None = None,
        desc: str | None = None,
        zone_id: str | None = None,
        stop_url: str | None = None,
        location_type: int = 0,
        parent_station: str | None = None,
        wheelchair_boarding: int = 0,
    ) -> TransitStop:
        """Create a transit stop"""
        stop = TransitStop(
            stop_id=stop_id,
            name=name,
            coordinates=coordinates,
            agency_id=agency_id,
            code=code,
            desc=desc,
            zone_id=zone_id,
            stop_url=stop_url,
            location_type=location_type,
            parent_station=parent_station,
            wheelchair_boarding=wheelchair_boarding,
        )
        return await self.transit_repository.create_stop(stop)

    async def get_stop(self, stop_id: UUID) -> TransitStop | None:
        """Get transit stop by ID"""
        cached = await self.cache.get(f"transit_stop:{stop_id}")
        if cached:
            return cached

        stop = await self.transit_repository.get_stop(stop_id)
        if stop:
            await self.cache.set(f"transit_stop:{stop_id}", stop)
        return stop

    async def get_stops_near(
        self,
        coordinates: Coordinates,
        radius_meters: float = 500,
        limit: int = 50,
    ) -> list[TransitStop]:
        """Get stops near coordinates"""
        return await self.transit_repository.get_stops_near(coordinates, radius_meters, limit)

    async def search_stops(self, query: str, limit: int = 20) -> list[TransitStop]:
        """Search stops by name"""
        return await self.transit_repository.search_stops(query, limit)

    # Route management
    async def create_route(
        self,
        route_id: str,
        agency_id: UUID,
        short_name: str,
        long_name: str,
        route_type: int,
        route_color: str | None = None,
        route_text_color: str | None = None,
    ) -> TransitRoute:
        """Create a transit route"""
        route = TransitRoute(
            route_id=route_id,
            agency_id=agency_id,
            short_name=short_name,
            long_name=long_name,
            route_type=route_type,
            route_color=route_color,
            route_text_color=route_text_color,
        )
        return await self.transit_repository.create_route(route)

    async def get_route(self, route_id: UUID) -> TransitRoute | None:
        """Get transit route by ID"""
        return await self.transit_repository.get_route(route_id)

    async def get_routes_for_agency(self, agency_id: UUID) -> list[TransitRoute]:
        """Get all routes for an agency"""
        return await self.transit_repository.get_routes_for_agency(agency_id)

    # Trip planning
    async def plan_trip(
        self,
        origin: Coordinates,
        destination: Coordinates,
        departure_time: datetime | None = None,
        arrival_time: datetime | None = None,
        max_walk_distance: int = 1000,
        wheelchair_accessible: bool = False,
        bike_allowed: bool = False,
    ) -> list[dict[str, Any]]:
        """Plan a transit trip"""
        # Use external transit service for real-time planning
        trips = await self.external_transit.plan_trip(
            origin=origin,
            destination=destination,
            departure_time=departure_time,
            arrival_time=arrival_time,
            max_walk_distance=max_walk_distance,
            wheelchair_accessible=wheelchair_accessible,
            bike_allowed=bike_allowed,
        )

        # Publish event
        event = TransitTripPlannedEvent.create(
            origin=origin,
            destination=destination,
            trips=trips,
        )
        await self.event_bus.publish(event)

        return trips

    async def get_route_details(self, route_id: UUID) -> dict[str, Any] | None:
        """Get detailed route information"""
        cached = await self.cache.get(f"route_details:{route_id}")
        if cached:
            return cached

        route = await self.get_route(route_id)
        if not route:
            return None

        stops = await self.transit_repository.get_stops_for_route(route_id)
        trips = await self.transit_repository.get_trips_for_route(route_id)

        details = {
            "route": route,
            "stops": stops,
            "trips": trips[:50],  # Limit trips
        }

        await self.cache.set(f"route_details:{route_id}", details)
        return details

    # Real-time
    async def get_real_time_departures(
        self,
        stop_id: UUID,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get real-time departures for a stop"""
        cached = await self.cache.get(f"realtime:{stop_id}")
        if cached:
            return cached[:limit]

        departures = await self.external_transit.get_real_time_departures(stop_id, limit)

        await self.cache.set(f"realtime:{stop_id}", departures, ttl=30)  # 30 second cache

        return departures

    async def get_vehicle_positions(self, route_id: UUID | None = None) -> list[TransitVehicle]:
        """Get real-time vehicle positions"""
        return await self.external_transit.get_vehicle_positions(route_id)

    async def get_service_alerts(self, agency_id: UUID | None = None) -> list[dict[str, Any]]:
        """Get service alerts"""
        return await self.external_transit.get_service_alerts(agency_id)

    # Sync
    async def sync_gtfs_data(self, feed_url: str) -> dict[str, int]:
        """Sync GTFS data from feed"""
        result = await self.external_transit.sync_gtfs(feed_url)

        # Invalidate caches
        await self.cache.delete_pattern("transit_stop:*")
        await self.cache.delete_pattern("route_details:*")
        await self.cache.delete_pattern("realtime:*")

        return result

    async def get_trip(self, trip_id: UUID) -> TransitTrip | None:
        """Get transit trip by ID"""
        return await self.transit_repository.get_trip(trip_id)

    async def get_trips_for_route(self, route_id: UUID) -> list[TransitTrip]:
        """Get trips for a route"""
        return await self.transit_repository.get_trips_for_route(route_id)