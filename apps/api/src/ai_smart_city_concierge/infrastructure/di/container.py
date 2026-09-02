"""
Dependency Injection Container
"""
from collections.abc import Callable
from functools import lru_cache
from typing import Any

from ...application.commands.user_commands import UserCommandHandler
from ...application.commands.itinerary_commands import ItineraryCommandHandler
from ...application.commands.conversation_commands import ConversationCommandHandler
from ...application.commands.poi_commands import POICommandHandler
from ...application.events.event_handlers import EventHandlers
from ...application.ports.event_publisher import EventPublisher
from ...application.ports.external_services import (
    AuthServicePort,
    CacheServicePort,
    EmbeddingServicePort,
    GeocodingServicePort,
    LLMServicePort,
    MessageQueuePort,
    MetricsServicePort,
    NotificationServicePort,
    PlacesServicePort,
    RateLimiterPort,
    RecommendationEnginePort,
    RoutingServicePort,
    SpeechToTextServicePort,
    StorageServicePort,
    TracingServicePort,
    TransitServicePort,
    VectorDBServicePort,
    VisionAIServicePort,
    WeatherServicePort,
)
from ...application.ports.repositories import (
    AnalyticsRepositoryPort,
    ConversationRepositoryPort,
    FeedbackRepositoryPort,
    ItineraryRepositoryPort,
    MediaRepositoryPort,
    POIRepositoryPort,
    TransitRepositoryPort,
    UserRepositoryPort,
    WeatherRepositoryPort,
)
from ...application.queries.user_queries import UserQueryHandler
from ...application.queries.itinerary_queries import ItineraryQueryHandler
from ...application.queries.conversation_queries import ConversationQueryHandler
from ...application.queries.poi_queries import POIQueryHandler
from ...application.use_cases import (
    AnalyticsUseCases,
    ConversationUseCases,
    FeedbackUseCases,
    ItineraryUseCases,
    MediaUseCases,
    POIUseCases,
    TransitUseCases,
    UserUseCases,
    WeatherUseCases,
)
from ...application.services import (
    ConversationService,
    ItineraryService,
    MediaApplicationService,
    POIApplicationService,
    TransitApplicationService,
    UserService,
    WeatherApplicationService,
)
from ...domain.services import (
    ItineraryOptimizationService,
    POIService,
    RecommendationService,
    RoutingService,
    TransitService,
    WeatherService,
)
from ..config.settings import Settings
from ..external.adapters import (
    BGEEmbeddingAdapter,
    CLIPAdapter,
    FasterWhisperAdapter,
    FCMNotificationAdapter,
    GooglePlacesAdapter,
    GTFSRealtimeAdapter,
    JaegerTracingAdapter,
    JWTAuthAdapter,
    LightFMAdapter,
    NominatimGeocodingAdapter,
    OpenAILLMAdapter,
    OpenWeatherMapAdapter,
    OSRMAdapter,
    PrometheusMetricsAdapter,
    QdrantVectorDBAdapter,
    RedisCacheAdapter,
    RedisMessageQueueAdapter,
    RedisRateLimiterAdapter,
    S3StorageAdapter,
)
from ..external.adapters.event_publisher_adapter import LocalEventBusAdapter
from ..messaging.local_event_bus import local_event_bus
from ..persistence.sqlalchemy.repositories import (
    SQLAlchemyAnalyticsRepository,
    SQLAlchemyConversationRepository,
    SQLAlchemyFeedbackRepository,
    SQLAlchemyItineraryRepository,
    SQLAlchemyMediaRepository,
    SQLAlchemyPOIRepository,
    SQLAlchemyTransitRepository,
    SQLAlchemyUserRepository,
    SQLAlchemyWeatherRepository,
)


