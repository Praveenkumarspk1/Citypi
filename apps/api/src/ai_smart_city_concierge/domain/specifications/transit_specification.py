"""
Transit Specifications - Specification pattern for Transit queries
"""
from dataclasses import dataclass
from datetime import datetime, time

from ..entities.transit import TransitMode, TransitRoute, TransitStop, TransitTrip
from ..repositories.base import Specification
from ..value_objects.coordinates import Coordinates


class TransitSpecification(Specification):
    """Base Transit specification"""
    pass


@dataclass(frozen=True)
class TransitRouteModeSpecification(TransitSpecification):
    """Specification for transit routes by mode"""
    mode: TransitMode

    def is_satisfied_by(self, route: TransitRoute) -> bool:
        return route.mode == self.mode


@dataclass(frozen=True)
class TransitRouteActiveSpecification(TransitSpecification):
    """Specification for active transit routes"""
    def is_satisfied_by(self, route: TransitRoute) -> bool:
        return route.is_active


@dataclass(frozen=True)
class TransitRouteAgencySpecification(TransitSpecification):
    """Specification for transit routes by agency"""
    agency_id: str

    def is_satisfied_by(self, route: TransitRoute) -> bool:
        return route.agency_id == self.agency_id


@dataclass(frozen=True)
class TransitRouteColorSpecification(TransitSpecification):
    """Specification for transit routes by color"""
    color: str

    def is_satisfied_by(self, route: TransitRoute) -> bool:
        return route.color and route.color.lower() == self.color.lower()


@dataclass(frozen=True)
class TransitStopWheelchairAccessibleSpecification(TransitSpecification):
    """Specification for wheelchair accessible stops"""
    required: bool = True

    def is_satisfied_by(self, stop: TransitStop) -> bool:
        if stop.wheelchair_accessible is None:
            return not self.required
        return stop.wheelchair_accessible == self.required


@dataclass(frozen=True)
class TransitStopHasShelterSpecification(TransitSpecification):
    """Specification for stops with shelter"""
    required: bool = True

    def is_satisfied_by(self, stop: TransitStop) -> bool:
        return stop.has_shelter == self.required


@dataclass(frozen=True)
class TransitStopHasRealtimeSpecification(TransitSpecification):
    """Specification for stops with real-time display"""
    required: bool = True

    def is_satisfied_by(self, stop: TransitStop) -> bool:
        return stop.has_realtime_display == self.required


@dataclass(frozen=True)
class TransitStopLocationSpecification(TransitSpecification):
    """Specification for stops within radius of coordinates"""
    center: Coordinates
    radius_meters: float

    def is_satisfied_by(self, stop: TransitStop) -> bool:
        return stop.coordinates.is_within_radius(self.center, self.radius_meters)


@dataclass(frozen=True)
class TransitStopZoneSpecification(TransitSpecification):
    """Specification for stops in a specific zone"""
    zone: str

    def is_satisfied_by(self, stop: TransitStop) -> bool:
        return stop.zone == self.zone


@dataclass(frozen=True)
class TransitTripWheelchairAccessibleSpecification(TransitSpecification):
    """Specification for wheelchair accessible trips"""
    required: bool = True

    def is_satisfied_by(self, trip: TransitTrip) -> bool:
        return trip.wheelchair_accessible == self.required


@dataclass(frozen=True)
class TransitTripBikesAllowedSpecification(TransitSpecification):
    """Specification for trips allowing bikes"""
    required: bool = True

    def is_satisfied_by(self, trip: TransitTrip) -> bool:
        return trip.bikes_allowed == self.required


@dataclass(frozen=True)
class TransitTripDirectionSpecification(TransitSpecification):
    """Specification for trips by direction"""
    direction_id: int  # 0 or 1

    def is_satisfied_by(self, trip: TransitTrip) -> bool:
        return trip.direction_id == self.direction_id


@dataclass(frozen=True)
class TransitScheduleTimeSpecification(TransitSpecification):
    """Specification for schedules within time range"""
    start_time: time
    end_time: time

    def is_satisfied_by(self, schedule) -> bool:
        return self.start_time <= schedule.departure_time <= self.end_time


@dataclass(frozen=True)
class TransitScheduleRouteSpecification(TransitSpecification):
    """Specification for schedules by route"""
    route_id: str

    def is_satisfied_by(self, schedule) -> bool:
        return schedule.route_id == self.route_id


@dataclass(frozen=True)
class TransitRealtimeArrivalSpecification(TransitSpecification):
    """Specification for real-time arrivals within minutes"""
    max_wait_minutes: int

    def is_satisfied_by(self, arrival) -> bool:
        wait_minutes = (arrival.predicted_arrival - datetime.utcnow()).total_seconds() / 60
        return 0 <= wait_minutes <= self.max_wait_minutes


@dataclass(frozen=True)
class TransitAlertSeveritySpecification(TransitSpecification):
    """Specification for alerts by severity"""
    severity: str  # info, warning, severe

    def is_satisfied_by(self, alert) -> bool:
        return alert.severity == self.severity


