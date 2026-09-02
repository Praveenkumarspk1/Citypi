"""
Integration tests for TransitRepository
"""
import pytest
from datetime import datetime, time, timezone, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from ai_smart_city_concierge.infrastructure.persistence.sqlalchemy.repositories.transit_repository import TransitRepository
from ai_smart_city_concierge.domain.aggregates.transit_aggregate import TransitAggregate
from ai_smart_city_concierge.domain.value_objects.coordinates import Coordinates
from ai_smart_city_concierge.domain.value_objects.transport_mode import TransportMode


@pytest.mark.asyncio
class TestTransitRepository:
    """Integration tests for TransitRepository"""

    async def test_save_and_get_route(self, db_session: AsyncSession):
        """Test saving and retrieving a transit route"""
        repo = TransitRepository(db_session)

        route = TransitAggregate.create_route(
            route_id="R1",
            name="Red Line",
            short_name="R",
            description="Main north-south line",
            transport_mode=TransportMode.SUBWAY,
            color="#FF0000",
            text_color="#FFFFFF",
        )

        route.add_stop(
            stop_id="S1",
            name="Central Station",
            coordinates=Coordinates(latitude=40.7128, longitude=-74.0060),
            stop_order=1,
            is_accessible=True,
        )
        route.add_stop(
            stop_id="S2",
            name="Downtown",
            coordinates=Coordinates(latitude=40.72, longitude=-74.01),
            stop_order=2,
            is_accessible=True,
        )

        await repo.save_route(route)
        await db_session.commit()

        # Retrieve the route
        retrieved = await repo.get_route_by_id("R1")
        assert retrieved is not None
        assert retrieved.route_id == "R1"
        assert retrieved.name == "Red Line"
        assert retrieved.transport_mode == TransportMode.SUBWAY
        assert len(retrieved.stops) == 2
        assert retrieved.stops[0].stop_id == "S1"
        assert retrieved.stops[1].stop_id == "S2"

    async def test_get_routes_by_transport_mode(self, db_session: AsyncSession):
        """Test getting routes by transport mode"""
        repo = TransitRepository(db_session)

        subway_route = TransitAggregate.create_route(
            route_id="R1", name="Red Line", transport_mode=TransportMode.SUBWAY
        )
        bus_route = TransitAggregate.create_route(
            route_id="R2", name="Bus 101", transport_mode=TransportMode.BUS
        )
        tram_route = TransitAggregate.create_route(
            route_id="R3", name="Tram 1", transport_mode=TransportMode.TRAM
        )

        await repo.save_route(subway_route)
        await repo.save_route(bus_route)
        await repo.save_route(tram_route)
        await db_session.commit()

        subway_routes = await repo.get_routes_by_transport_mode(TransportMode.SUBWAY)
        bus_routes = await repo.get_routes_by_transport_mode(TransportMode.BUS)

        assert len(subway_routes) == 1
        assert subway_routes[0].route_id == "R1"
        assert len(bus_routes) == 1
        assert bus_routes[0].route_id == "R2"

    async def test_get_active_routes(self, db_session: AsyncSession):
        """Test getting active routes"""
        repo = TransitRepository(db_session)

        active_route = TransitAggregate.create_route(
            route_id="R1", name="Active Route", transport_mode=TransportMode.SUBWAY
        )
        inactive_route = TransitAggregate.create_route(
            route_id="R2", name="Inactive Route", transport_mode=TransportMode.BUS
        )
        inactive_route.deactivate()

        await repo.save_route(active_route)
        await repo.save_route(inactive_route)
        await db_session.commit()

        active_routes = await repo.get_active_routes()
        assert len(active_routes) == 1
        assert active_routes[0].route_id == "R1"
        assert active_routes[0].is_active is True

    async def test_update_route(self, db_session: AsyncSession):
        """Test updating a route"""
        repo = TransitRepository(db_session)

        route = TransitAggregate.create_route(
            route_id="R1",
            name="Original Name",
            transport_mode=TransportMode.SUBWAY,
        )
        route.add_stop(
            stop_id="S1",
            name="Stop 1",
            coordinates=Coordinates(40.7, -74.0),
            stop_order=1,
        )
        await repo.save_route(route)
        await db_session.commit()

        # Update route
        route.add_stop(
            stop_id="S2",
            name="Stop 2",
            coordinates=Coordinates(40.71, -74.01),
            stop_order=2,
        )
        route.create_service_alert(
            alert_id="A1",
            cause="construction",
            effect="delay",
            severity="moderate",
            description="Maintenance work",
            affected_routes=["R1"],
            active_period_start=datetime.now(timezone.utc),
            active_period_end=datetime.now(timezone.utc) + timedelta(hours=4),
        )

        await repo.save_route(route)
        await db_session.commit()

        # Verify update
        retrieved = await repo.get_route_by_id("R1")
        assert len(retrieved.stops) == 2
        assert retrieved.stops[1].stop_id == "S2"
        assert len(retrieved.service_alerts) == 1
        assert retrieved.service_alerts[0].alert_id == "A1"

    async def test_delete_route(self, db_session: AsyncSession):
        """Test deleting a route"""
        repo = TransitRepository(db_session)

        route = TransitAggregate.create_route(
            route_id="R1",
            name="To Delete",
            transport_mode=TransportMode.SUBWAY,
        )
        await repo.save_route(route)
        await db_session.commit()

        # Delete route
        await repo.delete_route("R1")
        await db_session.commit()

        # Verify deletion
        retrieved = await repo.get_route_by_id("R1")
        assert retrieved is None

    async def test_save_and_get_vehicle_position(self, db_session: AsyncSession):
        """Test saving and retrieving vehicle positions"""
        repo = TransitRepository(db_session)

        route = TransitAggregate.create_route(
            route_id="R1",
            name="Red Line",
            transport_mode=TransportMode.SUBWAY,
        )
        route.add_stop(stop_id="S1", name="Stop 1", coordinates=Coordinates(40.7, -74.0), stop_order=1)
        route.add_stop(stop_id="S2", name="Stop 2", coordinates=Coordinates(40.71, -74.01), stop_order=2)
        await repo.save_route(route)
        await db_session.commit()

        # Update vehicle position
        position = Coordinates(latitude=40.705, longitude=-74.005)
        timestamp = datetime.now(timezone.utc)
        route.update_vehicle_position(
            vehicle_id="V1",
            position=position,
            current_stop_id="S1",
            next_stop_id="S2",
            occupancy=0.7,
            timestamp=timestamp,
        )
        await repo.save_route(route)
        await db_session.commit()

        # Retrieve vehicle positions
        vehicles = await repo.get_vehicle_positions("R1")
        assert len(vehicles) == 1
        assert vehicles[0].vehicle_id == "V1"
        assert vehicles[0].position.latitude == 40.705
        assert vehicles[0].current_stop_id == "S1"

    async def test_get_active_alerts(self, db_session: AsyncSession):
        """Test getting active service alerts"""
        repo = TransitRepository(db_session)

        route = TransitAggregate.create_route(
            route_id="R1",
            name="Red Line",
            transport_mode=TransportMode.SUBWAY,
        )
        now = datetime.now(timezone.utc)
        route.create_service_alert(
            alert_id="A1",
            cause="construction",
            effect="delay",
            severity="moderate",
            description="Active alert",
            affected_routes=["R1"],
            active_period_start=now - timedelta(hours=1),
            active_period_end=now + timedelta(hours=2),
        )
        route.create_service_alert(
            alert_id="A2",
            cause="weather",
            effect="detour",
            severity="severe",
            description="Future alert",
            affected_routes=["R1"],
            active_period_start=now + timedelta(days=1),
            active_period_end=now + timedelta(days=2),
        )
        await repo.save_route(route)
        await db_session.commit()

        active_alerts = await repo.get_active_alerts(now)
        assert len(active_alerts) == 1
        assert active_alerts[0].alert_id == "A1"

    async def test_plan_trip_persistence(self, db_session: AsyncSession):
        """Test that planned trips are persisted"""
        repo = TransitRepository(db_session)

        route = TransitAggregate.create_route(
            route_id="R1",
            name="Red Line",
            transport_mode=TransportMode.SUBWAY,
        )
        route.add_stop(stop_id="S1", name="Start", coordinates=Coordinates(40.7, -74.0), stop_order=1)
        route.add_stop(stop_id="S2", name="Middle", coordinates=Coordinates(40.71, -74.01), stop_order=2)
        route.add_stop(stop_id="S3", name="End", coordinates=Coordinates(40.72, -74.02), stop_order=3)
        await repo.save_route(route)
        await db_session.commit()

        # Plan a trip
        trip = route.plan_trip(
            origin_stop_id="S1",
            destination_stop_id="S3",
            departure_time=time(8, 0),
            arrival_time=time(8, 30),
        )
        await repo.save_route(route)
        await db_session.commit()

        # Verify trip was saved
        retrieved = await repo.get_route_by_id("R1")
        assert len(retrieved.planned_trips) == 1
        assert retrieved.planned_trips[0].origin_stop_id == "S1"
        assert retrieved.planned_trips[0].destination_stop_id == "S3"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])