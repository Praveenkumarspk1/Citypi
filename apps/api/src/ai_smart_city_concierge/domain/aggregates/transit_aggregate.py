"""
Transit Aggregate
"""
from dataclasses import dataclass, field
from datetime import datetime, time, timezone, timedelta
from typing import Optional
from uuid import UUID, uuid4

from ..entities.transit import Route, Stop, Trip, RealtimeVehiclePosition, RealtimeAlert
from ..events import (
    TransitRouteCreatedEvent as TransitRouteCreated,
    TransitStopAddedEvent as TransitStopAdded,
    TransitTripPlannedEvent as TransitTripPlanned,
    TransitVehiclePositionUpdatedEvent as TransitVehiclePositionUpdated,
    TransitServiceAlertCreatedEvent as TransitServiceAlertCreated,
)
from ..value_objects.coordinates import Coordinates


@dataclass
class TransitAggregate:
    """Transit aggregate root managing routes, stops, vehicles, and alerts"""
    
    route_id: str = ""
    name: str = ""
    short_name: str = ""
    description: str = ""
    transport_mode: str = ""
    color: str = ""
    text_color: str = ""
    is_active: bool = True
    stops: list = field(default_factory=list)
    vehicles: dict = field(default_factory=dict)
    service_alerts: list = field(default_factory=list)
    _uncommitted_events: list = field(default_factory=list)
    
    @classmethod
    def create_route(
        cls,
        route_id: str,
        name: str,
        short_name: str = "",
        description: str = "",
        transport_mode: str = "SUBWAY",
        color: str = "#000000",
        text_color: str = "#FFFFFF",
    ) -> "TransitAggregate":
        """Create a new transit route"""
        route = cls(
            route_id=route_id,
            name=name,
            short_name=short_name,
            description=description,
            transport_mode=transport_mode,
            color=color,
            text_color=text_color,
            is_active=True,
        )
        
        # Emit TransitRouteCreated event
        event = TransitRouteCreated.create(
            route_id=route_id,
            name=name,
            short_name=short_name,
            description=description,
            transport_mode=transport_mode,
            color=color,
            text_color=text_color,
        )
        route._uncommitted_events.append(event)
        
        return route
    
    def add_stop(
        self,
        stop_id: str,
        name: str,
        coordinates: Coordinates,
        stop_order: int,
        is_accessible: bool = True,
    ) -> str:
        """Add a stop to the route"""
        stop = Stop(
            id=stop_id,
            name=name,
            coordinates=coordinates,
            stop_order=stop_order,
            is_accessible=is_accessible,
        )
        self.stops.append(stop)
        self.stops.sort(key=lambda s: s.stop_order)
        
        # Emit TransitStopAdded event
        event = TransitStopAdded.create(
            route_id=self.route_id,
            id=stop_id,
            name=name,
            coordinates=coordinates,
            stop_order=stop_order,
            is_accessible=is_accessible,
        )
        self._uncommitted_events.append(event)
        
        return stop_id
    
    def plan_trip(
        self,
        origin_stop_id: str,
        destination_stop_id: str,
        departure_time: time,
        arrival_time: time,
    ) -> Trip:
        """Plan a trip between two stops"""
        origin_stop = next((s for s in self.stops if s.stop_id == origin_stop_id), None)
        dest_stop = next((s for s in self.stops if s.stop_id == destination_stop_id), None)
        
        if not origin_stop or not dest_stop:
            raise ValueError("Origin or destination stop not found")
        
        duration_minutes = int((datetime.combine(datetime.today(), arrival_time) - 
                               datetime.combine(datetime.today(), departure_time)).total_seconds() / 60)
        
        intermediate_stops = [
            s.stop_id for s in self.stops 
            if s.stop_order > origin_stop.stop_order and s.stop_order < dest_stop.stop_order
        ]
        
        trip = Trip(
            id=f"trip_{uuid4().hex[:8]}",
            route_id=self.route_id,
            origin_id=origin_stop_id,
            destination_id=destination_stop_id,
            departure_time=departure_time,
            arrival_time=arrival_time,
            duration_minutes=duration_minutes,
            intermediate_stops=intermediate_stops,
        )
        
        # Emit TransitTripPlanned event
        event = TransitTripPlanned.create(
            route_id=self.route_id,
            origin_id=origin_stop_id,
            destination_id=destination_stop_id,
            departure_time=departure_time,
            arrival_time=arrival_time,
            intermediate_stops=intermediate_stops,
        )
        self._uncommitted_events.append(event)
        
        return trip
    
    def update_vehicle_position(
        self,
        vehicle_id: str,
        position: Coordinates,
        current_stop_id: str,
        next_stop_id: str,
        occupancy: float,
        timestamp: datetime,
    ) -> RealtimeVehiclePosition:
        """Update vehicle position"""
        vehicle = RealtimeVehiclePosition(
            vehicle_id=vehicle_id,
            route_id=self.route_id,
            position=position,
            current_id=current_stop_id,
            next_id=next_stop_id,
            occupancy=occupancy,
            timestamp=timestamp,
        )
        self.vehicles[vehicle_id] = vehicle
        
        # Emit TransitVehiclePositionUpdated event
        event = TransitVehiclePositionUpdated.create(
            route_id=self.route_id,
            vehicle_id=vehicle_id,
            position=position,
            current_id=current_stop_id,
            next_id=next_stop_id,
            occupancy=occupancy,
            timestamp=timestamp,
        )
        self._uncommitted_events.append(event)
        
        return vehicle
    
    def create_service_alert(
        self,
        alert_id: str,
        cause: str,
        effect: str,
        severity: str,
        description: str,
        affected_routes: list[str],
        active_period_start: datetime,
        active_period_end: datetime,
    ) -> str:
        """Create a service alert"""
        alert = RealtimeAlert(
            id=alert_id,
            cause=cause,
            effect=effect,
            severity_level=severity,
            description=description,
            affected_routes=affected_routes,
            active_period_start=active_period_start,
            active_period_end=active_period_end,
        )
        self.service_alerts.append(alert)
        
        # Emit TransitServiceAlertCreated event
        event = TransitServiceAlertCreated.create(
            route_id=self.route_id,
            id=alert_id,
            cause=cause,
            effect=effect,
            severity_level=severity,
            description=description,
            affected_routes=affected_routes,
            active_period_start=active_period_start,
            active_period_end=active_period_end,
        )
        self._uncommitted_events.append(event)
        
        return alert_id
    
    def get_active_alerts(self, at_time: datetime) -> list:
        """Get active alerts at a given time"""
        return [
            alert for alert in self.service_alerts
            if alert.active_period_start <= at_time <= alert.active_period_end
        ]
    
    def deactivate(self) -> None:
        """Deactivate the route"""
        self.is_active = False
    
    def get_uncommitted_events(self) -> list:
        """Get uncommitted domain events"""
        return self._uncommitted_events
    
    def clear_events(self) -> None:
        """Clear uncommitted events"""
        self._uncommitted_events.clear()





