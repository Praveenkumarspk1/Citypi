"""
Analytics Domain Entities
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class EventType(StrEnum):
    """Analytics event types"""
    # User events
    USER_REGISTERED = "user_registered"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_PROFILE_UPDATED = "user_profile_updated"
    USER_PREFERENCES_UPDATED = "user_preferences_updated"

    # Conversation events
    CONVERSATION_STARTED = "conversation_started"
    CONVERSATION_MESSAGE_SENT = "conversation_message_sent"
    CONVERSATION_MESSAGE_RECEIVED = "conversation_message_received"
    CONVERSATION_ENDED = "conversation_ended"
    CONVERSATION_ARCHIVED = "conversation_archived"

    # POI events
    POI_VIEWED = "poi_viewed"
    POI_SEARCHED = "poi_searched"
    POI_FAVORITED = "poi_favorited"
    POI_UNFAVORITED = "poi_unfavorited"
    POI_SHARED = "poi_shared"
    POI_REVIEWED = "poi_reviewed"
    POI_PHOTO_UPLOADED = "poi_photo_uploaded"
    POI_DIRECTIONS_REQUESTED = "poi_directions_requested"

    # Itinerary events
    ITINERARY_CREATED = "itinerary_created"
    ITINERARY_VIEWED = "itinerary_viewed"
    ITINERARY_UPDATED = "itinerary_updated"
    ITINERARY_DELETED = "itinerary_deleted"
    ITINERARY_SHARED = "itinerary_shared"
    ITINERARY_DAY_ADDED = "itinerary_day_added"
    ITINERARY_ITEM_ADDED = "itinerary_item_added"
    ITINERARY_ITEM_REMOVED = "itinerary_item_removed"
    ITINERARY_ACTIVATED = "itinerary_activated"
    ITINERARY_COMPLETED = "itinerary_completed"
    ITINERARY_EXPORTED = "itinerary_exported"

    # Transit events
    TRANSIT_ROUTE_SEARCHED = "transit_route_searched"
    TRANSIT_ROUTE_VIEWED = "transit_route_viewed"
    TRANSIT_STOP_VIEWED = "transit_stop_viewed"
    TRANSIT_REALTIME_VIEWED = "transit_realtime_viewed"
    TRANSIT_FEEDBACK_SUBMITTED = "transit_feedback_submitted"

    # Weather events
    WEATHER_VIEWED = "weather_viewed"
    WEATHER_ALERT_VIEWED = "weather_alert_viewed"

    # Media events
    MEDIA_UPLOADED = "media_uploaded"
    MEDIA_VIEWED = "media_viewed"
    MEDIA_DOWNLOADED = "media_downloaded"
    MEDIA_SHARED = "media_shared"

    # Voice/Image AI events
    VOICE_MESSAGE_SENT = "voice_message_sent"
    VOICE_TRANSCRIPTION_COMPLETED = "voice_transcription_completed"
    IMAGE_ANALYSIS_REQUESTED = "image_analysis_requested"
    IMAGE_ANALYSIS_COMPLETED = "image_analysis_completed"

    # Recommendation events
    RECOMMENDATION_SHOWN = "recommendation_shown"
    RECOMMENDATION_CLICKED = "recommendation_clicked"
    RECOMMENDATION_DISMISSED = "recommendation_dismissed"
    RECOMMENDATION_SAVED = "recommendation_saved"
    RECOMMENDATION_FEEDBACK = "recommendation_feedback"

    # Search events
    SEARCH_PERFORMED = "search_performed"
    SEARCH_RESULT_CLICKED = "search_result_clicked"
    SEARCH_FILTERS_APPLIED = "search_filters_applied"

    # Map events
    MAP_VIEWED = "map_viewed"
    MAP_ZOOM_CHANGED = "map_zoom_changed"
    MAP_LAYER_TOGGLED = "map_layer_toggled"
    MAP_MARKER_CLICKED = "map_marker_clicked"

    # Error events
    ERROR_OCCURRED = "error_occurred"
    API_ERROR = "api_error"

    # Performance events
    PAGE_LOAD_TIME = "page_load_time"
    API_RESPONSE_TIME = "api_response_time"


class EventSource(StrEnum):
    """Event source"""
    WEB = "web"
    MOBILE_IOS = "mobile_ios"
    MOBILE_ANDROID = "mobile_android"
    API = "api"
    WORKER = "worker"
    WEBSOCKET = "websocket"


@dataclass
class AnalyticsEvent:
    """
    Analytics event entity.
    Immutable event record for analytics processing.
    """
    id: UUID = field(default_factory=uuid4)
    event_type: EventType = EventType.USER_LOGIN
    user_id: UUID | None = None
    session_id: str | None = None

    # Event properties
    properties: dict[str, Any] = field(default_factory=dict)

    # Context
    source: EventSource = EventSource.WEB
    app_version: str | None = None
    platform: str | None = None
    device_id: str | None = None

    # Location context
    coordinates: dict[str, float] | None = None
    city: str | None = None
    country: str | None = None

    # Timing
    timestamp: datetime = field(default_factory=datetime.utcnow)
    processing_time_ms: int | None = None

    # Metadata
    correlation_id: str | None = None
    experiment_id: str | None = None
    variant: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "event_type": self.event_type.value,
            "user_id": str(self.user_id) if self.user_id else None,
            "session_id": self.session_id,
            "properties": self.properties,
            "source": self.source.value,
            "app_version": self.app_version,
            "platform": self.platform,
            "device_id": self.device_id,
            "coordinates": self.coordinates,
            "city": self.city,
            "country": self.country,
            "timestamp": self.timestamp.isoformat(),
            "processing_time_ms": self.processing_time_ms,
            "correlation_id": self.correlation_id,
            "experiment_id": self.experiment_id,
            "variant": self.variant,
        }

    @classmethod
    def create(
        cls,
        event_type: EventType,
        user_id: UUID | None = None,
        session_id: str | None = None,
        properties: dict[str, Any] | None = None,
        source: EventSource = EventSource.WEB,
        **kwargs
    ) -> "AnalyticsEvent":
        """Factory method to create event"""
        return cls(
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            properties=properties or {},
            source=source,
            **kwargs
        )


@dataclass
class DailyMetrics:
    """Daily aggregated metrics"""
    date: date = field(default_factory=date.today)

    # User metrics
    total_users: int = 0
    new_users: int = 0
    active_users: int = 0
    returning_users: int = 0
    dau: int = 0  # Daily active users
    mau: int = 0  # Monthly active users (approx)

    # Session metrics
    total_sessions: int = 0
    avg_session_duration_seconds: float = 0.0
    avg_pages_per_session: float = 0.0
    bounce_rate: float = 0.0

    # Conversation metrics
    conversations_started: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    avg_conversation_length: float = 0.0
    avg_response_time_ms: float = 0.0

    # POI metrics
    poi_searches: int = 0
    poi_views: int = 0
    poi_favorites_added: int = 0
    poi_reviews_submitted: int = 0
    poi_photos_uploaded: int = 0

    # Itinerary metrics
    itineraries_created: int = 0
    itineraries_viewed: int = 0
    itineraries_completed: int = 0
    itineraries_shared: int = 0
    avg_itinerary_days: float = 0.0
    avg_pois_per_itinerary: float = 0.0

    # Transit metrics
    transit_searches: int = 0
    transit_routes_viewed: int = 0
    transit_feedback_submitted: int = 0

    # Weather metrics
    weather_views: int = 0
    weather_alerts_viewed: int = 0

    # AI metrics
    voice_messages: int = 0
    image_analyses: int = 0
    recommendations_shown: int = 0
    recommendations_clicked: int = 0
    recommendation_ctr: float = 0.0

    # Search metrics
    searches_performed: int = 0
    search_results_clicked: int = 0
    zero_result_searches: int = 0

    # Error metrics
    total_errors: int = 0
    error_rate: float = 0.0
    api_errors: int = 0

    # Performance metrics
    avg_page_load_ms: float = 0.0
    avg_api_response_ms: float = 0.0
    p95_api_response_ms: float = 0.0
    p99_api_response_ms: float = 0.0

    # Revenue/Business metrics (if applicable)
    premium_signups: int = 0
    premium_churn: int = 0
    revenue: float = 0.0

    # Timestamps
    calculated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "date": self.date.isoformat(),
            "total_users": self.total_users,
            "new_users": self.new_users,
            "active_users": self.active_users,
            "returning_users": self.returning_users,
            "dau": self.dau,
            "mau": self.mau,
            "total_sessions": self.total_sessions,
            "avg_session_duration_seconds": self.avg_session_duration_seconds,
            "avg_pages_per_session": self.avg_pages_per_session,
            "bounce_rate": self.bounce_rate,
            "conversations_started": self.conversations_started,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "avg_conversation_length": self.avg_conversation_length,
            "avg_response_time_ms": self.avg_response_time_ms,
            "poi_searches": self.poi_searches,
            "poi_views": self.poi_views,
            "poi_favorites_added": self.poi_favorites_added,
            "poi_reviews_submitted": self.poi_reviews_submitted,
            "poi_photos_uploaded": self.poi_photos_uploaded,
            "itineraries_created": self.itineraries_created,
            "itineraries_viewed": self.itineraries_viewed,
            "itineraries_completed": self.itineraries_completed,
            "itineraries_shared": self.itineraries_shared,
            "avg_itinerary_days": self.avg_itinerary_days,
            "avg_pois_per_itinerary": self.avg_pois_per_itinerary,
            "transit_searches": self.transit_searches,
            "transit_routes_viewed": self.transit_routes_viewed,
            "transit_feedback_submitted": self.transit_feedback_submitted,
            "weather_views": self.weather_views,
            "weather_alerts_viewed": self.weather_alerts_viewed,
            "voice_messages": self.voice_messages,
            "image_analyses": self.image_analyses,
            "recommendations_shown": self.recommendations_shown,
            "recommendations_clicked": self.recommendations_clicked,
            "recommendation_ctr": self.recommendation_ctr,
            "searches_performed": self.searches_performed,
            "search_results_clicked": self.search_results_clicked,
            "zero_result_searches": self.zero_result_searches,
            "total_errors": self.total_errors,
            "error_rate": self.error_rate,
            "api_errors": self.api_errors,
            "avg_page_load_ms": self.avg_page_load_ms,
            "avg_api_response_ms": self.avg_api_response_ms,
            "p95_api_response_ms": self.p95_api_response_ms,
            "p99_api_response_ms": self.p99_api_response_ms,
            "premium_signups": self.premium_signups,
            "premium_churn": self.premium_churn,
            "revenue": self.revenue,
            "calculated_at": self.calculated_at.isoformat(),
        }


@dataclass
class UserMetrics:
    """Per-user aggregated metrics"""
    user_id: UUID = field(default_factory=uuid4)

    # Activity
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    total_sessions: int = 0
    total_session_duration_seconds: int = 0
    days_active: int = 0

    # Conversations
    conversations_count: int = 0
    messages_sent: int = 0
    avg_conversation_length: float = 0.0

    # POI interactions
    poi_searches: int = 0
    poi_views: int = 0
    favorites_count: int = 0
    reviews_written: int = 0
    photos_uploaded: int = 0

    # Itinerary interactions
    itineraries_created: int = 0
    itineraries_completed: int = 0
    itineraries_shared: int = 0

    # Transit
    transit_searches: int = 0
    transit_feedback_count: int = 0

    # AI usage
    voice_messages_sent: int = 0
    images_analyzed: int = 0
    recommendations_clicked: int = 0
    recommendations_dismissed: int = 0

    # Preferences (inferred)
    preferred_categories: list[str] = field(default_factory=list)
    preferred_transport_modes: list[str] = field(default_factory=list)
    active_hours: list[int] = field(default_factory=list)  # 0-23
    active_days: list[int] = field(default_factory=list)  # 0-6 (Mon-Sun)

    # Engagement score
    engagement_score: float = 0.0
    churn_risk: float = 0.0

    # Timestamps
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "user_id": str(self.user_id),
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "total_sessions": self.total_sessions,
            "total_session_duration_seconds": self.total_session_duration_seconds,
            "days_active": self.days_active,
            "conversations_count": self.conversations_count,
            "messages_sent": self.messages_sent,
            "avg_conversation_length": self.avg_conversation_length,
            "poi_searches": self.poi_searches,
            "poi_views": self.poi_views,
            "favorites_count": self.favorites_count,
            "reviews_written": self.reviews_written,
            "photos_uploaded": self.photos_uploaded,
            "itineraries_created": self.itineraries_created,
            "itineraries_completed": self.itineraries_completed,
            "itineraries_shared": self.itineraries_shared,
            "transit_searches": self.transit_searches,
            "transit_feedback_count": self.transit_feedback_count,
            "voice_messages_sent": self.voice_messages_sent,
            "images_analyzed": self.images_analyzed,
            "recommendations_clicked": self.recommendations_clicked,
            "recommendations_dismissed": self.recommendations_dismissed,
            "preferred_categories": self.preferred_categories,
            "preferred_transport_modes": self.preferred_transport_modes,
            "active_hours": self.active_hours,
            "active_days": self.active_days,
            "engagement_score": self.engagement_score,
            "churn_risk": self.churn_risk,
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class FunnelStep:
    """Funnel analysis step"""
    step: str = ""
    event_type: EventType = EventType.USER_LOGIN
    count: int = 0
    conversion_rate: float = 0.0
    drop_off_rate: float = 0.0
    avg_time_to_next_step_seconds: float | None = None


@dataclass
class FunnelAnalysis:
    """Funnel analysis result"""
    name: str = ""
    steps: list[FunnelStep] = field(default_factory=list)
    total_conversions: int = 0
    overall_conversion_rate: float = 0.0
    date_range_start: date = field(default_factory=date.today)
    date_range_end: date = field(default_factory=date.today)
    segment: str | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "steps": [
                {
                    "step": s.step,
                    "event_type": s.event_type.value,
                    "count": s.count,
                    "conversion_rate": s.conversion_rate,
                    "drop_off_rate": s.drop_off_rate,
                    "avg_time_to_next_step_seconds": s.avg_time_to_next_step_seconds,
                }
                for s in self.steps
            ],
            "total_conversions": self.total_conversions,
            "overall_conversion_rate": self.overall_conversion_rate,
            "date_range_start": self.date_range_start.isoformat(),
            "date_range_end": self.date_range_end.isoformat(),
            "segment": self.segment,
        }


@dataclass
class CohortAnalysis:
    """Cohort retention analysis"""
    cohort_date: date = field(default_factory=date.today)
    cohort_size: int = 0
    retention: dict[int, float] = field(default_factory=dict)  # day -> retention rate
    segment: str | None = None

    def to_dict(self) -> dict:
        return {
            "cohort_date": self.cohort_date.isoformat(),
            "cohort_size": self.cohort_size,
            "retention": {str(k): v for k, v in self.retention.items()},
            "segment": self.segment,
        }


@dataclass
class FeatureUsage:
    """Feature usage statistics"""
    feature: str = ""
    total_users: int = 0
    total_events: int = 0
    avg_events_per_user: float = 0.0
    adoption_rate: float = 0.0  # % of active users using feature
    power_users: int = 0  # users with > 10 events
    date_range_start: date = field(default_factory=date.today)
    date_range_end: date = field(default_factory=date.today)

    def to_dict(self) -> dict:
        return {
            "feature": self.feature,
            "total_users": self.total_users,
            "total_events": self.total_events,
            "avg_events_per_user": self.avg_events_per_user,
            "adoption_rate": self.adoption_rate,
            "power_users": self.power_users,
            "date_range_start": self.date_range_start.isoformat(),
            "date_range_end": self.date_range_end.isoformat(),
        }

