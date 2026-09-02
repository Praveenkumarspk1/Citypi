"""
SQLAlchemy Feedback Models
"""
import uuid
from datetime import datetime

from ai_smart_city_concierge.domain.entities.feedback import (
    Feedback,
    FeedbackSentiment,
    FeedbackStatus,
    FeedbackType,
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


class FeedbackModel(Base):
    """SQLAlchemy model for Feedback"""
    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    type = Column(SQLEnum(FeedbackType), default=FeedbackType.APP_FEEDBACK, nullable=False)
    target_type = Column(String(50), nullable=False, index=True)
    target_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Content
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)

    # Sentiment analysis
    sentiment = Column(SQLEnum(FeedbackSentiment), nullable=True)
    sentiment_score = Column(Float, nullable=True)

    # Categories/tags
    categories = Column(JSON, default=list, nullable=False)
    tags = Column(JSON, default=list, nullable=False)

    # Media attachments
    media_ids = Column(JSON, default=list, nullable=False)

    # Location context
    location = Column(JSON, nullable=True)

    # Status
    status = Column(SQLEnum(FeedbackStatus), default=FeedbackStatus.PENDING, nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)
    is_anonymous = Column(Boolean, default=False, nullable=False)

    # Moderation
    moderated_at = Column(DateTime, nullable=True)
    moderated_by = Column(UUID(as_uuid=True), nullable=True)
    moderation_notes = Column(Text, nullable=True)

    # Response (for bug reports, feature requests)
    response = Column(Text, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    responded_by = Column(UUID(as_uuid=True), nullable=True)

    # Helpfulness
    helpful_count = Column(Integer, default=0, nullable=False)
    unhelpful_count = Column(Integer, default=0, nullable=False)

    # Metadata
    app_version = Column(String(50), nullable=True)
    platform = Column(String(50), nullable=True)
    device_info = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("UserModel", back_populates="feedback")
    poi = relationship("POIModel", back_populates="reviews")

    __table_args__ = (
        Index('ix_feedback_target', 'target_type', 'target_id'),
        Index('ix_feedback_user_type', 'user_id', 'type'),
        Index('ix_feedback_status_created', 'status', 'created_at'),
    )

    def to_entity(self):
        return Feedback(
            id=self.id,
            user_id=self.user_id,
            type=self.type,
            target_type=self.target_type,
            target_id=self.target_id,
            title=self.title,
            content=self.content,
            rating=self.rating,
            sentiment=self.sentiment,
            sentiment_score=self.sentiment_score,
            categories=self.categories or [],
            tags=self.tags or [],
            media_ids=[uuid.UUID(m) for m in (self.media_ids or [])],
            location=self.location,
            status=self.status,
            is_public=self.is_public,
            is_anonymous=self.is_anonymous,
            moderated_at=self.moderated_at,
            moderated_by=self.moderated_by,
            moderation_notes=self.moderation_notes,
            response=self.response,
            responded_at=self.responded_at,
            responded_by=self.responded_by,
            helpful_count=self.helpful_count,
            unhelpful_count=self.unhelpful_count,
            app_version=self.app_version,
            platform=self.platform,
            device_info=self.device_info,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_entity(cls, entity):
        return cls(
            id=entity.id,
            user_id=entity.user_id,
            type=entity.type,
            target_type=entity.target_type,
            target_id=entity.target_id,
            title=entity.title,
            content=entity.content,
            rating=entity.rating,
            sentiment=entity.sentiment,
            sentiment_score=entity.sentiment_score,
            categories=entity.categories,
            tags=entity.tags,
            media_ids=[str(m) for m in entity.media_ids],
            location=entity.location,
            status=entity.status,
            is_public=entity.is_public,
            is_anonymous=entity.is_anonymous,
            moderated_at=entity.moderated_at,
            moderated_by=entity.moderated_by,
            moderation_notes=entity.moderation_notes,
            response=entity.response,
            responded_at=entity.responded_at,
            responded_by=entity.responded_by,
            helpful_count=entity.helpful_count,
            unhelpful_count=entity.unhelpful_count,
            app_version=entity.app_version,
            platform=entity.platform,
            device_info=entity.device_info,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class POIReviewModel(FeedbackModel):
    """SQLAlchemy model for POI Review (extends Feedback)"""
    __tablename__ = "poi_reviews"

    id = Column(UUID(as_uuid=True), ForeignKey("feedback.id"), primary_key=True)

    # POI-specific ratings
    food_rating = Column(Integer, nullable=True)
    service_rating = Column(Integer, nullable=True)
    atmosphere_rating = Column(Integer, nullable=True)
    value_rating = Column(Integer, nullable=True)
    cleanliness_rating = Column(Integer, nullable=True)
    accessibility_rating = Column(Integer, nullable=True)

    # Visit details
    visit_date = Column(DateTime, nullable=True)
    visit_type = Column(String(50), nullable=True)
    party_size = Column(Integer, nullable=True)
    price_per_person = Column(Float, nullable=True)
    currency = Column(String(3), default="USD", nullable=False)

    # Recommendations
    would_recommend = Column(Boolean, nullable=True)
    favorite_dishes = Column(JSON, default=list, nullable=False)

    def to_entity(self):
        entity = super().to_entity()
        return POIReview(
            **{k: v for k, v in entity.__dict__.items() if not k.startswith('_')},
            food_rating=self.food_rating,
            service_rating=self.service_rating,
            atmosphere_rating=self.atmosphere_rating,
            value_rating=self.value_rating,
            cleanliness_rating=self.cleanliness_rating,
            accessibility_rating=self.accessibility_rating,
            visit_date=self.visit_date,
            visit_type=self.visit_type,
            party_size=self.party_size,
            price_per_person=self.price_per_person,
            currency=self.currency,
            would_recommend=self.would_recommend,
            favorite_dishes=self.favorite_dishes or [],
        )

    @classmethod
    def from_entity(cls, entity):
        base = super().from_entity(entity)
        base.food_rating = entity.food_rating
        base.service_rating = entity.service_rating
        base.atmosphere_rating = entity.atmosphere_rating
        base.value_rating = entity.value_rating
        base.cleanliness_rating = entity.cleanliness_rating
        base.accessibility_rating = entity.accessibility_rating
        base.visit_date = entity.visit_date
        base.visit_type = entity.visit_type
        base.party_size = entity.party_size
        base.price_per_person = entity.price_per_person
        base.currency = entity.currency
        base.would_recommend = entity.would_recommend
        base.favorite_dishes = entity.favorite_dishes
        return base


class ItineraryReviewModel(FeedbackModel):
    """SQLAlchemy model for Itinerary Review (extends Feedback)"""
    __tablename__ = "itinerary_reviews"

    id = Column(UUID(as_uuid=True), ForeignKey("feedback.id"), primary_key=True)

    # Itinerary-specific ratings
    pacing_rating = Column(Integer, nullable=True)
    variety_rating = Column(Integer, nullable=True)
    accuracy_rating = Column(Integer, nullable=True)
    usefulness_rating = Column(Integer, nullable=True)

    # Completion
    completed = Column(Boolean, default=False, nullable=False)
    completion_date = Column(DateTime, nullable=True)
    days_completed = Column(Integer, default=0, nullable=False)
    total_days = Column(Integer, default=0, nullable=False)

    # Modifications
    modified_itin = Column(Boolean, default=False, nullable=False)
    modifications = Column(JSON, default=list, nullable=False)

    def to_entity(self):
        entity = super().to_entity()
        return ItineraryReview(
            **{k: v for k, v in entity.__dict__.items() if not k.startswith('_')},
            pacing_rating=self.pacing_rating,
            variety_rating=self.variety_rating,
            accuracy_rating=self.accuracy_rating,
            usefulness_rating=self.usefulness_rating,
            completed=self.completed,
            completion_date=self.completion_date,
            days_completed=self.days_completed,
            total_days=self.total_days,
            modified_itin=self.modified_itin,
            modifications=self.modifications or [],
        )

    @classmethod
    def from_entity(cls, entity):
        base = super().from_entity(entity)
        base.pacing_rating = entity.pacing_rating
        base.variety_rating = entity.variety_rating
        base.accuracy_rating = entity.accuracy_rating
        base.usefulness_rating = entity.usefulness_rating
        base.completed = entity.completed
        base.completion_date = entity.completion_date
        base.days_completed = entity.days_completed
        base.total_days = entity.total_days
        base.modified_itin = entity.modified_itin
        base.modifications = entity.modifications
        return base


class TransitFeedbackModel(FeedbackModel):
    """SQLAlchemy model for Transit Feedback (extends Feedback)"""
    __tablename__ = "transit_feedback"

    id = Column(UUID(as_uuid=True), ForeignKey("feedback.id"), primary_key=True)

    # Transit-specific ratings
    punctuality_rating = Column(Integer, nullable=True)
    cleanliness_rating = Column(Integer, nullable=True)
    comfort_rating = Column(Integer, nullable=True)
    safety_rating = Column(Integer, nullable=True)
    accessibility_rating = Column(Integer, nullable=True)
    information_rating = Column(Integer, nullable=True)

    # Trip details
    route_id = Column(String(100), nullable=True)
    trip_id = Column(String(100), nullable=True)
    stop_id = Column(String(100), nullable=True)
    direction = Column(String(50), nullable=True)
    scheduled_time = Column(DateTime, nullable=True)
    actual_time = Column(DateTime, nullable=True)
    delay_minutes = Column(Integer, nullable=True)

    # Issue categories
    issue_categories = Column(JSON, default=list, nullable=False)

    def to_entity(self):
        entity = super().to_entity()
        return TransitFeedback(
            **{k: v for k, v in entity.__dict__.items() if not k.startswith('_')},
            punctuality_rating=self.punctuality_rating,
            cleanliness_rating=self.cleanliness_rating,
            comfort_rating=self.comfort_rating,
            safety_rating=self.safety_rating,
            accessibility_rating=self.accessibility_rating,
            information_rating=self.information_rating,
            route_id=self.route_id,
            trip_id=self.trip_id,
            stop_id=self.stop_id,
            direction=self.direction,
            scheduled_time=self.scheduled_time,
            actual_time=self.actual_time,
            delay_minutes=self.delay_minutes,
            issue_categories=self.issue_categories or [],
        )

    @classmethod
    def from_entity(cls, entity):
        base = super().from_entity(entity)
        base.punctuality_rating = entity.punctuality_rating
        base.cleanliness_rating = entity.cleanliness_rating
        base.comfort_rating = entity.comfort_rating
        base.safety_rating = entity.safety_rating
        base.accessibility_rating = entity.accessibility_rating
        base.information_rating = entity.information_rating
        base.route_id = entity.route_id
        base.trip_id = entity.trip_id
        base.stop_id = entity.stop_id
        base.direction = entity.direction
        base.scheduled_time = entity.scheduled_time
        base.actual_time = entity.actual_time
        base.delay_minutes = entity.delay_minutes
        base.issue_categories = entity.issue_categories
        return base


class RecommendationFeedbackModel(FeedbackModel):
    """SQLAlchemy model for Recommendation Feedback (extends Feedback)"""
    __tablename__ = "recommendation_feedback"

    id = Column(UUID(as_uuid=True), ForeignKey("feedback.id"), primary_key=True)

    # Recommendation details
    recommendation_id = Column(UUID(as_uuid=True), nullable=True)
    recommendation_type = Column(String(50), nullable=True)
    algorithm = Column(String(100), nullable=True)

    # Feedback
    relevance_rating = Column(Integer, nullable=True)
    action_taken = Column(String(50), nullable=True)
    action_timestamp = Column(DateTime, nullable=True)

    # Context
    context = Column(JSON, default=dict, nullable=False)

    def to_entity(self):
        entity = super().to_entity()
        return RecommendationFeedback(
            **{k: v for k, v in entity.__dict__.items() if not k.startswith('_')},
            recommendation_id=self.recommendation_id,
            recommendation_type=self.recommendation_type,
            algorithm=self.algorithm,
            relevance_rating=self.relevance_rating,
            action_taken=self.action_taken,
            action_timestamp=self.action_timestamp,
            context=self.context or {},
        )

    @classmethod
    def from_entity(cls, entity):
        base = super().from_entity(entity)
        base.recommendation_id = entity.recommendation_id
        base.recommendation_type = entity.recommendation_type
        base.algorithm = entity.algorithm
        base.relevance_rating = entity.relevance_rating
        base.action_taken = entity.action_taken
        base.action_timestamp = entity.action_timestamp
        base.context = entity.context
        return base
