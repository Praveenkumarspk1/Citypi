"""
Unit tests for TransitAggregate
"""
import pytest
from datetime import datetime, time, timezone, timedelta
from uuid import uuid4

from ai_smart_city_concierge.domain.aggregates.transit_aggregate import TransitAggregate
from ai_smart_city_concierge.domain.value_objects.coordinates import Coordinates
from ai_smart_city_concierge.domain.value_objects.transport_mode import TransportMode
from ai_smart_city_concierge.domain.events.transit_events import (
    TransitRouteCreated,
    TransitStopAdded,
    TransitTripPlanned,
    TransitVehiclePositionUpdated,
    TransitServiceAlertCreated,
)


class TestTransitAggregate:
    """Test cases for TransitAggregate"""

    def test_create_transit_route(self):
        """Test creating a new transit route"""
        route = TransitAggregate.create_route(
            route_id="R1",
            name="Red Line",
            short_name="R",
            description="Main north-south line",
            transport_mode=TransportMode.SUBWAY,
            color="#FF0000",
            text_color="#FFFFFF",
        )

        assert route.route_id == "R1"
        assert route.name == "Red Line"
        assert route.short_name == "R"
        assert route.transport_mode == TransportMode.SUBWAY
        assert route.color == "#FF0000"
        assert route.text_color == "#FFFFFF"
        assert route.is_active is True
        assert len(route.stops) == 0

    def test_add_stop_to_route(self):
        """Test adding a stop to a route"""
        route = TransitAggregate.create_route(
            route_id="R1",
            name="Red Line",
            transport_mode=TransportMode.SUBWAY,
        )

        stop_id = route.add_stop(
            stop_id="S1",
            name="Central Station",
            coordinates=Coordinates(latitude=40.7128, longitude=-74.0060),
            stop_order=1,
            is_accessible=True,
        )

        assert len(route.stops) == 1
        stop = route.stops[0]
        assert stop.stop_id == "S1"
        assert stop.name == "Central Station"
        assert stop.coordinates.latitude == 40.7128
        assert stop.coordinates.longitude == -74.0060
        assert stop.stop_order == 1
        assert stop.is_accessible is True

    def test_add_multiple_stops(self):
        """Test adding multiple stops in order"""
        route = TransitAggregate.create_route(
            route_id="R1",
            name="Red Line",
            transport_mode=TransportMode.SUBWAY,
        )

        route.add_stop(stop_id="S1", name="Station A", coordinates=Coordinates(40.7, -74.0), stop_order=1)
        route.add_stop(stop_id="S2", name="Station B", coordinates=Coordinates(40.71, -74.01), stop_order=2)
        route.add_stop(stop_id="S3", name="Station C", coordinates=Coordinates(40.72, -74.02), stop_order=3)

        assert len(route.stops) == 3
        assert route.stops[0].stop_order == 1
        assert route.stops[1].stop_order == 2
        assert route.stops[2].stop_order == 3

    def test_plan_trip(self):
        """Test planning a transit trip"""
        route = TransitAggregate.create_route(
            route_id="R1",
            name="Red Line",
            transport_mode=TransportMode.SUBWAY,
        )

        route.add_stop(stop_id="S1", name="Start", coordinates=Coordinates(40.7, -74.0), stop_order=1)
        route.add_stop(stop_id="S2", name="Middle", coordinates=Coordinates(40.71, -74.01), stop_order=2)
        route.add_stop(stop_id="S3", name="End", coordinates=Coordinates(40.72, -74.02), stop_order=3)

        trip = route.plan_trip(
            origin_stop_id="S1",
            destination_stop_id="S3",
            departure_time=time(8, 0),
            arrival_time=time(8, 30),
        )

        assert trip.origin_stop_id == "S1"
        assert trip.destination_stop_id == "S3"
        assert trip.departure_time == time(8, 0)
        assert trip.arrival_time == time(8, 30)
        assert trip.duration_minutes == 30
        assert len(trip.intermediate_stops) == 1
        assert trip.intermediate_stops[0] == "S2"

    def test_update_vehicle_position(self):
        """Test updating vehicle position"""
        route = TransitAggregate.create_route(
            route_id="R1",
            name="Red Line",
            transport_mode=TransportMode.SUBWAY,
        )

        route.add_stop(stop_id="S1", name="Station A", coordinates=Coordinates(40.7, -74.0), stop_order=1)
        route.add_stop(stop_id="S2", name="Station B", coordinates=Coordinates(40.71, -74.01), stop_order=2)

        vehicle_id = "V1"
        position = Coordinates(latitude=40.705, longitude=-74.005)

        route.update_vehicle_position(
            vehicle_id=vehicle_id,
            position=position,
            current_stop_id="S1",
            next_stop_id="S2",
            occupancy=0.7,
            timestamp=datetime.now(timezone.utc),
        )

        vehicle = route.vehicles[vehicle_id]
        assert vehicle.vehicle_id == vehicle_id
        assert vehicle.position.latitude == 40.705
        assert vehicle.position.longitude == -74.005
        assert vehicle.current_stop_id == "S1"
        assert vehicle.next_stop_id == "S2"
        assert vehicle.occupancy == 0.7

    def test_create_service_alert(self):
        """Test creating a service alert"""
        route = TransitAggregate.create_route(
            route_id="R1",
            name="Red Line",
            transport_mode=TransportMode.SUBWAY,
        )

        alert_id = route.create_service_alert(
            alert_id="A1",
            cause="construction",
            effect="delay",
            severity="moderate",
            description="Track maintenance causing delays",
            affected_routes=["R1"],
            active_period_start=datetime.now(timezone.utc),
            active_period_end=datetime.now(timezone.utc) + timedelta(hours=4),
        )

        assert len(route.service_alerts) == 1
        alert = route.service_alerts[0]
        assert alert.alert_id == "A1"
        assert alert.cause == "construction"
        assert alert.effect == "delay"
        assert alert.severity == "moderate"
        assert alert.description == "Track maintenance causing delays"
        assert "R1" in alert.affected_routes

    def test_get_active_alerts(self):
        """Test getting active alerts"""
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

        active_alerts = route.get_active_alerts(now)
        assert len(active_alerts) == 1
        assert active_alerts[0].alert_id == "A1"

    def test_deactivate_route(self):
        """Test deactivating a route"""
        route = TransitAggregate.create_route(
            route_id="R1",
            name="Red Line",
            transport_mode=TransportMode.SUBWAY,
        )

        assert route.is_active is True

        route.deactivate()

        assert route.is_active is False

    def test_transit_events_emitted(self):
        """Test that domain events are emitted"""
        route = TransitAggregate.create_route(
            route_id="R1",
            name="Red Line",
            transport_mode=TransportMode.SUBWAY,
        )

        # Check TransitRouteCreated event
        events = route.get_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], TransitRouteCreated)
        assert events[0].route_id == "R1"
        assert events[0].name == "Red Line"

        # Clear events and add stop
        route.clear_events()
        route.add_stop(
            stop_id="S1",
            name="Central Station",
            coordinates=Coordinates(40.7128, -74.0060),
            stop_order=1,
        )

        events = route.get_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], TransitStopAdded)
        assert events[0].stop_id == "S1"
        assert events[0].name == "Central Station"

        # Clear events and plan trip
        route.clear_events()
        route.add_stop(stop_id="S2", name="Station B", coordinates=Coordinates(40.72, -74.01), stop_order=2)
        route.plan_trip(
            origin_stop_id="S1",
            destination_stop_id="S2",
            departure_time=time(8, 0),
            arrival_time=time(8, 15),
        )

        events = route.get_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], TransitTripPlanned)
        assert events[0].origin_stop_id == "S1"
        assert events[0].destination_stop_id == "S2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])