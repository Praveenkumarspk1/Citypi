"""
Analytics Types

Type definitions for analytics and metrics.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class EventType(str, Enum):
    """Analytics event types."""
    # User events
    USER_REGISTERED = "user_registered"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_PROFILE_UPDATED = "user_profile_updated"
    USER_PREFERENCES_UPDATED = "user_preferences_updated"
    USER_DEACTIVATED = "user_deactivated"
    # Conversation events
    CONVERSATION_STARTED = "conversation_started"
    CONVERSATION_ENDED = "conversation_ended"
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    # POI events
    POI_VIEWED = "poi_viewed"
    POI_SEARCHED = "poi_searched"
    POI_FAVORITED = "poi_favorited"
    POI_REVIEWED = "poi_reviewed"
    POI_SHARED = "poi_shared"
    # Itinerary events
    ITINERARY_CREATED = "itinerary_created"
    ITINERARY_VIEWED = "itinerary_viewed"
    ITINERARY_SHARED = "itinerary_shared"
    ITINERARY_EXPORTED = "itinerary_exported"
    ITINERARY_ITEM_COMPLETED = "itinerary_item_completed"
    # Transit events
    TRANSIT_ROUTE_VIEWED = "transit_route_viewed"
    TRANSIT_PREDICTION_VIEWED = "transit_prediction_viewed"
    TRANSIT_ALERT_RECEIVED = "transit_alert_received"
    # Weather events
    WEATHER_VIEWED = "weather_viewed"
    WEATHER_ALERT_RECEIVED = "weather_alert_received"
    # Media events
    MEDIA_UPLOADED = "media_uploaded"
    MEDIA_VIEWED = "media_viewed"
    MEDIA_SHARED = "media_shared"
    # Location events
    LOCATION_SHARED = "location_shared"
    LOCATION_VIEWED = "location_viewed"
    # Notification events
    NOTIFICATION_SENT = "notification_sent"
    NOTIFICATION_OPENED = "notification_opened"
    NOTIFICATION_DISMISSED = "notification_dismissed"
    # Search events
    SEARCH_PERFORMED = "search_performed"
    SEARCH_RESULT_CLICKED = "search_result_clicked"
    # Recommendation events
    RECOMMENDATION_SHOWN = "recommendation_shown"
    RECOMMENDATION_CLICKED = "recommendation_clicked"
    RECOMMENDATION_DISMISSED = "recommendation_dismissed"
    # Error events
    ERROR_OCCURRED = "error_occurred"
    API_ERROR = "api_error"
    # Performance events
    PAGE_LOAD_TIME = "page_load_time"
    API_RESPONSE_TIME = "api_response_time"


class AnalyticsEvent(BaseModel):
    """Analytics event."""
    id: UUID
    event_type: EventType
    user_id: Optional[UUID] = None
    session_id: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnalyticsEventCreate(BaseModel):
    """Analytics event creation request."""
    event_type: EventType
    user_id: Optional[UUID] = None
    session_id: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[datetime] = None


class UserMetrics(BaseModel):
    """Aggregated user metrics."""
    user_id: UUID
    period_start: datetime
    period_end: datetime
    sessions_count: int = 0
    total_session_duration: int = 0  # seconds
    conversations_count: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    pois_viewed: int = 0
    pois_favorited: int = 0
    itineraries_created: int = 0
    itineraries_completed: int = 0
    transit_routes_viewed: int = 0
    weather_checks: int = 0
    media_uploaded: int = 0
    notifications_received: int = 0
    notifications_opened: int = 0
    searches_performed: int = 0
    recommendations_clicked: int = 0
    errors_encountered: int = 0
    avg_session_duration: float = 0.0
    avg_messages_per_session: float = 0.0
    retention_day_1: bool = False
    retention_day_7: bool = False
    retention_day_30: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SystemMetrics(BaseModel):
    """System-wide metrics."""
    period_start: datetime
    period_end: datetime
    total_users: int = 0
    active_users: int = 0
    new_users: int = 0
    returning_users: int = 0
    total_sessions: int = 0
    total_conversations: int = 0
    total_messages: int = 0
    total_poi_views: int = 0
    total_itineraries: int = 0
    total_transit_queries: int = 0
    total_weather_queries: int = 0
    total_media_uploads: int = 0
    total_notifications: int = 0
    total_searches: int = 0
    total_recommendations: int = 0
    total_errors: int = 0
    avg_response_time: float = 0.0
    uptime_percentage: float = 100.0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FunnelStep(BaseModel):
    """Funnel analysis step."""
    step: str
    users: int
    conversion_rate: float
    drop_off_rate: float


class FunnelAnalysis(BaseModel):
    """Funnel analysis result."""
    name: str
    steps: List[FunnelStep]
    overall_conversion_rate: float
    period_start: datetime
    period_end: datetime


class CohortAnalysis(BaseModel):
    """Cohort analysis result."""
    cohort: str
    cohort_size: int
    periods: List[Dict[str, Any]]  # period -> retention data


class RetentionData(BaseModel):
    """Retention metrics."""
    period: str
    cohort_size: int
    retained_users: int
    retention_rate: float