class Container:
    """Dependency injection container"""

    def __init__(self):
        self._services: dict[str, Any] = {}
        self._factories: dict[str, Callable] = {}
        self._singletons: dict[str, Any] = {}
        self._settings: Settings | None = None

    def configure(self, settings: Settings) -> None:
        """Configure container with settings"""
        self._settings = settings
        self._register_core_services()
        self._register_repositories()
        self._register_external_services()
        self._register_domain_services()
        self._register_use_cases()

    def _register_core_services(self) -> None:
        """Register core services"""
        self._factories["settings"] = lambda: self._settings

        # Event Publisher
        self._factories[EventPublisher] = lambda: LocalEventBusAdapter(local_event_bus)

    def _register_repositories(self) -> None:
        """Register repository implementations"""
        # POI Repository
        self._factories[POIRepositoryPort] = lambda: SQLAlchemyPOIRepository(
            session_factory=self._get_session_factory(),
        )

        # User Repository
        self._factories[UserRepositoryPort] = lambda: SQLAlchemyUserRepository(
            session_factory=self._get_session_factory(),
        )

        # Conversation Repository
        self._factories[ConversationRepositoryPort] = lambda: SQLAlchemyConversationRepository(
            session_factory=self._get_session_factory(),
        )

        # Itinerary Repository
        self._factories[ItineraryRepositoryPort] = lambda: SQLAlchemyItineraryRepository(
            session_factory=self._get_session_factory(),
        )

        # Transit Repository
        self._factories[TransitRepositoryPort] = lambda: SQLAlchemyTransitRepository(
            session_factory=self._get_session_factory(),
        )

        # Weather Repository
        self._factories[WeatherRepositoryPort] = lambda: SQLAlchemyWeatherRepository(
            session_factory=self._get_session_factory(),
        )

        # Media Repository
        self._factories[MediaRepositoryPort] = lambda: SQLAlchemyMediaRepository(
            session_factory=self._get_session_factory(),
        )

        # Feedback Repository
        self._factories[FeedbackRepositoryPort] = lambda: SQLAlchemyFeedbackRepository(
            session_factory=self._get_session_factory(),
        )

        # Analytics Repository
        self._factories[AnalyticsRepositoryPort] = lambda: SQLAlchemyAnalyticsRepository(
            session_factory=self._get_session_factory(),
        )

    def _register_external_services(self) -> None:
        """Register external service adapters"""
        settings = self._settings

        # Geocoding
        self._factories[GeocodingServicePort] = lambda: NominatimGeocodingAdapter(
            base_url=settings.geocoding.nominatim_url,
            user_agent=settings.geocoding.user_agent,
        )

        # Routing
        self._factories[RoutingServicePort] = lambda: OSRMAdapter(
            base_url=settings.routing.osrm_url,
        )

        # Places
        self._factories[PlacesServicePort] = lambda: GooglePlacesAdapter(
            api_key=settings.places.google_api_key,
        )

        # Transit
        self._factories[TransitServicePort] = lambda: GTFSRealtimeAdapter(
            feed_urls=settings.transit.gtfs_feed_urls,
        )

        # Weather
        self._factories[WeatherServicePort] = lambda: OpenWeatherMapAdapter(
            api_key=settings.weather.openweather_api_key,
        )

        # Vector DB
        self._factories[VectorDBServicePort] = lambda: QdrantVectorDBAdapter(
            host=settings.vector_db.qdrant_host,
            port=settings.vector_db.qdrant_port,
            api_key=settings.vector_db.qdrant_api_key,
        )

        # Embedding
        self._factories[EmbeddingServicePort] = lambda: BGEEmbeddingAdapter(
            model_name=settings.embedding.model_name,
            device=settings.embedding.device,
        )

        # LLM
        self._factories[LLMServicePort] = lambda: OpenAILLMAdapter(
            api_key=settings.llm.openai_api_key,
            model=settings.llm.model,
        )

        # Speech to Text
        self._factories[SpeechToTextServicePort] = lambda: FasterWhisperAdapter(
            model_size=settings.speech.whisper_model_size,
            device=settings.speech.device,
            compute_type=settings.speech.compute_type,
        )

        # Vision AI
        self._factories[VisionAIServicePort] = lambda: CLIPAdapter(
            model_name=settings.vision.clip_model_name,
            device=settings.vision.device,
        )

        # Recommendation
        self._factories[RecommendationEnginePort] = lambda: LightFMAdapter(
            no_components=settings.recommendation.lightfm_components,
            learning_rate=settings.recommendation.lightfm_learning_rate,
            loss=settings.recommendation.lightfm_loss,
        )

        # Cache
        self._factories[CacheServicePort] = lambda: RedisCacheAdapter(
            host=settings.cache.redis_host,
            port=settings.cache.redis_port,
            db=settings.cache.redis_db,
            password=settings.cache.redis_password,
        )

        # Message Queue
        self._factories[MessageQueuePort] = lambda: RedisMessageQueueAdapter(
            host=settings.message_queue.redis_host,
            port=settings.message_queue.redis_port,
            db=settings.message_queue.redis_db,
            password=settings.message_queue.redis_password,
        )

        # Storage
        self._factories[StorageServicePort] = lambda: S3StorageAdapter(
            access_key=settings.storage.s3_access_key,
            secret_key=settings.storage.s3_secret_key,
            region=settings.storage.s3_region,
            endpoint_url=settings.storage.s3_endpoint_url,
        )

        # Notification
        self._factories[NotificationServicePort] = lambda: FCMNotificationAdapter(
            credentials_path=settings.notification.fcm_credentials_path,
            project_id=settings.notification.fcm_project_id,
        )

        # Auth
        self._factories[AuthServicePort] = lambda: JWTAuthAdapter(
            secret_key=settings.auth.jwt_secret_key,
            algorithm=settings.auth.jwt_algorithm,
            issuer=settings.auth.jwt_issuer,
            audience=settings.auth.jwt_audience,
        )

        # Rate Limiter
        self._factories[RateLimiterPort] = lambda: RedisRateLimiterAdapter(
            host=settings.rate_limiter.redis_host,
            port=settings.rate_limiter.redis_port,
            db=settings.rate_limiter.redis_db,
            password=settings.rate_limiter.redis_password,
        )

        # Metrics
        self._factories[MetricsServicePort] = lambda: PrometheusMetricsAdapter(
            port=settings.metrics.prometheus_port,
            path=settings.metrics.prometheus_path,
        )

        # Tracing
        self._factories[TracingServicePort] = lambda: JaegerTracingAdapter(
            service_name=settings.tracing.service_name,
            agent_host=settings.tracing.jaeger_agent_host,
            agent_port=settings.tracing.jaeger_agent_port,
            collector_endpoint=settings.tracing.jaeger_collector_endpoint,
        )

    def _register_domain_services(self) -> None:
        """Register domain services"""
        self._factories[RoutingService] = lambda: RoutingService(
            routing_service=self.get(RoutingServicePort),
        )

        self._factories[RecommendationService] = lambda: RecommendationService(
            recommendation_engine=self.get(RecommendationEnginePort),
        )

        self._factories[WeatherService] = lambda: WeatherService(
            weather_service=self.get(WeatherServicePort),
        )

        self._factories[TransitService] = lambda: TransitService(
            transit_service=self.get(TransitServicePort),
        )

        self._factories[POIService] = lambda: POIService(
            poi_repository=self.get(POIRepositoryPort),
            embedding_service=self.get(EmbeddingServicePort),
            vector_db=self.get(VectorDBServicePort),
        )

        self._factories[ItineraryOptimizationService] = lambda: ItineraryOptimizationService(
            routing_service=self.get(RoutingServicePort),
            transit_service=self.get(TransitServicePort),
            weather_service=self.get(WeatherServicePort),
            poi_service=self.get(POIService),
        )

    def _register_use_cases(self) -> None:
        """Register use cases"""
        self._factories[POIUseCases] = lambda: POIUseCases(
            poi_repository=self.get(POIRepositoryPort),
            poi_service=self.get(POIService),
            embedding_service=self.get(EmbeddingServicePort),
            vector_db=self.get(VectorDBServicePort),
        )

        self._factories[UserUseCases] = lambda: UserUseCases(
            user_repository=self.get(UserRepositoryPort),
            auth_service=self.get(AuthServicePort),
            notification_service=self.get(NotificationServicePort),
        )

        # Register User Command and Query Handlers
        self._factories[UserCommandHandler] = lambda: UserCommandHandler(
            user_repository=self.get(UserRepositoryPort),
            event_publisher=self.get(EventPublisher),
        )

        self._factories[UserQueryHandler] = lambda: UserQueryHandler(
            user_repository=self.get(UserRepositoryPort),
        )

        # Register other Command Handlers
        self._factories[ItineraryCommandHandler] = lambda: ItineraryCommandHandler(
            itinerary_repository=self.get(ItineraryRepositoryPort),
            event_publisher=self.get(EventPublisher),
        )

        self._factories[ConversationCommandHandler] = lambda: ConversationCommandHandler(
            conversation_repository=self.get(ConversationRepositoryPort),
            event_publisher=self.get(EventPublisher),
        )

        self._factories[POICommandHandler] = lambda: POICommandHandler(
            poi_repository=self.get(POIRepositoryPort),
            event_publisher=self.get(EventPublisher),
        )

        # Register other Query Handlers
        self._factories[ItineraryQueryHandler] = lambda: ItineraryQueryHandler(
            itinerary_repository=self.get(ItineraryRepositoryPort),
        )

        self._factories[ConversationQueryHandler] = lambda: ConversationQueryHandler(
            conversation_repository=self.get(ConversationRepositoryPort),
        )

        self._factories[POIQueryHandler] = lambda: POIQueryHandler(
            poi_repository=self.get(POIRepositoryPort),
        )

        self._factories[ConversationUseCases] = lambda: ConversationUseCases(
            conversation_repository=self.get(ConversationRepositoryPort),
            llm_service=self.get(LLMServicePort),
            embedding_service=self.get(EmbeddingServicePort),
            vector_db=self.get(VectorDBServicePort),
        )

        self._factories[ItineraryUseCases] = lambda: ItineraryUseCases(
            itinerary_repository=self.get(ItineraryRepositoryPort),
            itinerary_optimization_service=self.get(ItineraryOptimizationService),
            poi_service=self.get(POIService),
            transit_service=self.get(TransitService),
            weather_service=self.get(WeatherService),
        )

        self._factories[TransitUseCases] = lambda: TransitUseCases(
            transit_repository=self.get(TransitRepositoryPort),
            transit_service=self.get(TransitService),
            routing_service=self.get(RoutingService),
        )

        self._factories[WeatherUseCases] = lambda: WeatherUseCases(
            weather_repository=self.get(WeatherRepositoryPort),
            weather_service=self.get(WeatherService),
        )

        self._factories[MediaUseCases] = lambda: MediaUseCases(
            media_repository=self.get(MediaRepositoryPort),
            storage_service=self.get(StorageServicePort),
            vision_service=self.get(VisionAIServicePort),
        )

        self._factories[FeedbackUseCases] = lambda: FeedbackUseCases(
            feedback_repository=self.get(FeedbackRepositoryPort),
            analytics_service=self.get(AnalyticsUseCases),
        )

        self._factories[AnalyticsUseCases] = lambda: AnalyticsUseCases(
            analytics_repository=self.get(AnalyticsRepositoryPort),
            metrics_service=self.get(MetricsServicePort),
        )

    def _register_application_services(self) -> None:
        """Register application services"""
        # User Service
        self._factories[UserService] = lambda: UserService(
            user_repository=self.get(UserRepositoryPort),
            cache=self.get(CacheServicePort),
            auth=self.get(AuthServicePort),
            notification=self.get(NotificationServicePort),
            event_bus=self.get(EventPublisher),
        )

        # Conversation Service
        self._factories[ConversationService] = lambda: ConversationService(
            conversation_repository=self.get(ConversationRepositoryPort),
            conversation_manager=self._get_conversation_manager(),
            llm_service=self.get(LLMServicePort),
            embedding_service=self.get(EmbeddingServicePort),
            vector_db=self.get(VectorDBServicePort),
            cache=self.get(CacheServicePort),
            event_bus=self.get(EventPublisher),
        )

        # Itinerary Service
        self._factories[ItineraryService] = lambda: ItineraryService(
            itinerary_repository=self.get(ItineraryRepositoryPort),
            optimization_service=self.get(ItineraryOptimizationService),
            llm_service=self.get(LLMServicePort),
            embedding_service=self.get(EmbeddingServicePort),
            vector_db=self.get(VectorDBServicePort),
            cache=self.get(CacheServicePort),
            event_bus=self.get(EventPublisher),
        )

        # POI Service
        self._factories[POIApplicationService] = lambda: POIApplicationService(
            poi_repository=self.get(POIRepositoryPort),
            poi_service=self.get(POIService),
            embedding_service=self.get(EmbeddingServicePort),
            vector_db=self.get(VectorDBServicePort),
            cache=self.get(CacheServicePort),
            event_bus=self.get(EventPublisher),
        )

        # Transit Service
        self._factories[TransitApplicationService] = lambda: TransitApplicationService(
            transit_repository=self.get(TransitRepositoryPort),
            transit_service=self.get(TransitService),
            external_transit=self.get(TransitServicePort),
            cache=self.get(CacheServicePort),
            event_bus=self.get(EventPublisher),
        )

        # Weather Service
        self._factories[WeatherApplicationService] = lambda: WeatherApplicationService(
            weather_repository=self.get(WeatherRepositoryPort),
            weather_service=self.get(WeatherService),
            external_weather=self.get(WeatherServicePort),
            cache=self.get(CacheServicePort),
            event_bus=self.get(EventPublisher),
        )

        # Media Service
        self._factories[MediaApplicationService] = lambda: MediaApplicationService(
            media_repository=self.get(MediaRepositoryPort),
            storage=self.get(StorageServicePort),
            speech_service=self.get(SpeechToTextServicePort),
            vision_service=self.get(VisionAIServicePort),
            cache=self.get(CacheServicePort),
            event_bus=self.get(EventPublisher),
        )

        # Event Handlers
        self._factories[EventHandlers] = lambda: EventHandlers(
            user_repository=self.get(UserRepositoryPort),
            conversation_repository=self.get(ConversationRepositoryPort),
            itinerary_repository=self.get(ItineraryRepositoryPort),
            poi_repository=self.get(POIRepositoryPort),
            transit_repository=self.get(TransitRepositoryPort),
            weather_repository=self.get(WeatherRepositoryPort),
            media_repository=self.get(MediaRepositoryPort),
            feedback_repository=self.get(FeedbackRepositoryPort),
            analytics_repository=self.get(AnalyticsRepositoryPort),
            embedding_service=self.get(EmbeddingServicePort),
            vector_db=self.get(VectorDBServicePort),
            notification_service=self.get(NotificationServicePort),
            event_publisher=self.get(EventPublisher),
        )

    def _get_conversation_manager(self):
        """Get conversation manager domain service"""
        from ...domain.services.conversation_manager import ConversationManager
        return ConversationManager(
            llm_service=self.get(LLMServicePort),
            embedding_service=self.get(EmbeddingServicePort),
            vector_db=self.get(VectorDBServicePort),
        )

    def configure(self, settings: Settings) -> None:
        """Configure container with settings"""
        self._settings = settings
        self._register_core_services()
        self._register_repositories()
        self._register_external_services()
        self._register_domain_services()
        self._register_application_services()
        self._register_use_cases()
        """Get database session factory"""
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

        engine = create_async_engine(
            self._settings.database.url,
            echo=self._settings.database.echo,
            pool_size=self._settings.database.pool_size,
            max_overflow=self._settings.database.max_overflow,
        )

        return async_sessionmaker(engine, expire_on_commit=False)

    def register(self, interface: type, factory: Callable) -> None:
        """Register a service factory"""
        self._factories[interface] = factory

    def register_singleton(self, interface: type, instance: Any) -> None:
        """Register a singleton instance"""
        self._singletons[interface] = instance

    def get(self, interface: type) -> Any:
        """Get service instance"""
        # Check singletons first
        if interface in self._singletons:
            return self._singletons[interface]

        # Check cached services
        key = str(interface)
        if key in self._services:
            return self._services[key]

        # Create from factory
        if interface in self._factories:
            instance = self._factories[interface]()
            self._services[key] = instance
            return instance

        # Try string key
        if key in self._factories:
            instance = self._factories[key]()
            self._services[key] = instance
            return instance

        raise KeyError(f"No registration found for {interface}")

    async def close(self) -> None:
        """Close all services"""
        for service in self._services.values():
            if hasattr(service, 'close'):
                await service.close()
        self._services.clear()


