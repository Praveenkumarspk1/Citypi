"""
Application Use Cases
"""
from .analytics_use_cases import (
    AnalyticsUseCases,
    GetEventsRequest,
    GetFunnelRequest,
    GetMetricsRequest,
    GetRetentionRequest,
    TrackEventRequest,
    TrackMetricRequest,
)
from .conversation_use_cases import (
    ConversationUseCases,
    CreateConversationRequest,
    SendMessageRequest,
    UpdateConversationRequest,
)
from .feedback_use_cases import (
    CreateFeedbackRequest,
    FeedbackUseCases,
    ModerateFeedbackRequest,
    UpdateFeedbackRequest,
)
from .itinerary_use_cases import (
    CreateDayRequest,
    CreateItemRequest,
    CreateItineraryRequest,
    ItineraryUseCases,
    OptimizeItineraryRequest,
    UpdateItineraryRequest,
)
from .media_use_cases import MediaUseCases, UpdateMediaRequest, UploadMediaRequest
from .poi_use_cases import CreatePOIRequest, POIUseCases, SearchPOIsRequest, UpdatePOIRequest
from .transit_use_cases import (
    GetRealtimeRequest,
    GetRoutesRequest,
    GetScheduleRequest,
    GetStopsRequest,
    TransitUseCases,
)
from .user_use_cases import CreateUserRequest, SearchUsersRequest, UpdateUserRequest, UserUseCases
from .weather_use_cases import GetHistoricalWeatherRequest, GetWeatherRequest, WeatherUseCases

__all__ = [
    "POIUseCases",
    "CreatePOIRequest",
    "UpdatePOIRequest",
    "SearchPOIsRequest",
    "UserUseCases",
    "CreateUserRequest",
    "UpdateUserRequest",
    "SearchUsersRequest",
    "ConversationUseCases",
    "CreateConversationRequest",
    "SendMessageRequest",
    "UpdateConversationRequest",
    "ItineraryUseCases",
    "CreateItineraryRequest",
    "UpdateItineraryRequest",
    "CreateDayRequest",
    "CreateItemRequest",
    "OptimizeItineraryRequest",
    "TransitUseCases",
    "GetRoutesRequest",
    "GetStopsRequest",
    "GetScheduleRequest",
    "GetRealtimeRequest",
    "WeatherUseCases",
    "GetWeatherRequest",
    "GetHistoricalWeatherRequest",
    "MediaUseCases",
    "UploadMediaRequest",
    "UpdateMediaRequest",
    "FeedbackUseCases",
    "CreateFeedbackRequest",
    "UpdateFeedbackRequest",
    "ModerateFeedbackRequest",
    "AnalyticsUseCases",
    "TrackEventRequest",
    "TrackMetricRequest",
    "GetEventsRequest",
    "GetMetricsRequest",
    "GetFunnelRequest",
    "GetRetentionRequest",
]
