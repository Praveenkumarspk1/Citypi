"""
Feedback Domain Entities
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class FeedbackType(StrEnum):
    POI_REVIEW = "poi_review"
    ITINERARY_REVIEW = "itinerary_review"
    TRANSIT_FEEDBACK = "transit_feedback"
    APP_FEEDBACK = "app_feedback"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    CONTENT_MODERATION = "content_moderation"
    RECOMMENDATION_FEEDBACK = "recommendation_feedback"


class FeedbackSentiment(StrEnum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class FeedbackStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"
    RESOLVED = "resolved"


@dataclass
class Feedback:
    """
    Feedback aggregate root.
    Represents user feedback on various entities.
    """
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    type: FeedbackType = FeedbackType.APP_FEEDBACK

    # Target entity
    target_type: str = ""  # poi, itinerary, transit, app, etc.
    target_id: UUID = field(default_factory=uuid4)

    # Content
    title: str | None = None
    content: str = ""
    rating: int | None = None  # 1-5

    # Sentiment analysis
    sentiment: FeedbackSentiment | None = None
    sentiment_score: float | None = None  # -1 to 1

    # Categories/tags
    categories: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    # Media attachments
    media_ids: list[UUID] = field(default_factory=list)

    # Location context
    location: dict[str, Any] | None = None  # coordinates, address

    # Status
    status: FeedbackStatus = FeedbackStatus.PENDING
    is_public: bool = True
    is_anonymous: bool = False

    # Moderation
    moderated_at: datetime | None = None
    moderated_by: UUID | None = None
    moderation_notes: str | None = None

    # Response (for bug reports, feature requests)
    response: str | None = None
    responded_at: datetime | None = None
    responded_by: UUID | None = None

    # Helpfulness
    helpful_count: int = 0
    unhelpful_count: int = 0

    # Metadata
    app_version: str | None = None
    platform: str | None = None
    device_info: dict[str, Any] | None = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        if not self.content:
            raise ValueError("Feedback content is required")
        if self.rating is not None and not 1 <= self.rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

    def approve(self, moderator_id: UUID) -> None:
        """Approve feedback"""
        self.status = FeedbackStatus.APPROVED
        self.moderated_at = datetime.utcnow()
        self.moderated_by = moderator_id
        self.updated_at = datetime.utcnow()

    def reject(self, moderator_id: UUID, notes: str) -> None:
        """Reject feedback"""
        self.status = FeedbackStatus.REJECTED
        self.moderated_at = datetime.utcnow()
        self.moderated_by = moderator_id
        self.moderation_notes = notes
        self.updated_at = datetime.utcnow()

    def flag(self, moderator_id: UUID, notes: str) -> None:
        """Flag feedback"""
        self.status = FeedbackStatus.FLAGGED
        self.moderated_at = datetime.utcnow()
        self.moderated_by = moderator_id
        self.moderation_notes = notes
        self.updated_at = datetime.utcnow()

    def resolve(self, moderator_id: UUID, response: str) -> None:
        """Resolve feedback (for bug reports, feature requests)"""
        self.status = FeedbackStatus.RESOLVED
        self.response = response
        self.responded_at = datetime.utcnow()
        self.responded_by = moderator_id
        self.updated_at = datetime.utcnow()

    def mark_helpful(self) -> None:
        """Mark as helpful"""
        self.helpful_count += 1
        self.updated_at = datetime.utcnow()

    def mark_unhelpful(self) -> None:
        """Mark as unhelpful"""
        self.unhelpful_count += 1
        self.updated_at = datetime.utcnow()

    def get_helpfulness_ratio(self) -> float:
        """Get helpfulness ratio"""
        total = self.helpful_count + self.unhelpful_count
        if total == 0:
            return 0.0
        return self.helpful_count / total

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "type": self.type.value,
            "target_type": self.target_type,
            "target_id": str(self.target_id),
            "title": self.title,
            "content": self.content,
            "rating": self.rating,
            "sentiment": self.sentiment.value if self.sentiment else None,
            "sentiment_score": self.sentiment_score,
            "categories": self.categories,
            "tags": self.tags,
            "media_ids": [str(mid) for mid in self.media_ids],
            "location": self.location,
            "status": self.status.value,
            "is_public": self.is_public,
            "is_anonymous": self.is_anonymous,
            "moderated_at": self.moderated_at.isoformat() if self.moderated_at else None,
            "moderated_by": str(self.moderated_by) if self.moderated_by else None,
            "moderation_notes": self.moderation_notes,
            "response": self.response,
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
            "responded_by": str(self.responded_by) if self.responded_by else None,
            "helpful_count": self.helpful_count,
            "unhelpful_count": self.unhelpful_count,
            "helpfulness_ratio": self.get_helpfulness_ratio(),
            "app_version": self.app_version,
            "platform": self.platform,
            "device_info": self.device_info,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class POIReview(Feedback):
    """POI-specific review"""
    type: FeedbackType = FeedbackType.POI_REVIEW
    target_type: str = "poi"

    # POI-specific ratings
    food_rating: int | None = None
    service_rating: int | None = None
    atmosphere_rating: int | None = None
    value_rating: int | None = None
    cleanliness_rating: int | None = None
    accessibility_rating: int | None = None

    # Visit details
    visit_date: datetime | None = None
    visit_type: str | None = None  # dine_in, takeout, delivery, etc.
    party_size: int | None = None
    price_per_person: float | None = None
    currency: str = "USD"

    # Recommendations
    would_recommend: bool | None = None
    favorite_dishes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "food_rating": self.food_rating,
            "service_rating": self.service_rating,
            "atmosphere_rating": self.atmosphere_rating,
            "value_rating": self.value_rating,
            "cleanliness_rating": self.cleanliness_rating,
            "accessibility_rating": self.accessibility_rating,
            "visit_date": self.visit_date.isoformat() if self.visit_date else None,
            "visit_type": self.visit_type,
            "party_size": self.party_size,
            "price_per_person": self.price_per_person,
            "currency": self.currency,
            "would_recommend": self.would_recommend,
            "favorite_dishes": self.favorite_dishes,
        })
        return data


@dataclass
class ItineraryReview(Feedback):
    """Itinerary-specific review"""
    type: FeedbackType = FeedbackType.ITINERARY_REVIEW
    target_type: str = "itinerary"

    # Itinerary-specific ratings
    pacing_rating: int | None = None
    variety_rating: int | None = None
    accuracy_rating: int | None = None
    usefulness_rating: int | None = None

    # Completion
    completed: bool = False
    completion_date: datetime | None = None
    days_completed: int = 0
    total_days: int = 0

    # Modifications
    modified_itin: bool = False
    modifications: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "pacing_rating": self.pacing_rating,
            "variety_rating": self.variety_rating,
            "accuracy_rating": self.accuracy_rating,
            "usefulness_rating": self.usefulness_rating,
            "completed": self.completed,
            "completion_date": self.completion_date.isoformat() if self.completion_date else None,
            "days_completed": self.days_completed,
            "total_days": self.total_days,
            "modified_itin": self.modified_itin,
            "modifications": self.modifications,
        })
        return data


@dataclass
class TransitFeedback(Feedback):
    """Transit-specific feedback"""
    type: FeedbackType = FeedbackType.TRANSIT_FEEDBACK
    target_type: str = "transit"

    # Transit-specific ratings
    punctuality_rating: int | None = None
    cleanliness_rating: int | None = None
    comfort_rating: int | None = None
    safety_rating: int | None = None
    accessibility_rating: int | None = None
    information_rating: int | None = None

    # Trip details
    route_id: str | None = None
    trip_id: str | None = None
    stop_id: str | None = None
    direction: str | None = None
    scheduled_time: datetime | None = None
    actual_time: datetime | None = None
    delay_minutes: int | None = None

    # Issue categories
    issue_categories: list[str] = field(default_factory=list)  # delay, crowding, cleanliness, etc.

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "punctuality_rating": self.punctuality_rating,
            "cleanliness_rating": self.cleanliness_rating,
            "comfort_rating": self.comfort_rating,
            "safety_rating": self.safety_rating,
            "accessibility_rating": self.accessibility_rating,
            "information_rating": self.information_rating,
            "route_id": self.route_id,
            "trip_id": self.trip_id,
            "stop_id": self.stop_id,
            "direction": self.direction,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "actual_time": self.actual_time.isoformat() if self.actual_time else None,
            "delay_minutes": self.delay_minutes,
            "issue_categories": self.issue_categories,
        })
        return data


@dataclass
class RecommendationFeedback(Feedback):
    """Feedback on AI recommendations"""
    type: FeedbackType = FeedbackType.RECOMMENDATION_FEEDBACK
    target_type: str = "recommendation"

    # Recommendation details
    recommendation_id: UUID | None = None
    recommendation_type: str | None = None  # poi, itinerary, route, etc.
    algorithm: str | None = None

    # Feedback
    relevance_rating: int | None = None  # 1-5
    action_taken: str | None = None  # visited, saved, dismissed, shared
    action_timestamp: datetime | None = None

    # Context
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "recommendation_id": str(self.recommendation_id) if self.recommendation_id else None,
            "recommendation_type": self.recommendation_type,
            "algorithm": self.algorithm,
            "relevance_rating": self.relevance_rating,
            "action_taken": self.action_taken,
            "action_timestamp": self.action_timestamp.isoformat() if self.action_timestamp else None,
            "context": self.context,
        })
        return data