# Global container instance
_container: Container | None = None


def get_container() -> Container:
    """Get global container instance"""
    global _container
    if _container is None:
        _container = Container()
    return _container


def configure_container(settings: Settings) -> Container:
    """Configure and return global container"""
    global _container
    _container = Container()
    _container.configure(settings)
    return _container


@lru_cache
def get_settings() -> Settings:
    """Get cached settings"""
    from ..config.settings import get_settings as _get_settings
    return _get_settings()


# Convenience functions for common services
def get_poi_repository() -> POIRepositoryPort:
    return get_container().get(POIRepositoryPort)


def get_user_repository() -> UserRepositoryPort:
    return get_container().get(UserRepositoryPort)


def get_conversation_repository() -> ConversationRepositoryPort:
    return get_container().get(ConversationRepositoryPort)


def get_itinerary_repository() -> ItineraryRepositoryPort:
    return get_container().get(ItineraryRepositoryPort)


def get_transit_repository() -> TransitRepositoryPort:
    return get_container().get(TransitRepositoryPort)


def get_weather_repository() -> WeatherRepositoryPort:
    return get_container().get(WeatherRepositoryPort)


def get_media_repository() -> MediaRepositoryPort:
    return get_container().get(MediaRepositoryPort)


def get_feedback_repository() -> FeedbackRepositoryPort:
    return get_container().get(FeedbackRepositoryPort)


