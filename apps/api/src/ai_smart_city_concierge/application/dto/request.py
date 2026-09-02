"""
Request DTOs
"""
from dataclasses import dataclass, field
from datetime import date, time
from typing import Any
from uuid import UUID

from ai_smart_city_concierge.domain.entities.conversation import (
    ConversationStatus,
    MessageRole,
    MessageType,
)
from ai_smart_city_concierge.domain.entities.feedback import FeedbackStatus, FeedbackType
from ai_smart_city_concierge.domain.entities.itinerary import (
    ItineraryItemType,
    ItineraryStatus,
    TransportMode,
)
from ai_smart_city_concierge.domain.entities.media import MediaSource, MediaType
from ai_smart_city_concierge.domain.entities.poi import POICategory, POISource
from ai_smart_city_concierge.domain.value_objects.coordinates import Coordinates


# User Requests
@dataclass
class CreateUserRequest:
    email: str
    display_name: str | None = None
    firebase_uid: str | None = None
    google_id: str | None = None
    password: str | None = None
    locale: str = "en"
    timezone: str = "UTC"
    interests: list[str] = field(default_factory=list)
    budget_level: str = "moderate"
    accessibility_needs: list[str] = field(default_factory=list)
    dietary_restrictions: list[str] = field(default_factory=list)
    preferred_transport_modes: list[str] = field(default_factory=list)


@dataclass
class UpdateUserProfileRequest:
    display_name: str | None = None
    avatar_url: str | None = None
    locale: str | None = None
    timezone: str | None = None


@dataclass
class UpdateUserPreferencesRequest:
    interests: list[str] | None = None
    budget_level: str | None = None
    accessibility_needs: list[str] | None = None
    dietary_restrictions: list[str] | None = None
    preferred_transport_modes: list[str] | None = None


@dataclass
class UserLoginRequest:
    email: str
    password: str
    firebase_token: str | None = None
    google_token: str | None = None


@dataclass
class RefreshTokenRequest:
    refresh_token: str


# POI Requests
@dataclass
class CreatePOIRequest:
    name: str
    name_local: str | None = None
    description: str | None = None
    category: POICategory = POICategory.OTHER
    subcategory: str | None = None
    tags: list[str] = field(default_factory=list)
    coordinates: Coordinates = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None
    neighborhood: str | None = None
    contact: dict[str, Any] | None = None
    opening_hours: dict[str, Any] | None = None
    external_id: str | None = None
    source: POISource = POISource.MANUAL

    def __post_init__(self):
        if self.coordinates is None:
            self.coordinates = Coordinates(0, 0)


@dataclass
class UpdatePOIRequest:
    name: str | None = None
    name_local: str | None = None
    description: str | None = None
    category: POICategory | None = None
    subcategory: str | None = None
    tags: list[str] | None = None
    coordinates: Coordinates | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None
    neighborhood: str | None = None
    contact: dict[str, Any] | None = None
    opening_hours: dict[str, Any] | None = None
    wheelchair_accessible: bool | None = None
    wifi_available: bool | None = None
    outdoor_seating: bool | None = None
    takeaway: bool | None = None
    delivery: bool | None = None
    reservation_required: bool | None = None
    accepts_credit_cards: bool | None = None
    accepts_cash: bool | None = None
    price_level: int | None = None


@dataclass
class AddPOIPhotoRequest:
    photo_url: str
    featured: bool = False


@dataclass
class UpdatePOIRatingRequest:
    rating: float
    review_count: int


@dataclass
class VerifyPOIRequest:
    verified_by: UUID


@dataclass
class FavoritePOIRequest:
    user_id: UUID


# Conversation Requests
@dataclass
class StartConversationRequest:
    user_id: UUID
    title: str | None = None
    language: str = "en"
    location: Coordinates | None = None
    context: dict[str, Any] = field(default_factory=dict)
    initial_message: str | None = None
    initial_message_type: MessageType = MessageType.TEXT


@dataclass
class AddMessageRequest:
    role: MessageRole
    content: str
    type: MessageType = MessageType.TEXT
    tokens: int = 0
    model: str | None = None
    processing_time_ms: int = 0
    attachments: list[dict[str, Any]] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_call_id: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    location: Coordinates | None = None


@dataclass
class UpdateConversationRequest:
    title: str | None = None
    language: str | None = None
    location: Coordinates | None = None
    context: dict[str, Any] | None = None
    status: ConversationStatus | None = None


@dataclass
class UpdateConversationSummaryRequest:
    summary: str


# Itinerary Requests
@dataclass
class CreateItineraryRequest:
    user_id: UUID
    title: str
    description: str | None = None
    start_date: date = None
    end_date: date = None
    budget_level: str = "moderate"
    pace: str = "moderate"
    interests: list[str] = field(default_factory=list)
    accessibility_needs: list[str] = field(default_factory=list)
    dietary_restrictions: list[str] = field(default_factory=list)
    transport_preferences: list[TransportMode] = field(default_factory=list)
    base_location: Coordinates | None = None
    base_address: str | None = None
    city: str | None = None
    country: str | None = None
    tags: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.start_date is None:
            self.start_date = date.today()
        if self.end_date is None:
            self.end_date = self.start_date


@dataclass
class UpdateItineraryRequest:
    title: str | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget_level: str | None = None
    pace: str | None = None
    interests: list[str] | None = None
    accessibility_needs: list[str] | None = None
    dietary_restrictions: list[str] | None = None
    transport_preferences: list[TransportMode] | None = None
    base_location: Coordinates | None = None
    base_address: str | None = None
    city: str | None = None
    country: str | None = None
    tags: list[str] | None = None
    status: ItineraryStatus | None = None


