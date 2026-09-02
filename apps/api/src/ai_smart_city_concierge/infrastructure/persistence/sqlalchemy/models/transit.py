"""
SQLAlchemy Transit Models
"""
import uuid
from datetime import datetime

from ai_smart_city_concierge.domain.entities.transit import (
    Agency,
    Fare,
    RealtimeAlert,
    RealtimeTripUpdate,
    RealtimeVehiclePosition,
    Route,
    RouteType,
    ServiceCalendar,
    ServiceException,
    Shape,
    Stop,
    StopTime,
    TransitRoute,
    Trip,
)
from ai_smart_city_concierge.infrastructure.config.database import Base
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class AgencyModel(Base):
    """SQLAlchemy model for Transit Agency"""
    __tablename__ = "transit_agencies"

    id = Column(String(100), primary_key=True)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    timezone = Column(String(100), default="UTC", nullable=False)
    lang = Column(String(10), nullable=True)
    phone = Column(String(50), nullable=True)
    fare_url = Column(String(500), nullable=True)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    routes = relationship("RouteModel", back_populates="agency", lazy="dynamic")
    stops = relationship("StopModel", back_populates="agency", lazy="dynamic")

    def to_entity(self):
        return Agency(
            id=self.id,
            name=self.name,
            url=self.url,
            timezone=self.timezone,
            lang=self.lang,
            phone=self.phone,
            fare_url=self.fare_url,
            email=self.email,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_entity(cls, entity):
        return cls(
            id=entity.id,
            name=entity.name,
            url=entity.url,
            timezone=entity.timezone,
            lang=entity.lang,
            phone=entity.phone,
            fare_url=entity.fare_url,
            email=entity.email,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class StopModel(Base):
    """SQLAlchemy model for Transit Stop"""
    __tablename__ = "transit_stops"

    id = Column(String(100), primary_key=True)
    code = Column(String(50), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    zone_id = Column(String(50), nullable=True)
    url = Column(String(500), nullable=True)
    location_type = Column(Integer, default=0, nullable=False)
    parent_station = Column(String(100), ForeignKey("transit_stops.id"), nullable=True)
    platform_code = Column(String(50), nullable=True)
    wheelchair_boarding = Column(Integer, nullable=True)
    agency_id = Column(String(100), ForeignKey("transit_agencies.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    agency = relationship("AgencyModel", back_populates="stops")
    routes = relationship("RouteModel", secondary="route_stops", back_populates="stops")

    __table_args__ = (
        Index('ix_transit_stops_location', 'latitude', 'longitude'),
        Index('ix_transit_stops_parent', 'parent_station'),
    )

    def to_entity(self):
        from ....domain.value_objects.coordinates import Coordinates
        return Stop(
            id=self.id,
            code=self.code,
            name=self.name,
            description=self.description,
            coordinates=Coordinates(latitude=self.latitude, longitude=self.longitude),
            zone_id=self.zone_id,
            url=self.url,
            location_type=self.location_type,
            parent_station=self.parent_station,
            platform_code=self.platform_code,
            wheelchair_boarding=self.wheelchair_boarding,
            agency_id=self.agency_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_entity(cls, entity):
        return cls(
            id=entity.id,
            code=entity.code,
            name=entity.name,
            description=entity.description,
            latitude=entity.coordinates.latitude,
            longitude=entity.coordinates.longitude,
            zone_id=entity.zone_id,
            url=entity.url,
            location_type=entity.location_type,
            parent_station=entity.parent_station,
            platform_code=entity.platform_code,
            wheelchair_boarding=entity.wheelchair_boarding,
            agency_id=entity.agency_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class RouteModel(Base):
    """SQLAlchemy model for Transit Route"""
    __tablename__ = "transit_routes"

    id = Column(String(100), primary_key=True)
    agency_id = Column(String(100), ForeignKey("transit_agencies.id"), nullable=False, index=True)
    short_name = Column(String(50), nullable=True)
    long_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(SQLEnum(RouteType), default=RouteType.BUS, nullable=False)
    url = Column(String(500), nullable=True)
    color = Column(String(7), nullable=True)
    text_color = Column(String(7), nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    agency = relationship("AgencyModel", back_populates="routes")
    trips = relationship("TripModel", back_populates="route", lazy="dynamic")
    stops = relationship("StopModel", secondary="route_stops", back_populates="routes")

    def to_entity(self):
        return Route(
            id=self.id,
            agency_id=self.agency_id,
            short_name=self.short_name,
            long_name=self.long_name,
            description=self.description,
            type=self.type,
            url=self.url,
            color=self.color,
            text_color=self.text_color,
            sort_order=self.sort_order,
            is_active=self.is_active,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_entity(cls, entity):
        return cls(
            id=entity.id,
            agency_id=entity.agency_id,
            short_name=entity.short_name,
            long_name=entity.long_name,
            description=entity.description,
            type=entity.type,
            url=entity.url,
            color=entity.color,
            text_color=entity.text_color,
            sort_order=entity.sort_order,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class RouteStopModel(Base):
    """Association table for Route-Stop many-to-many"""
    __tablename__ = "route_stops"

    route_id = Column(String(100), ForeignKey("transit_routes.id"), primary_key=True)
    stop_id = Column(String(100), ForeignKey("transit_stops.id"), primary_key=True)
    sequence = Column(Integer, nullable=False)


class TripModel(Base):
    """SQLAlchemy model for Transit Trip"""
    __tablename__ = "transit_trips"

    id = Column(String(100), primary_key=True)
    route_id = Column(String(100), ForeignKey("transit_routes.id"), nullable=False, index=True)
    service_id = Column(String(100), ForeignKey("service_calendars.service_id"), nullable=False, index=True)
    trip_headsign = Column(String(255), nullable=True)
    trip_short_name = Column(String(100), nullable=True)
    direction_id = Column(Integer, default=0, nullable=False)
    block_id = Column(String(100), nullable=True)
    shape_id = Column(String(100), nullable=True)
    wheelchair_accessible = Column(Integer, default=0, nullable=False)
    bikes_allowed = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    route = relationship("RouteModel", back_populates="trips")
    service = relationship("ServiceCalendarModel", back_populates="trips")
    stop_times = relationship("StopTimeModel", back_populates="trip", lazy="dynamic", order_by="StopTimeModel.stop_sequence")

    def to_entity(self):
        return Trip(
            id=self.id,
            route_id=self.route_id,
            service_id=self.service_id,
            trip_headsign=self.trip_headsign,
            trip_short_name=self.trip_short_name,
            direction_id=self.direction_id,
            block_id=self.block_id,
            shape_id=self.shape_id,
            wheelchair_accessible=self.wheelchair_accessible,
            bikes_allowed=self.bikes_allowed,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_entity(cls, entity):
        return cls(
            id=entity.id,
            route_id=entity.route_id,
            service_id=entity.service_id,
            trip_headsign=entity.trip_headsign,
            trip_short_name=entity.trip_short_name,
            direction_id=entity.direction_id,
            block_id=entity.block_id,
            shape_id=entity.shape_id,
            wheelchair_accessible=entity.wheelchair_accessible,
            bikes_allowed=entity.bikes_allowed,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class StopTimeModel(Base):
    """SQLAlchemy model for Stop Time"""
    __tablename__ = "stop_times"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trip_id = Column(String(100), ForeignKey("transit_trips.id"), nullable=False, index=True)
    arrival_time = Column(String(8), nullable=False)  # HH:MM:SS
    departure_time = Column(String(8), nullable=False)  # HH:MM:SS
    stop_id = Column(String(100), ForeignKey("transit_stops.id"), nullable=False, index=True)
    stop_sequence = Column(Integer, nullable=False)
    stop_headsign = Column(String(255), nullable=True)
    pickup_type = Column(Integer, default=0, nullable=False)
    drop_off_type = Column(Integer, default=0, nullable=False)
    shape_dist_traveled = Column(Float, nullable=True)
    timepoint = Column(Integer, default=1, nullable=False)

    # Relationships
    trip = relationship("TripModel", back_populates="stop_times")
    stop = relationship("StopModel")

    __table_args__ = (
        Index('ix_stop_times_trip_sequence', 'trip_id', 'stop_sequence'),
    )

    def to_entity(self):
        return StopTime(
            trip_id=self.trip_id,
            arrival_time=self.arrival_time,
            departure_time=self.departure_time,
            stop_id=self.stop_id,
            stop_sequence=self.stop_sequence,
            stop_headsign=self.stop_headsign,
            pickup_type=self.pickup_type,
            drop_off_type=self.drop_off_type,
            shape_dist_traveled=self.shape_dist_traveled,
            timepoint=self.timepoint,
        )

    @classmethod
    def from_entity(cls, entity):
        return cls(
            trip_id=entity.trip_id,
            arrival_time=entity.arrival_time,
            departure_time=entity.departure_time,
            stop_id=entity.stop_id,
            stop_sequence=entity.stop_sequence,
            stop_headsign=entity.stop_headsign,
            pickup_type=entity.pickup_type,
            drop_off_type=entity.drop_off_type,
            shape_dist_traveled=entity.shape_dist_traveled,
            timepoint=entity.timepoint,
        )


class ServiceCalendarModel(Base):
    """SQLAlchemy model for Service Calendar"""
    __tablename__ = "service_calendars"

    service_id = Column(String(100), primary_key=True)
    monday = Column(Integer, default=0, nullable=False)
    tuesday = Column(Integer, default=0, nullable=False)
    wednesday = Column(Integer, default=0, nullable=False)
    thursday = Column(Integer, default=0, nullable=False)
    friday = Column(Integer, default=0, nullable=False)
    saturday = Column(Integer, default=0, nullable=False)
    sunday = Column(Integer, default=0, nullable=False)
    start_date = Column(String(8), nullable=False)  # YYYYMMDD
    end_date = Column(String(8), nullable=False)  # YYYYMMDD

    # Relationships
    trips = relationship("TripModel", back_populates="service")
    exceptions = relationship("ServiceExceptionModel", back_populates="service")

    def to_entity(self):
        return ServiceCalendar(
            service_id=self.service_id,
            monday=self.monday,
            tuesday=self.tuesday,
            wednesday=self.wednesday,
            thursday=self.thursday,
            friday=self.friday,
            saturday=self.saturday,
            sunday=self.sunday,
            start_date=self.start_date,
            end_date=self.end_date,
        )

    @classmethod
    def from_entity(cls, entity):
        return cls(
            service_id=entity.service_id,
            monday=entity.monday,
            tuesday=entity.tuesday,
            wednesday=entity.wednesday,
            thursday=entity.thursday,
            friday=entity.friday,
            saturday=entity.saturday,
            sunday=entity.sunday,
            start_date=entity.start_date,
            end_date=entity.end_date,
        )


class ServiceExceptionModel(Base):
    """SQLAlchemy model for Service Exception"""
    __tablename__ = "service_exceptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_id = Column(String(100), ForeignKey("service_calendars.service_id"), nullable=False, index=True)
    date = Column(String(8), nullable=False)  # YYYYMMDD
    exception_type = Column(Integer, default=1, nullable=False)  # 1=added, 2=removed

    # Relationships
    service = relationship("ServiceCalendarModel", back_populates="exceptions")

    def to_entity(self):
        return ServiceException(
            service_id=self.service_id,
            date=self.date,
            exception_type=self.exception_type,
        )

    @classmethod
    def from_entity(cls, entity):
        return cls(
            service_id=entity.service_id,
            date=entity.date,
            exception_type=entity.exception_type,
        )


class ShapeModel(Base):
    """SQLAlchemy model for Route Shape"""
    __tablename__ = "shapes"

    id = Column(String(100), primary_key=True)
    points = Column(JSON, default=list, nullable=False)  # List of [lat, lng]

    def to_entity(self):
        from ....domain.value_objects.coordinates import Coordinates
        return Shape(
            id=self.id,
            points=[Coordinates(latitude=p[0], longitude=p[1]) for p in self.points],
        )

    @classmethod
    def from_entity(cls, entity):
        return cls(
            id=entity.id,
            points=[[p.latitude, p.longitude] for p in entity.points],
        )


class FareModel(Base):
    """SQLAlchemy model for Fare"""
    __tablename__ = "fares"

    id = Column(String(100), primary_key=True)
    price = Column(Float, default=0.0, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    payment_method = Column(Integer, default=0, nullable=False)
    transfers = Column(Integer, default=0, nullable=False)
    transfer_duration = Column(Integer, nullable=True)

    def to_entity(self):
        return Fare(
            id=self.id,
            price=self.price,
            currency=self.currency,
            payment_method=self.payment_method,
            transfers=self.transfers,
            transfer_duration=self.transfer_duration,
        )

    @classmethod
    def from_entity(cls, entity):
        return cls(
            id=entity.id,
            price=entity.price,
            currency=entity.currency,
            payment_method=entity.payment_method,
            transfers=entity.transfers,
            transfer_duration=entity.transfer_duration,
        )


class RealtimeVehiclePositionModel(Base):
    """SQLAlchemy model for Real-time Vehicle Position"""
    __tablename__ = "realtime_vehicle_positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String(100), nullable=False, index=True)
    trip_id = Column(String(100), nullable=False, index=True)
    route_id = Column(String(100), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    bearing = Column(Float, nullable=True)
    speed = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    stop_id = Column(String(100), nullable=True)
    current_status = Column(Integer, default=0, nullable=False)
    congestion_level = Column(Integer, default=0, nullable=False)
    occupancy_status = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        Index('ix_realtime_vehicle_route_time', 'route_id', 'timestamp'),
    )

    def to_entity(self):
        from ....domain.value_objects.coordinates import Coordinates
        return RealtimeVehiclePosition(
            vehicle_id=self.vehicle_id,
            trip_id=self.trip_id,
            route_id=self.route_id,
            coordinates=Coordinates(latitude=self.latitude, longitude=self.longitude),
            bearing=self.bearing,
            speed=self.speed,
            timestamp=self.timestamp,
            stop_id=self.stop_id,
            current_status=self.current_status,
            congestion_level=self.congestion_level,
            occupancy_status=self.occupancy_status,
        )

    @classmethod
    def from_entity(cls, entity):
        return cls(
            vehicle_id=entity.vehicle_id,
            trip_id=entity.trip_id,
            route_id=entity.route_id,
            latitude=entity.coordinates.latitude,
            longitude=entity.coordinates.longitude,
            bearing=entity.bearing,
            speed=entity.speed,
            timestamp=entity.timestamp,
            stop_id=entity.stop_id,
            current_status=entity.current_status,
            congestion_level=entity.congestion_level,
            occupancy_status=entity.occupancy_status,
        )


class RealtimeTripUpdateModel(Base):
    """SQLAlchemy model for Real-time Trip Update"""
    __tablename__ = "realtime_trip_updates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trip_id = Column(String(100), nullable=False, index=True)
    route_id = Column(String(100), nullable=False, index=True)
    start_time = Column(String(8), nullable=False)
    start_date = Column(String(8), nullable=False)
    schedule_relationship = Column(Integer, default=0, nullable=False)
    vehicle_id = Column(String(100), nullable=True)
    stop_time_updates = Column(JSON, default=list, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    delay = Column(Integer, nullable=True)

    def to_entity(self):
        return RealtimeTripUpdate(
            trip_id=self.trip_id,
            route_id=self.route_id,
            start_time=self.start_time,
            start_date=self.start_date,
            schedule_relationship=self.schedule_relationship,
            vehicle=RealtimeVehiclePositionModel.from_entity(self.vehicle) if self.vehicle_id else None,
            stop_time_updates=self.stop_time_updates,
            timestamp=self.timestamp,
            delay=self.delay,
        )

    @classmethod
    def from_entity(cls, entity):
        return cls(
            trip_id=entity.trip_id,
            route_id=entity.route_id,
            start_time=entity.start_time,
            start_date=entity.start_date,
            schedule_relationship=entity.schedule_relationship,
            vehicle_id=entity.vehicle.vehicle_id if entity.vehicle else None,
            stop_time_updates=entity.stop_time_updates,
            timestamp=entity.timestamp,
            delay=entity.delay,
        )


class RealtimeAlertModel(Base):
    """SQLAlchemy model for Real-time Alert"""
    __tablename__ = "realtime_alerts"

    id = Column(String(100), primary_key=True)
    cause = Column(Integer, default=0, nullable=False)
    effect = Column(Integer, default=0, nullable=False)
    url = Column(String(500), nullable=True)
    header_text = Column(String(255), nullable=True)
    description_text = Column(Text, nullable=True)
    tts_header_text = Column(String(255), nullable=True)
    tts_description_text = Column(Text, nullable=True)
    severity_level = Column(Integer, default=0, nullable=False)
    active_period_start = Column(DateTime, nullable=True)
    active_period_end = Column(DateTime, nullable=True)
    informed_entities = Column(JSON, default=list, nullable=False)

    def to_entity(self):
        return RealtimeAlert(
            id=self.id,
            cause=self.cause,
            effect=self.effect,
            url=self.url,
            header_text=self.header_text,
            description_text=self.description_text,
            tts_header_text=self.tts_header_text,
            tts_description_text=self.tts_description_text,
            severity_level=self.severity_level,
            active_period_start=self.active_period_start,
            active_period_end=self.active_period_end,
            informed_entities=self.informed_entities,
        )

    @classmethod
    def from_entity(cls, entity):
        return cls(
            id=entity.id,
            cause=entity.cause,
            effect=entity.effect,
            url=entity.url,
            header_text=entity.header_text,
            description_text=entity.description_text,
            tts_header_text=entity.tts_header_text,
            tts_description_text=entity.tts_description_text,
            severity_level=entity.severity_level,
            active_period_start=entity.active_period_start,
            active_period_end=entity.active_period_end,
            informed_entities=entity.informed_entities,
        )


class TransitRouteModel(Base):
    """SQLAlchemy model for Computed Transit Route"""
    __tablename__ = "computed_transit_routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    origin_lat = Column(Float, nullable=False)
    origin_lng = Column(Float, nullable=False)
    destination_lat = Column(Float, nullable=False)
    destination_lng = Column(Float, nullable=False)
    origin_name = Column(String(255), nullable=False)
    destination_name = Column(String(255), nullable=False)
    legs = Column(JSON, default=list, nullable=False)
    total_duration_minutes = Column(Integer, default=0, nullable=False)
    total_distance_meters = Column(Float, default=0.0, nullable=False)
    total_cost = Column(Float, default=0.0, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    departure_time = Column(DateTime, nullable=False)
    arrival_time = Column(DateTime, nullable=False)
    transfers = Column(Integer, default=0, nullable=False)
    walking_distance_meters = Column(Float, default=0.0, nullable=False)
    walking_duration_minutes = Column(Integer, default=0, nullable=False)
    fare_details = Column(JSON, default=list, nullable=False)
    has_realtime = Column(Boolean, default=False, nullable=False)
    realtime_updated_at = Column(DateTime, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("UserModel")

    def to_entity(self):
        from ....domain.value_objects.coordinates import Coordinates
        return TransitRoute(
            id=self.id,
            origin=Coordinates(latitude=self.origin_lat, longitude=self.origin_lng),
            destination=Coordinates(latitude=self.destination_lat, longitude=self.destination_lng),
            origin_name=self.origin_name,
            destination_name=self.destination_name,
            legs=[TransitLegModel.from_dict(leg) for leg in self.legs],
            total_duration_minutes=self.total_duration_minutes,
            total_distance_meters=self.total_distance_meters,
            total_cost=self.total_cost,
            currency=self.currency,
            departure_time=self.departure_time,
            arrival_time=self.arrival_time,
            transfers=self.transfers,
            walking_distance_meters=self.walking_distance_meters,
            walking_duration_minutes=self.walking_duration_minutes,
            fare_details=[FareModel.from_dict(f) for f in self.fare_details],
            has_realtime=self.has_realtime,
            realtime_updated_at=self.realtime_updated_at,
            created_at=self.created_at,
        )

    @classmethod
    def from_entity(cls, entity):
        return cls(
            id=entity.id,
            origin_lat=entity.origin.latitude,
            origin_lng=entity.origin.longitude,
            destination_lat=entity.destination.latitude,
            destination_lng=entity.destination.longitude,
            origin_name=entity.origin_name,
            destination_name=entity.destination_name,
            legs=[leg.to_dict() for leg in entity.legs],
            total_duration_minutes=entity.total_duration_minutes,
            total_distance_meters=entity.total_distance_meters,
            total_cost=entity.total_cost,
            currency=entity.currency,
            departure_time=entity.departure_time,
            arrival_time=entity.arrival_time,
            transfers=entity.transfers,
            walking_distance_meters=entity.walking_distance_meters,
            walking_duration_minutes=entity.walking_duration_minutes,
            fare_details=[f.to_dict() for f in entity.fare_details],
            has_realtime=entity.has_realtime,
            realtime_updated_at=entity.realtime_updated_at,
            user_id=entity.user_id,
            created_at=entity.created_at,
        )


class TransitLegModel:
    """Helper class for Transit Leg serialization"""

    @staticmethod
    def from_dict(data):
        from ....domain.entities.transit import RouteType, TransitLeg, TransitMode
        from ....domain.value_objects.coordinates import Coordinates
        return TransitLeg(
            id=uuid.UUID(data["id"]),
            sequence=data["sequence"],
            mode=TransitMode(data["mode"]),
            from_stop_id=data.get("from_stop_id"),
            from_stop_name=data["from_stop_name"],
            from_coordinates=Coordinates(latitude=data["from_coordinates"]["lat"], longitude=data["from_coordinates"]["lng"]),
            to_stop_id=data.get("to_stop_id"),
            to_stop_name=data["to_stop_name"],
            to_coordinates=Coordinates(latitude=data["to_coordinates"]["lat"], longitude=data["to_coordinates"]["lng"]),
            route_id=data.get("route_id"),
            route_short_name=data.get("route_short_name"),
            route_long_name=data.get("route_long_name"),
            route_color=data.get("route_color"),
            route_type=RouteType(data["route_type"]) if data.get("route_type") else None,
            trip_id=data.get("trip_id"),
            trip_headsign=data.get("trip_headsign"),
            departure_time=datetime.fromisoformat(data["departure_time"]),
            arrival_time=datetime.fromisoformat(data["arrival_time"]),
            duration_minutes=data["duration_minutes"],
            wait_time_minutes=data["wait_time_minutes"],
            distance_meters=data["distance_meters"],
            shape_points=[Coordinates(latitude=p["lat"], longitude=p["lng"]) for p in data.get("shape_points", [])],
            realtime_delay=data.get("realtime_delay"),
            realtime_vehicle=RealtimeVehiclePositionModel.from_dict(data["realtime_vehicle"]) if data.get("realtime_vehicle") else None,
            instructions=data["instructions"],
        )

    @staticmethod
    def to_dict(leg):
        return {
            "id": str(leg.id),
            "sequence": leg.sequence,
            "mode": leg.mode.value,
            "from_stop_id": leg.from_stop_id,
            "from_stop_name": leg.from_stop_name,
            "from_coordinates": {"lat": leg.from_coordinates.latitude, "lng": leg.from_coordinates.longitude},
            "to_stop_id": leg.to_stop_id,
            "to_stop_name": leg.to_stop_name,
            "to_coordinates": {"lat": leg.to_coordinates.latitude, "lng": leg.to_coordinates.longitude},
            "route_id": leg.route_id,
            "route_short_name": leg.route_short_name,
            "route_long_name": leg.route_long_name,
            "route_color": leg.route_color,
            "route_type": leg.route_type.value if leg.route_type else None,
            "trip_id": leg.trip_id,
            "trip_headsign": leg.trip_headsign,
            "departure_time": leg.departure_time.isoformat(),
            "arrival_time": leg.arrival_time.isoformat(),
            "duration_minutes": leg.duration_minutes,
            "wait_time_minutes": leg.wait_time_minutes,
            "distance_meters": leg.distance_meters,
            "shape_points": [{"lat": p.latitude, "lng": p.longitude} for p in leg.shape_points],
            "realtime_delay": leg.realtime_delay,
            "realtime_vehicle": leg.realtime_vehicle.to_dict() if leg.realtime_vehicle else None,
            "instructions": leg.instructions,
        }
