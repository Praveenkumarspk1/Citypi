"""
Application Ports Package
"""
from .repositories import (
    UserRepositoryPort,
    ConversationRepositoryPort,
    ItineraryRepositoryPort,
    POIRepositoryPort,
    TransitRepositoryPort,
    WeatherRepositoryPort,
    MediaRepositoryPort,
    FeedbackRepositoryPort,
    AnalyticsRepositoryPort,
)
from .external_services import (
    GeocodingServicePort,
    RoutingServicePort,
    PlacesServicePort,
    TransitDataServicePort,
    RealtimeTransitServicePort,
    WeatherServicePort,
    VectorDatabasePort,
    EmbeddingServicePort,
    LLMServicePort,
    SpeechToTextServicePort,
    VisionAIServicePort,
    RecommendationEnginePort,
    CacheServicePort,
    MessageQueuePort,
    StorageServicePort,
    NotificationServicePort,
    AuthServicePort,
    RateLimiterPort,
    MetricsServicePort,
    TracingServicePort,
)
from .event_publisher import EventPublisher

# Aliases for backward compatibility
CachePort = CacheServicePort
EmbeddingPort = EmbeddingServicePort
EventBusPort = EventPublisher
GeocodingPort = GeocodingServicePort
LLMPort = LLMServicePort
RoutingPort = RoutingServicePort
StoragePort = StorageServicePort
STTPort = SpeechToTextServicePort
TransitPort = TransitDataServicePort
VectorSearchPort = VectorDatabasePort
VisionPort = VisionAIServicePort
WeatherPort = WeatherServicePort

__all__ = [
    # Repository ports
    "UserRepositoryPort",
    "ConversationRepositoryPort",
    "ItineraryRepositoryPort",
    "POIRepositoryPort",
    "TransitRepositoryPort",
    "WeatherRepositoryPort",
    "MediaRepositoryPort",
    "FeedbackRepositoryPort",
    "AnalyticsRepositoryPort",
    # External service ports
    "GeocodingServicePort",
    "RoutingServicePort",
    "PlacesServicePort",
    "TransitDataServicePort",
    "RealtimeTransitServicePort",
    "WeatherServicePort",
    "VectorDatabasePort",
    "EmbeddingServicePort",
    "LLMServicePort",
    "SpeechToTextServicePort",
    "VisionAIServicePort",
    "RecommendationEnginePort",
    "CacheServicePort",
    "MessageQueuePort",
    "StorageServicePort",
    "NotificationServicePort",
    "AuthServicePort",
    "RateLimiterPort",
    "MetricsServicePort",
    "TracingServicePort",
    # Event publisher
    "EventPublisher",
    # Aliases
    "CachePort",
    "EmbeddingPort",
    "EventBusPort",
    "GeocodingPort",
    "LLMPort",
    "RoutingPort",
    "StoragePort",
    "STTPort",
    "TransitPort",
    "VectorSearchPort",
    "VisionPort",
    "WeatherPort",
]