@dataclass
class AddItineraryDayRequest:
    day_date: date
    title: str | None = None
    notes: str | None = None
    start_time: time = time(9, 0)
    end_time: time = time(22, 0)
    base_location: Coordinates | None = None
    base_address: str | None = None


@dataclass
class UpdateItineraryDayRequest:
    title: str | None = None
    notes: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    base_location: Coordinates | None = None
    base_address: str | None = None


@dataclass
class AddItineraryItemRequest:
    type: ItineraryItemType = ItineraryItemType.POI
    poi_id: UUID | None = None
    title: str = ""
    description: str | None = None
    coordinates: Coordinates | None = None
    address: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    duration_minutes: int = 0
    transport_mode: TransportMode | None = None
    transit_details: dict[str, Any] = field(default_factory=dict)
    from_location: Coordinates | None = None
    to_location: Coordinates | None = None
    estimated_cost: float = 0.0
    currency: str = "USD"
    notes: str | None = None
    is_flexible: bool = True
    is_required: bool = False


@dataclass
class UpdateItineraryItemRequest:
    type: ItineraryItemType | None = None
    poi_id: UUID | None = None
    title: str | None = None
    description: str | None = None
    coordinates: Coordinates | None = None
    address: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    duration_minutes: int | None = None
    transport_mode: TransportMode | None = None
    transit_details: dict[str, Any] | None = None
    from_location: Coordinates | None = None
    to_location: Coordinates | None = None
    estimated_cost: float | None = None
    currency: str | None = None
    notes: str | None = None
    is_flexible: bool | None = None
    is_required: bool | None = None


@dataclass
class ReorderItineraryItemsRequest:
    item_ids: list[UUID]


@dataclass
class ReorderItineraryDaysRequest:
    day_ids: list[UUID]


@dataclass
class AddCollaboratorRequest:
    user_id: UUID


@dataclass
class PublishItineraryRequest:
    share_token: str


@dataclass
class GenerateItineraryByAIRequest:
    user_id: UUID
    prompt: str
    model: str
    tokens: int
    title: str
    start_date: date
    end_date: date
    budget_level: str = "moderate"
    pace: str = "moderate"
    interests: list[str] = field(default_factory=list)
    accessibility_needs: list[str] = field(default_factory=list)
    dietary_restrictions: list[str] = field(default_factory=list)
    transport_preferences: list[TransportMode] = field(default_factory=list)
    base_location: Coordinates | None = None
    base_address: str | None = None
    city: str | None = None
    country: str | None = None


# Media Requests
@dataclass
class UploadMediaRequest:
    filename: str
    original_filename: str
    type: MediaType
    mime_type: str
    size_bytes: int
    width: int = 0
    height: int = 0
    format: str = ""
    user_id: UUID | None = None
    poi_id: UUID | None = None
    conversation_id: UUID | None = None
    itinerary_id: UUID | None = None
    source: MediaSource = MediaSource.USER_UPLOAD
    source_url: str | None = None
    attribution: str | None = None
    license: str | None = None
    title: str | None = None
    description: str | None = None
    alt_text: str | None = None
    tags: list[str] = field(default_factory=list)
    coordinates: Coordinates | None = None
    address: str | None = None


@dataclass
class UpdateMediaRequest:
    title: str | None = None
    description: str | None = None
    alt_text: str | None = None
    tags: list[str] | None = None


# Feedback Requests
@dataclass
class CreateFeedbackRequest:
    user_id: UUID
    type: FeedbackType
    target_type: str
    target_id: UUID
    title: str | None = None
    content: str = ""
    rating: int | None = None
    categories: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    media_ids: list[UUID] = field(default_factory=list)
    location: dict[str, Any] | None = None
    is_public: bool = True
    is_anonymous: bool = False
    app_version: str | None = None
    platform: str | None = None
    device_info: dict[str, Any] | None = None


@dataclass
class UpdateFeedbackRequest:
    status: FeedbackStatus | None = None
    is_public: bool | None = None
    moderation_notes: str | None = None


@dataclass
class RespondFeedbackRequest:
    response: str


@dataclass
class MarkFeedbackHelpfulRequest:
    pass


# Search Requests
@dataclass
class SearchRequest:
    query: str
    coordinates: Coordinates | None = None
    radius_meters: float | None = None
    categories: list[POICategory] | None = None
    page: int = 1
    page_size: int = 20
    sort_by: str = "relevance"
    sort_order: str = "desc"


# Transit Requests
@dataclass
class TransitRouteRequest:
    origin: Coordinates
    destination: Coordinates
    origin_name: str = ""
    destination_name: str = ""
    departure_time: datetime | None = None
    arrival_time: datetime | None = None
    transport_modes: list[TransportMode] = field(default_factory=list)
    max_transfers: int = 3
    max_walking_distance: int = 1000
    wheelchair_accessible: bool = False


# Weather Requests
@dataclass
class WeatherForecastRequest:
    coordinates: Coordinates
    days: int = 7
    include_hourly: bool = True
    include_alerts: bool = True


# Recommendation Requests
@dataclass
class GetRecommendationsRequest:
    user_id: UUID
    type: str = "poi"  # poi, itinerary, route
    context: dict[str, Any] = field(default_factory=dict)
    limit: int = 10
    exclude_ids: list[UUID] = field(default_factory=list)