@dataclass(frozen=True)
class TransitAlertActiveSpecification(TransitSpecification):
    """Specification for active alerts"""
    def is_satisfied_by(self, alert) -> bool:
        now = datetime.utcnow()
        if alert.active_period_start and alert.active_period_start > now:
            return False
        if alert.active_period_end and alert.active_period_end < now:
            return False
        return True


@dataclass(frozen=True)
class TransitAlertRouteSpecification(TransitSpecification):
    """Specification for alerts affecting a route"""
    route_id: str

    def is_satisfied_by(self, alert) -> bool:
        return self.route_id in alert.affected_routes


@dataclass(frozen=True)
class TransitAlertStopSpecification(TransitSpecification):
    """Specification for alerts affecting a stop"""
    stop_id: str

    def is_satisfied_by(self, alert) -> bool:
        return self.stop_id in alert.affected_stops


# Composite specifications for common query patterns
class TransitSpecifications:
    """Factory for common Transit specification combinations"""

    @staticmethod
    def nearby_bus_stops(center: Coordinates, radius_meters: float = 500) -> TransitSpecification:
        """Find nearby bus stops"""
        return (TransitStopLocationSpecification(center, radius_meters) &
                TransitRouteModeSpecification(TransitMode.BUS))

    @staticmethod
    def accessible_stops(center: Coordinates, radius_meters: float = 1000) -> TransitSpecification:
        """Find wheelchair accessible stops"""
        return (TransitStopLocationSpecification(center, radius_meters) &
                TransitStopWheelchairAccessibleSpecification())

    @staticmethod
    def stops_with_shelter(center: Coordinates, radius_meters: float = 500) -> TransitSpecification:
        """Find stops with shelter"""
        return (TransitStopLocationSpecification(center, radius_meters) &
                TransitStopHasShelterSpecification())

    @staticmethod
    def stops_with_realtime(center: Coordinates, radius_meters: float = 500) -> TransitSpecification:
        """Find stops with real-time displays"""
        return (TransitStopLocationSpecification(center, radius_meters) &
                TransitStopHasRealtimeSpecification())

    @staticmethod
    def metro_routes() -> TransitSpecification:
        """Get all metro routes"""
        return (TransitRouteModeSpecification(TransitMode.METRO) &
                TransitRouteActiveSpecification())

    @staticmethod
    def bus_routes() -> TransitSpecification:
        """Get all bus routes"""
        return (TransitRouteModeSpecification(TransitMode.BUS) &
                TransitRouteActiveSpecification())

    @staticmethod
    def tram_routes() -> TransitSpecification:
        """Get all tram routes"""
        return (TransitRouteModeSpecification(TransitMode.TRAM) &
                TransitRouteActiveSpecification())

    @staticmethod
    def train_routes() -> TransitSpecification:
        """Get all train routes"""
        return (TransitRouteModeSpecification(TransitMode.TRAIN) &
                TransitRouteActiveSpecification())

    @staticmethod
    def ferry_routes() -> TransitSpecification:
        """Get all ferry routes"""
        return (TransitRouteModeSpecification(TransitMode.FERRY) &
                TransitRouteActiveSpecification())

    @staticmethod
    def active_routes() -> TransitSpecification:
        """Get all active routes"""
        return TransitRouteActiveSpecification()

    @staticmethod
    def routes_by_agency(agency_id: str) -> TransitSpecification:
        """Get routes by agency"""
        return (TransitRouteAgencySpecification(agency_id) &
                TransitRouteActiveSpecification())

    @staticmethod
    def accessible_trips() -> TransitSpecification:
        """Get wheelchair accessible trips"""
        return TransitTripWheelchairAccessibleSpecification()

    @staticmethod
    def bike_friendly_trips() -> TransitSpecification:
        """Get bike-friendly trips"""
        return TransitTripBikesAllowedSpecification()

    @staticmethod
    def upcoming_arrivals(max_wait_minutes: int = 30) -> TransitSpecification:
        """Get upcoming real-time arrivals"""
        return TransitRealtimeArrivalSpecification(max_wait_minutes)

    @staticmethod
    def active_alerts() -> TransitSpecification:
        """Get active transit alerts"""
        return TransitAlertActiveSpecification()

    @staticmethod
    def severe_alerts() -> TransitSpecification:
        """Get severe transit alerts"""
        return (TransitAlertSeveritySpecification("severe") &
                TransitAlertActiveSpecification())

    @staticmethod
    def alerts_for_route(route_id: str) -> TransitSpecification:
        """Get alerts for a specific route"""
        return (TransitAlertRouteSpecification(route_id) &
                TransitAlertActiveSpecification())

    @staticmethod
    def alerts_for_stop(stop_id: str) -> TransitSpecification:
        """Get alerts for a specific stop"""
        return (TransitAlertStopSpecification(stop_id) &
                TransitAlertActiveSpecification())

    @staticmethod
    def schedules_for_route(route_id: str, start_time: time, end_time: time) -> TransitSpecification:
        """Get schedules for a route within time range"""
        return (TransitScheduleRouteSpecification(route_id) &
                TransitScheduleTimeSpecification(start_time, end_time))