def get_analytics_repository() -> AnalyticsRepositoryPort:
    return get_container().get(AnalyticsRepositoryPort)


def get_geocoding_service() -> GeocodingServicePort:
    return get_container().get(GeocodingServicePort)


def get_routing_service() -> RoutingServicePort:
    return get_container().get(RoutingServicePort)


def get_places_service() -> PlacesServicePort:
    return get_container().get(PlacesServicePort)


def get_transit_service() -> TransitServicePort:
    return get_container().get(TransitServicePort)


def get_weather_service() -> WeatherServicePort:
    return get_container().get(WeatherServicePort)


def get_vector_db() -> VectorDBServicePort:
    return get_container().get(VectorDBServicePort)


def get_embedding_service() -> EmbeddingServicePort:
    return get_container().get(EmbeddingServicePort)


def get_llm_service() -> LLMServicePort:
    return get_container().get(LLMServicePort)


def get_speech_service() -> SpeechToTextServicePort:
    return get_container().get(SpeechToTextServicePort)


def get_vision_service() -> VisionAIServicePort:
    return get_container().get(VisionAIServicePort)


def get_recommendation_engine() -> RecommendationEnginePort:
    return get_container().get(RecommendationEnginePort)


def get_cache() -> CacheServicePort:
    return get_container().get(CacheServicePort)


