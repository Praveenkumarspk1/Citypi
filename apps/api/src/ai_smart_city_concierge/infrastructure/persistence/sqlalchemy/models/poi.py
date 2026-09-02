"""
SQLAlchemy POI Model
"""
import uuid
from datetime import datetime

from ai_smart_city_concierge.domain.entities.poi import (
    POI,
    ContactInfo,
    OpeningHours,
    POICategory,
    POISource,
)
from ai_smart_city_concierge.infrastructure.config.database import Base
from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Index, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class POIModel(Base):
    """SQLAlchemy model for POI"""
    __tablename__ = "pois"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(255), nullable=True, index=True)
    source = Column(SQLEnum(POISource), default=POISource.OSM, nullable=False)

    # Basic info
    name = Column(String(255), nullable=False, index=True)
    name_local = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    category = Column(SQLEnum(POICategory), default=POICategory.OTHER, nullable=False, index=True)
    subcategory = Column(String(100), nullable=True)
    tags = Column(JSON, default=list, nullable=False)

    # Location
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True, index=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    neighborhood = Column(String(100), nullable=True)

    # Contact & Hours
    contact_phone = Column(String(50), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_website = Column(String(500), nullable=True)
    contact_facebook = Column(String(255), nullable=True)
    contact_instagram = Column(String(255), nullable=True)
    contact_twitter = Column(String(255), nullable=True)
    opening_hours = Column(JSON, nullable=True)

    # Attributes
    wheelchair_accessible = Column(Boolean, nullable=True)
    wifi_available = Column(Boolean, nullable=True)
    outdoor_seating = Column(Boolean, nullable=True)
    takeaway = Column(Boolean, nullable=True)
    delivery = Column(Boolean, nullable=True)
    reservation_required = Column(Boolean, nullable=True)
    accepts_credit_cards = Column(Boolean, nullable=True)
    accepts_cash = Column(Boolean, nullable=True)
    price_level = Column(Integer, nullable=True)

    # Media
    photos = Column(JSON, default=list, nullable=False)
    featured_photo = Column(String(500), nullable=True)

    # Ratings & Reviews
    rating = Column(Float, nullable=True)
    review_count = Column(Integer, default=0, nullable=False)
    user_ratings_total = Column(Integer, default=0, nullable=False)

    # Popularity & Trends
    popularity_score = Column(Float, default=0.0, nullable=False)
    visit_count = Column(Integer, default=0, nullable=False)
    last_visited_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(UUID(as_uuid=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Vector embedding reference
    embedding_id = Column(String(255), nullable=True)

    # Relationships
    reviews = relationship("FeedbackModel", back_populates="poi", lazy="dynamic")
    media = relationship("MediaModel", back_populates="poi", lazy="dynamic")
    favorites = relationship("FavoriteModel", back_populates="poi", lazy="dynamic")
    itinerary_items = relationship("ItineraryItemModel", back_populates="poi", lazy="dynamic")

    # Indexes
    __table_args__ = (
        Index('ix_pois_location', 'latitude', 'longitude'),
        Index('ix_pois_category_active', 'category', 'is_active'),
        Index('ix_pois_source_external', 'source', 'external_id', unique=True),
    )

    def to_entity(self):
        """Convert to domain entity"""
        return POI(
            id=self.id,
            external_id=self.external_id,
            source=self.source,
            name=self.name,
            name_local=self.name_local,
            description=self.description,
            category=self.category,
            subcategory=self.subcategory,
            tags=self.tags or [],
            coordinates=Coordinates(latitude=self.latitude, longitude=self.longitude),
            address=self.address,
            city=self.city,
            state=self.state,
            country=self.country,
            postal_code=self.postal_code,
            neighborhood=self.neighborhood,
            contact=ContactInfo(
                phone=self.contact_phone,
                email=self.contact_email,
                website=self.contact_website,
                facebook=self.contact_facebook,
                instagram=self.contact_instagram,
                twitter=self.contact_twitter,
            ),
            opening_hours=OpeningHours(**self.opening_hours) if self.opening_hours else None,
            wheelchair_accessible=self.wheelchair_accessible,
            wifi_available=self.wifi_available,
            outdoor_seating=self.outdoor_seating,
            takeaway=self.takeaway,
            delivery=self.delivery,
            reservation_required=self.reservation_required,
            accepts_credit_cards=self.accepts_credit_cards,
            accepts_cash=self.accepts_cash,
            price_level=self.price_level,
            photos=self.photos or [],
            featured_photo=self.featured_photo,
            rating=self.rating,
            review_count=self.review_count,
            user_ratings_total=self.user_ratings_total,
            popularity_score=self.popularity_score,
            visit_count=self.visit_count,
            last_visited_at=self.last_visited_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
            verified_at=self.verified_at,
            verified_by=self.verified_by,
            is_active=self.is_active,
            is_verified=self.is_verified,
            embedding_id=self.embedding_id,
        )

    @classmethod
    def from_entity(cls, entity):
        """Create model from domain entity"""
        return cls(
            id=entity.id,
            external_id=entity.external_id,
            source=entity.source,
            name=entity.name,
            name_local=entity.name_local,
            description=entity.description,
            category=entity.category,
            subcategory=entity.subcategory,
            tags=entity.tags,
            latitude=entity.coordinates.latitude,
            longitude=entity.coordinates.longitude,
            address=entity.address,
            city=entity.city,
            state=entity.state,
            country=entity.country,
            postal_code=entity.postal_code,
            neighborhood=entity.neighborhood,
            contact_phone=entity.contact.phone,
            contact_email=entity.contact.email,
            contact_website=entity.contact.website,
            contact_facebook=entity.contact.facebook,
            contact_instagram=entity.contact.instagram,
            contact_twitter=entity.contact.twitter,
            opening_hours=entity.opening_hours.to_dict() if entity.opening_hours else None,
            wheelchair_accessible=entity.wheelchair_accessible,
            wifi_available=entity.wifi_available,
            outdoor_seating=entity.outdoor_seating,
            takeaway=entity.takeaway,
            delivery=entity.delivery,
            reservation_required=entity.reservation_required,
            accepts_credit_cards=entity.accepts_credit_cards,
            accepts_cash=entity.accepts_cash,
            price_level=entity.price_level,
            photos=entity.photos,
            featured_photo=entity.featured_photo,
            rating=entity.rating,
            review_count=entity.review_count,
            user_ratings_total=entity.user_ratings_total,
            popularity_score=entity.popularity_score,
            visit_count=entity.visit_count,
            last_visited_at=entity.last_visited_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            verified_at=entity.verified_at,
            verified_by=entity.verified_by,
            is_active=entity.is_active,
            is_verified=entity.is_verified,
            embedding_id=entity.embedding_id,
        )


from ai_smart_city_concierge.domain.value_objects.coordinates import Coordinates
