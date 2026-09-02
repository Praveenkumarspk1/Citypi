"""
SQLAlchemy Itinerary Models
"""
import uuid
from datetime import datetime, time

from ai_smart_city_concierge.domain.entities.itinerary import (
    Itinerary,
    ItineraryDay,
    ItineraryItem,
    ItineraryItemType,
    ItineraryStatus,
    TransportMode,
)
from ai_smart_city_concierge.infrastructure.config.database import Base
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class ItineraryModel(Base):
    """SQLAlchemy model for Itinerary"""
    __tablename__ = "itineraries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(ItineraryStatus), default=ItineraryStatus.DRAFT, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    budget_level = Column(String(20), default="moderate", nullable=False)
    pace = Column(String(20), default="moderate", nullable=False)
    interests = Column(JSON, default=list, nullable=False)
    accessibility_needs = Column(JSON, default=list, nullable=False)
    dietary_restrictions = Column(JSON, default=list, nullable=False)
    transport_preferences = Column(JSON, default=list, nullable=False)
    base_location_lat = Column(Float, nullable=True)
    base_location_lng = Column(Float, nullable=True)
    base_address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    is_public = Column(Boolean, default=False, nullable=False)
    share_token = Column(String(255), unique=True, nullable=True, index=True)
    collaborators = Column(JSON, default=list, nullable=False)
    total_estimated_cost = Column(Float, default=0.0, nullable=False)
    total_distance_meters = Column(Float, default=0.0, nullable=False)
    poi_count = Column(Integer, default=0, nullable=False)
    tags = Column(JSON, default=list, nullable=False)
    generated_by_ai = Column(Boolean, default=False, nullable=False)
    generation_prompt = Column(Text, nullable=True)
    generation_model = Column(String(100), nullable=True)
    generation_tokens = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    published_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("UserModel", back_populates="itineraries")
    days = relationship("ItineraryDayModel", back_populates="itinerary", lazy="dynamic", order_by="ItineraryDayModel.sequence")

    def to_entity(self):
        """Convert to domain entity"""
        from ....domain.value_objects.coordinates import Coordinates
        return Itinerary(
            id=self.id,
            user_id=self.user_id,
            title=self.title,
            description=self.description,
            status=self.status,
            start_date=datetime.combine(self.start_date, time.min),
            end_date=datetime.combine(self.end_date, time.min),
            budget_level=self.budget_level,
            pace=self.pace,
            interests=self.interests or [],
            accessibility_needs=self.accessibility_needs or [],
            dietary_restrictions=self.dietary_restrictions or [],
            transport_preferences=[TransportMode(t) for t in (self.transport_preferences or [])],
            base_location=Coordinates(latitude=self.base_location_lat, longitude=self.base_location_lng) if self.base_location_lat and self.base_location_lng else None,
            base_address=self.base_address,
            city=self.city,
            country=self.country,
            is_public=self.is_public,
            share_token=self.share_token,
            collaborators=[uuid.UUID(c) for c in (self.collaborators or [])],
            total_estimated_cost=self.total_estimated_cost,
            total_distance_meters=self.total_distance_meters,
            poi_count=self.poi_count,
            tags=self.tags or [],
            generated_by_ai=self.generated_by_ai,
            generation_prompt=self.generation_prompt,
            generation_model=self.generation_model,
            generation_tokens=self.generation_tokens,
            created_at=self.created_at,
            updated_at=self.updated_at,
            published_at=self.published_at,
            completed_at=self.completed_at,
        )

    @classmethod
    def from_entity(cls, entity):
        """Create model from domain entity"""
        return cls(
            id=entity.id,
            user_id=entity.user_id,
            title=entity.title,
            description=entity.description,
            status=entity.status,
            start_date=entity.start_date.date(),
            end_date=entity.end_date.date(),
            budget_level=entity.budget_level,
            pace=entity.pace,
            interests=entity.interests,
            accessibility_needs=entity.accessibility_needs,
            dietary_restrictions=entity.dietary_restrictions,
            transport_preferences=[t.value for t in entity.transport_preferences],
            base_location_lat=entity.base_location.latitude if entity.base_location else None,
            base_location_lng=entity.base_location.longitude if entity.base_location else None,
            base_address=entity.base_address,
            city=entity.city,
            country=entity.country,
            is_public=entity.is_public,
            share_token=entity.share_token,
            collaborators=[str(c) for c in entity.collaborators],
            total_estimated_cost=entity.total_estimated_cost,
            total_distance_meters=entity.total_distance_meters,
            poi_count=entity.poi_count,
            tags=entity.tags,
            generated_by_ai=entity.generated_by_ai,
            generation_prompt=entity.generation_prompt,
            generation_model=entity.generation_model,
            generation_tokens=entity.generation_tokens,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            published_at=entity.published_at,
            completed_at=entity.completed_at,
        )