def get_message_queue() -> MessageQueuePort:
    return get_container().get(MessageQueuePort)


def get_storage() -> StorageServicePort:
    return get_container().get(StorageServicePort)


def get_notification_service() -> NotificationServicePort:
    return get_container().get(NotificationServicePort)


def get_auth_service() -> AuthServicePort:
    return get_container().get(AuthServicePort)


def get_rate_limiter() -> RateLimiterPort:
    return get_container().get(RateLimiterPort)


def get_metrics() -> MetricsServicePort:
    return get_container().get(MetricsServicePort)


def get_tracing() -> TracingServicePort:
    return get_container().get(TracingServicePort)


def get_poi_use_cases() -> POIUseCases:
    return get_container().get(POIUseCases)


def get_user_use_cases() -> UserUseCases:
    return get_container().get(UserUseCases)


def get_conversation_use_cases() -> ConversationUseCases:
    return get_container().get(ConversationUseCases)


def get_itinerary_use_cases() -> ItineraryUseCases:
    return get_container().get(ItineraryUseCases)


def get_transit_use_cases() -> TransitUseCases:
    return get_container().get(TransitUseCases)


def get_weather_use_cases() -> WeatherUseCases:
    return get_container().get(WeatherUseCases)


def get_media_use_cases() -> MediaUseCases:
    return get_container().get(MediaUseCases)


