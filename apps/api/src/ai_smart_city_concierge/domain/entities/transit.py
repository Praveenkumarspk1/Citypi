"""
Transit Domain Entities
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any
from uuid import UUID, uuid4

from ..value_objects.coordinates import Coordinates


class TransitMode(StrEnum):
    """Transit modes based on GTFS"""
    TRAM = "tram"           # 0
    SUBWAY = "subway"       # 1
    RAIL = "rail"           # 2
    BUS = "bus"             # 3
    FERRY = "ferry"         # 4
    CABLE_CAR = "cable_car" # 5
    GONDOLA = "gondola"     # 6
    FUNICULAR = "funicular" # 7
    WALKING = "walking"
    CYCLING = "cycling"
    DRIVING = "driving"
    TAXI = "taxi"
    RIDESHARE = "rideshare"


class RouteType(int, Enum):
    """GTFS route types"""
    TRAM = 0
    SUBWAY = 1
    RAIL = 2
    BUS = 3
    FERRY = 4
    CABLE_CAR = 5
    GONDOLA = 6
    FUNICULAR = 7


@dataclass
class Agency:
    """Transit agency"""
    id: str = ""
    name: str = ""
    url: str = ""
    timezone: str = "UTC"
    lang: str = ""
    phone: str = ""
    fare_url: str = ""
    email: str = "" 

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "timezone": self.timezone,
            "lang": self.lang,
            "phone": self.phone,
            "fare_url": self.fare_url,
            "email": self.email,
        }


@dataclass
class Stop:
    """Transit stop/station"""
    id: str = ""
    code: str = ""
    name: str = ""
    description: str = ""
    coordinates: Coordinates = field(default_factory=lambda: Coordinates(0, 0))
    zone_id: str = ""
    url: str = "" 
    location_type: int = 0  # 0=stop, 1=station, 2=entrance, 3=generic node, 4=boarding area
    stop_order: int = 0
    parent_station: str = ""
    platform_code: str = "" 
    is_accessible: bool = True
    
    
    
    
    

    # Additional metadata
    agency_id: str = ""
    routes: list[str] = field(default_factory=list)  # Route IDs serving this stop

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "coordinates": self.coordinates.to_dict(),
            "zone_id": self.zone_id,
            "url": self.url,
            "location_type": self.location_type,
            "parent_station": self.parent_station,
            "platform_code": self.platform_code,
            "wheelchair_boarding": self.wheelchair_boarding,
            "agency_id": self.agency_id,
            "routes": self.routes,
        }

    def to_geojson(self) -> dict:
        return {
            "type": "Feature",
            "geometry": self.coordinates.to_geojson(),
            "properties": {
                "id": self.id,
                "name": self.name,
                "code": self.code,
                "location_type": self.location_type,
            }
        }


@dataclass
class Route:
    """Transit route"""
    id: str = ""
    agency_id: str = ""
    short_name: str = ""
    long_name: str = ""
    description: str = ""
    type: RouteType = RouteType.BUS
    url: str = ""
    color: str = ""
    text_color: str = "" 
    sort_order: int = 0

    # Additional metadata
    stops: list[str] = field(default_factory=list)  # Stop IDs in sequence
    is_active: bool = True

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agency_id": self.agency_id,
            "short_name": self.short_name,
            "long_name": self.long_name,
            "description": self.description,
            "type": self.type.value,
            "type_name": self.type.name,
            "url": self.url,
            "color": self.color,
            "text_color": self.text_color,
            "sort_order": self.sort_order,
            "stops": self.stops,
            "is_active": self.is_active,
        }


@dataclass
class Trip:
    """Transit trip (a specific journey on a route)"""
    id: str = ""
    route_id: str = ""
    service_id: str = ""
    trip_headsign: str = ""
    trip_short_name: str = ""
    direction_id: int = 0  # 0 or 1
    block_id: str = ""
    shape_id: str = ""
    wheelchair_accessible: int = 0  # 0=no info, 1=accessible, 2=not accessible
    bikes_allowed: int = 0  # 0=no info, 1=allowed, 2=not allowed

    # Additional metadata
    stop_times: list["StopTime"] = field(default_factory=list)

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "route_id": self.route_id,
            "service_id": self.service_id,
            "trip_headsign": self.trip_headsign,
            "trip_short_name": self.trip_short_name,
            "direction_id": self.direction_id,
            "block_id": self.block_id,
            "shape_id": self.shape_id,
            "wheelchair_accessible": self.wheelchair_accessible,
            "bikes_allowed": self.bikes_allowed,
        }


# Alias for compatibility
TransitTrip = Trip


@dataclass
class StopTime:
    """Stop time for a trip"""
    trip_id: str = ""
    arrival_time: str = ""  # HH:MM:SS
    departure_time: str = ""  # HH:MM:SS
    stop_id: str = ""
    stop_sequence: int = 0
    stop_headsign: str = ""
    pickup_type: int = 0  # 0=regular, 1=none, 2=phone, 3=driver
    drop_off_type: int = 0  # 0=regular, 1=none, 2=phone, 3=driver
    shape_dist_traveled: float = 0.0
    timepoint: int = 1  # 0=approximate, 1=exact

    def to_dict(self) -> dict:
        return {
            "trip_id": self.trip_id,
            "arrival_time": self.arrival_time,
            "departure_time": self.departure_time,
            "stop_id": self.stop_id,
            "stop_sequence": self.stop_sequence,
            "stop_headsign": self.stop_headsign,
            "pickup_type": self.pickup_type,
            "drop_off_type": self.drop_off_type,
            "shape_dist_traveled": self.shape_dist_traveled,
            "timepoint": self.timepoint,
        }


@dataclass
class ServiceCalendar:
    """Service calendar (when service operates)"""
    service_id: str = ""
    monday: int = 0
    tuesday: int = 0
    wednesday: int = 0
    thursday: int = 0
    friday: int = 0
    saturday: int = 0
    sunday: int = 0
    start_date: str = ""  # YYYYMMDD
    end_date: str = ""    # YYYYMMDD

    def is_active_on(self, date: datetime) -> bool:
        """Check if service is active on given date"""
        date_str = date.strftime("%Y%m%d")
        if date_str < self.start_date or date_str > self.end_date:
            return False
        weekday = date.weekday()  # 0=Monday
        days = [self.monday, self.tuesday, self.wednesday,
                self.thursday, self.friday, self.saturday, self.sunday]
        return days[weekday] == 1

    def to_dict(self) -> dict:
        return {
            "service_id": self.service_id,
            "monday": self.monday,
            "tuesday": self.tuesday,
            "wednesday": self.wednesday,
            "thursday": self.thursday,
            "friday": self.friday,
            "saturday": self.saturday,
            "sunday": self.sunday,
            "start_date": self.start_date,
            "end_date": self.end_date,
        }


@dataclass
class ServiceException:
    """Service exception (added/removed service)"""
    service_id: str = ""
    date: str = ""  # YYYYMMDD
    exception_type: int = 1  # 1=added, 2=removed

    def to_dict(self) -> dict:
        return {
            "service_id": self.service_id,
            "date": self.date,
            "exception_type": self.exception_type,
        }


@dataclass
class Shape:
    """Route shape (geometry)"""
    id: str = ""
    points: list[Coordinates] = field(default_factory=list)

    def to_geojson(self) -> dict:
        return {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [p.to_lng_lat_tuple() for p in self.points]
            },
            "properties": {"id": self.id}
        }


@dataclass
class Fare:
    """Fare information"""
    id: str = ""
    price: float = 0.0
    currency: str = "USD"
    payment_method: int = 0  # 0=onboard, 1=before boarding
    transfers: int = 0  # 0=no transfers, 1=1 transfer, 2=2 transfers
    transfer_duration: int = 0   # seconds

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "price": self.price,
            "currency": self.currency,
            "payment_method": self.payment_method,
            "transfers": self.transfers,
            "transfer_duration": self.transfer_duration,
        }


@dataclass
class RealtimeVehiclePosition:
    """Real-time vehicle position (GTFS-RT)"""
    vehicle_id: str = ""
    trip_id: str = ""
    route_id: str = ""
    coordinates: Coordinates = field(default_factory=lambda: Coordinates(0, 0))
    bearing: float = 0.0
    speed: float = 0.0   # m/s
    timestamp: datetime = field(default_factory=datetime.utcnow)
    stop_id: str = ""
    current_status: int = 0  # 0=incoming, 1=stopped, 2=in_transit
    congestion_level: int = 0  # 0=unknown, 1=running_smoothly, 2=stop_and_go, 3=congestion, 4=severe_congestion
    occupancy_status: int = 0  # 0=empty, 1=many_seats, 2=few_seats, 3=standing, 4=crushed, 5=full, 6=not_accepting

    def to_dict(self) -> dict:
        return {
            "vehicle_id": self.vehicle_id,
            "trip_id": self.trip_id,
            "route_id": self.route_id,
            "coordinates": self.coordinates.to_dict(),
            "bearing": self.bearing,
            "speed": self.speed,
            "timestamp": self.timestamp.isoformat(),
            "stop_id": self.stop_id,
            "current_status": self.current_status,
            "congestion_level": self.congestion_level,
            "occupancy_status": self.occupancy_status,
        }


@dataclass
class RealtimeTripUpdate:
    """Real-time trip update (GTFS-RT)"""
    trip_id: str = ""
    route_id: str = ""
    start_time: str = ""
    start_date: str = ""
    schedule_relationship: int = 0  # 0=scheduled, 1=added, 2=unscheduled, 3=canceled
    vehicle: RealtimeVehiclePosition | None = None
    stop_time_updates: list[dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    delay: int = 0  # seconds

    def to_dict(self) -> dict:
        return {
            "trip_id": self.trip_id,
            "route_id": self.route_id,
            "start_time": self.start_time,
            "start_date": self.start_date,
            "schedule_relationship": self.schedule_relationship,
            "vehicle": self.vehicle.to_dict() if self.vehicle else None,
            "stop_time_updates": self.stop_time_updates,
            "timestamp": self.timestamp.isoformat(),
            "delay": self.delay,
        }


@dataclass
class RealtimeAlert:
    """Real-time service alert (GTFS-RT)"""
    id: str = ""
    cause: int = 0  # 1=construction, 2=weather, 3=accident, etc.
    effect: int = 0  # 1=no_service, 2=reduced_service, 3=significant_delays, etc.
    url: str = ""
    header_text: str = ""
    description_text: str = ""
    tts_header_text: str = ""
    tts_description_text: str = ""
    severity_level: int = 0  # 1=info, 2=warning, 3=severe
    active_period_start: datetime | None = None
    active_period_end: datetime | None = None
    informed_entities: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "cause": self.cause,
            "effect": self.effect,
            "url": self.url,
            "header_text": self.header_text,
            "description_text": self.description_text,
            "tts_header_text": self.tts_header_text,
            "tts_description_text": self.tts_description_text,
            "severity_level": self.severity_level,
            "active_period_start": self.active_period_start.isoformat() if self.active_period_start else None,
            "active_period_end": self.active_period_end.isoformat() if self.active_period_end else None,
            "informed_entities": self.informed_entities,
        }


@dataclass
class TransitRoute:
    """Computed transit route for journey planning"""
    id: UUID = field(default_factory=uuid4)
    origin: Coordinates = field(default_factory=lambda: Coordinates(0, 0))
    destination: Coordinates = field(default_factory=lambda: Coordinates(0, 0))
    origin_name: str = ""
    destination_name: str = ""

    # Route details
    legs: list["TransitLeg"] = field(default_factory=list)
    total_duration_minutes: int = 0
    total_distance_meters: float = 0.0
    total_cost: float = 0.0
    currency: str = "USD"

    # Timing
    departure_time: datetime = field(default_factory=datetime.utcnow)
    arrival_time: datetime = field(default_factory=datetime.utcnow)

    # Metadata
    transfers: int = 0
    walking_distance_meters: float = 0.0
    walking_duration_minutes: int = 0
    fare_details: list[Fare] = field(default_factory=list)

    # Real-time
    has_realtime: bool = False
    realtime_updated_at: datetime | None = None 

    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "origin": self.origin.to_dict(),
            "destination": self.destination.to_dict(),
            "origin_name": self.origin_name,
            "destination_name": self.destination_name,
            "legs": [leg.to_dict() for leg in self.legs],
            "total_duration_minutes": self.total_duration_minutes,
            "total_distance_meters": self.total_distance_meters,
            "total_cost": self.total_cost,
            "currency": self.currency,
            "departure_time": self.departure_time.isoformat(),
            "arrival_time": self.arrival_time.isoformat(),
            "transfers": self.transfers,
            "walking_distance_meters": self.walking_distance_meters,
            "walking_duration_minutes": self.walking_duration_minutes,
            "fare_details": [f.to_dict() for f in self.fare_details],
            "has_realtime": self.has_realtime,
            "realtime_updated_at": self.realtime_updated_at.isoformat() if self.realtime_updated_at else None,
        }


@dataclass
class TransitLeg:
    """Single leg of a transit route"""
    id: UUID = field(default_factory=uuid4)
    sequence: int = 0
    mode: TransitMode = TransitMode.WALKING

    # Locations
    from_stop_id: str = ""
    from_stop_name: str = ""
    from_coordinates: Coordinates = field(default_factory=lambda: Coordinates(0, 0))
    to_stop_id: str = ""
    to_stop_name: str = ""
    to_coordinates: Coordinates = field(default_factory=lambda: Coordinates(0, 0))

    # Transit details
    route_id: str = ""
    route_short_name: str = ""
    route_long_name: str = ""
    route_color: str = ""
    route_type: RouteType | None = None
    trip_id: str = ""
    trip_headsign: str = ""

    # Timing
    departure_time: datetime = field(default_factory=datetime.utcnow)
    arrival_time: datetime = field(default_factory=datetime.utcnow)
    duration_minutes: int = 0
    wait_time_minutes: int = 0

    # Distance
    distance_meters: float = 0.0

    # Path geometry
    shape_points: list[Coordinates] = field(default_factory=list)

    # Real-time
    realtime_delay: int = 0  # seconds
    realtime_vehicle: RealtimeVehiclePosition | None = None

    # Instructions
    instructions: str = ""

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "sequence": self.sequence,
            "mode": self.mode.value,
            "from_stop_id": self.from_stop_id,
            "from_stop_name": self.from_stop_name,
            "from_coordinates": self.from_coordinates.to_dict(),
            "to_stop_id": self.to_stop_id,
            "to_stop_name": self.to_stop_name,
            "to_coordinates": self.to_coordinates.to_dict(),
            "route_id": self.route_id,
            "route_short_name": self.route_short_name,
            "route_long_name": self.route_long_name,
            "route_color": self.route_color,
            "route_type": self.route_type.value if self.route_type else None,
            "trip_id": self.trip_id,
            "trip_headsign": self.trip_headsign,
            "departure_time": self.departure_time.isoformat(),
            "arrival_time": self.arrival_time.isoformat(),
            "duration_minutes": self.duration_minutes,
            "wait_time_minutes": self.wait_time_minutes,
            "distance_meters": self.distance_meters,
            "shape_points": [p.to_dict() for p in self.shape_points],
            "realtime_delay": self.realtime_delay,
            "realtime_vehicle": self.realtime_vehicle.to_dict() if self.realtime_vehicle else None,
            "instructions": self.instructions,
        }