class ItineraryDayModel(Base):
    """SQLAlchemy model for Itinerary Day"""
    __tablename__ = "itinerary_days"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    itinerary_id = Column(UUID(as_uuid=True), ForeignKey("itineraries.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    sequence = Column(Integer, default=0, nullable=False)
    title = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    start_time = Column(Time, default=time(9, 0), nullable=False)
    end_time = Column(Time, default=time(22, 0), nullable=False)
    base_location_lat = Column(Float, nullable=True)
    base_location_lng = Column(Float, nullable=True)
    base_address = Column(String(500), nullable=True)
    total_duration_minutes = Column(Integer, default=0, nullable=False)
    total_cost = Column(Float, default=0.0, nullable=False)
    total_distance_meters = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    itinerary = relationship("ItineraryModel", back_populates="days")
    items = relationship("ItineraryItemModel", back_populates="day", lazy="dynamic", order_by="ItineraryItemModel.sequence")

    def to_entity(self):
        """Convert to domain entity"""
        from ....domain.value_objects.coordinates import Coordinates
        return ItineraryDay(
            id=self.id,
            date=datetime.combine(self.date, time.min),
            sequence=self.sequence,
            title=self.title,
            notes=self.notes,
            start_time=self.start_time,
            end_time=self.end_time,
            base_location=Coordinates(latitude=self.base_location_lat, longitude=self.base_location_lng) if self.base_location_lat and self.base_location_lng else None,
            base_address=self.base_address,
            items=[],  # Loaded separately
            total_duration_minutes=self.total_duration_minutes,
            total_cost=self.total_cost,
            total_distance_meters=self.total_distance_meters,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_entity(cls, entity, itinerary_id):
        """Create model from domain entity"""
        return cls(
            id=entity.id,
            itinerary_id=itinerary_id,
            date=entity.date.date(),
            sequence=entity.sequence,
            title=entity.title,
            notes=entity.notes,
            start_time=entity.start_time,
            end_time=entity.end_time,
            base_location_lat=entity.base_location.latitude if entity.base_location else None,
            base_location_lng=entity.base_location.longitude if entity.base_location else None,
            base_address=entity.base_address,
            total_duration_minutes=entity.total_duration_minutes,
            total_cost=entity.total_cost,
            total_distance_meters=entity.total_distance_meters,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class ItineraryItemModel(Base):
    """SQLAlchemy model for Itinerary Item"""
    __tablename__ = "itinerary_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    day_id = Column(UUID(as_uuid=True), ForeignKey("itinerary_days.id"), nullable=False, index=True)
    type = Column(SQLEnum(ItineraryItemType), default=ItineraryItemType.POI, nullable=False)
    sequence = Column(Integer, default=0, nullable=False)
    poi_id = Column(UUID(as_uuid=True), ForeignKey("pois.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)
    address = Column(String(500), nullable=True)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    duration_minutes = Column(Integer, default=0, nullable=False)
    transport_mode = Column(SQLEnum(TransportMode), nullable=True)
    transit_details = Column(JSON, default=dict, nullable=False)
    from_location_lat = Column(Float, nullable=True)
    from_location_lng = Column(Float, nullable=True)
    to_location_lat = Column(Float, nullable=True)
    to_location_lng = Column(Float, nullable=True)
    estimated_cost = Column(Float, default=0.0, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    notes = Column(Text, nullable=True)
    is_flexible = Column(Boolean, default=True, nullable=False)
    is_required = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    day = relationship("ItineraryDayModel", back_populates="items")
    poi = relationship("POIModel", back_populates="itinerary_items")

    def to_entity(self):
        """Convert to domain entity"""
        from ....domain.value_objects.coordinates import Coordinates
        return ItineraryItem(
            id=self.id,
            type=self.type,
            sequence=self.sequence,
            poi_id=self.poi_id,
            title=self.title,
            description=self.description,
            coordinates=Coordinates(latitude=self.location_lat, longitude=self.location_lng) if self.location_lat and self.location_lng else None,
            address=self.address,
            start_time=self.start_time,
            end_time=self.end_time,
            duration_minutes=self.duration_minutes,
            transport_mode=self.transport_mode,
            transit_details=self.transit_details or {},
            from_location=Coordinates(latitude=self.from_location_lat, longitude=self.from_location_lng) if self.from_location_lat and self.from_location_lng else None,
            to_location=Coordinates(latitude=self.to_location_lat, longitude=self.to_location_lng) if self.to_location_lat and self.to_location_lng else None,
            estimated_cost=self.estimated_cost,
            currency=self.currency,
            notes=self.notes,
            is_flexible=self.is_flexible,
            is_required=self.is_required,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_entity(cls, entity, day_id):
        """Create model from domain entity"""
        return cls(
            id=entity.id,
            day_id=day_id,
            type=entity.type,
            sequence=entity.sequence,
            poi_id=entity.poi_id,
            title=entity.title,
            description=entity.description,
            location_lat=entity.coordinates.latitude if entity.coordinates else None,
            location_lng=entity.coordinates.longitude if entity.coordinates else None,
            address=entity.address,
            start_time=entity.start_time,
            end_time=entity.end_time,
            duration_minutes=entity.duration_minutes,
            transport_mode=entity.transport_mode,
            transit_details=entity.transit_details,
            from_location_lat=entity.from_location.latitude if entity.from_location else None,
            from_location_lng=entity.from_location.longitude if entity.from_location else None,
            to_location_lat=entity.to_location.latitude if entity.to_location else None,
            to_location_lng=entity.to_location.longitude if entity.to_location else None,
            estimated_cost=entity.estimated_cost,
            currency=entity.currency,
            notes=entity.notes,
            is_flexible=entity.is_flexible,
            is_required=entity.is_required,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