def get_feedback_use_cases() -> FeedbackUseCases:
    return get_container().get(FeedbackUseCases)


def get_analytics_use_cases() -> AnalyticsUseCases:
    return get_container().get(AnalyticsUseCases)


# Application Services
def get_user_service() -> UserService:
    return get_container().get(UserService)


def get_conversation_service() -> ConversationService:
    return get_container().get(ConversationService)


def get_itinerary_service() -> ItineraryService:
    return get_container().get(ItineraryService)


def get_poi_application_service() -> POIApplicationService:
    return get_container().get(POIApplicationService)


def get_transit_application_service() -> TransitApplicationService:
    return get_container().get(TransitApplicationService)


def get_weather_application_service() -> WeatherApplicationService:
    return get_container().get(WeatherApplicationService)


def get_media_application_service() -> MediaApplicationService:
    return get_container().get(MediaApplicationService)


# Command Handlers
def get_itinerary_command_handler() -> ItineraryCommandHandler:
    return get_container().get(ItineraryCommandHandler)


def get_conversation_command_handler() -> ConversationCommandHandler:
    return get_container().get(ConversationCommandHandler)


def get_poi_command_handler() -> POICommandHandler:
    return get_container().get(POICommandHandler)


# Query Handlers
def get_itinerary_query_handler() -> ItineraryQueryHandler:
    return get_container().get(ItineraryQueryHandler)


def get_conversation_query_handler() -> ConversationQueryHandler:
    return get_container().get(ConversationQueryHandler)


def get_poi_query_handler() -> POIQueryHandler:
    return get_container().get(POIQueryHandler)


# Event Handlers
def get_event_handlers() -> EventHandlers:
    return get_container().get(EventHandlers)
