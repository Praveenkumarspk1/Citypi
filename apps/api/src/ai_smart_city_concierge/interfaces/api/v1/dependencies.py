"""
Dependency Injection Container
Wires up all application ports to their infrastructure implementations
"""
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ....application.ports import (
    CachePort,
    EmbeddingPort,
    EventBusPort,
    GeocodingPort,
    LLMPort,
    RoutingPort,
    StoragePort,
    STTPort,
    TransitPort,
    VectorSearchPort,
    VisionPort,
    WeatherPort,
)
from ....application.use_cases import (
    ConversationUseCases,
    ItineraryUseCases,
    MediaUseCases,
    POIUseCases,
    TransitUseCases,
    UserUseCases,
    WeatherUseCases,
)
from ....domain.repositories import (
    ConversationRepository,
    ItineraryRepository,
    POIRepository,
    TransitRepository,
    UserRepository,
    VectorRepository,
    WeatherRepository,
)
from ....infrastructure.auth.jwt_auth import JWTAuth
from ....infrastructure.config.settings import get_settings
from ....infrastructure.external_apis.bge_m3_client import BGEM3Client
from ....infrastructure.external_apis.clip_client import CLIPClient
from ....infrastructure.external_apis.gemini_client import GeminiClient
from ....infrastructure.external_apis.gtfs_client import GTFSClient
from ....infrastructure.external_apis.nominatim_client import NominatimClient
from ....infrastructure.external_apis.open_charge_map_client import OpenChargeMapClient
from ....infrastructure.external_apis.open_meteo_client import OpenMeteoClient
from ....infrastructure.external_apis.overpass_client import OverpassClient
from ....infrastructure.external_apis.whisper_client import WhisperClient
from ....infrastructure.messaging.local_event_bus import LocalEventBus
from ....infrastructure.persistence.redis.cache_repository import RedisCacheRepository
from ....infrastructure.persistence.redis.session_store import RedisSessionStore
from ....infrastructure.persistence.sqlalchemy.repositories import (
    SQLAlchemyConversationRepository,
    SQLAlchemyItineraryRepository,
    SQLAlchemyPOIRepository,
    SQLAlchemyTransitRepository,
    SQLAlchemyUserRepository,
    SQLAlchemyWeatherRepository,
)
from ....infrastructure.persistence.sqlalchemy.session import get_db_session
from ....infrastructure.storage.local_storage import LocalStorage
from ....infrastructure.vector_stores.chromadb_adapter import ChromaDBAdapter

# ==========================================
# Infrastructure Adapters (Singletons)
# ==========================================

@lru_cache
def get_settings_instance():
    """Get cached settings instance"""
    return get_settings()


@lru_cache
def get_gemini_client() -> LLMPort:
    """Get Gemini LLM client"""
    settings = get_settings_instance()
    return GeminiClient(
        api_key=settings.ai.gemini_api_key,
        model=settings.ai.gemini_model,
        temperature=settings.ai.gemini_temperature,
        max_tokens=settings.ai.gemini_max_tokens,
        top_p=settings.ai.gemini_top_p,
        top_k=settings.ai.gemini_top_k,
    )


@lru_cache
def get_embedding_client() -> EmbeddingPort:
    """Get BGE-M3 embedding client"""
    settings = get_settings_instance()
    return BGEM3Client(
        model_name=settings.ai.embedding_model,
        device=settings.ai.embedding_device,
        batch_size=settings.ai.embedding_batch_size,
        normalize=settings.ai.embedding_normalize,
    )


@lru_cache
def get_whisper_client() -> STTPort:
    """Get Whisper STT client"""
    settings = get_settings_instance()
    return WhisperClient(
        model_size=settings.ai.whisper_model,
        device=settings.ai.whisper_device,
        compute_type=settings.ai.whisper_compute_type,
    )


@lru_cache
def get_clip_client() -> VisionPort:
    """Get CLIP vision client"""
    settings = get_settings_instance()
    return CLIPClient(
        model_name=settings.ai.clip_model,
        device=settings.ai.clip_device,
    )


@lru_cache
def get_vector_store() -> VectorSearchPort:
    """Get ChromaDB vector store"""
    settings = get_settings_instance()
    return ChromaDBAdapter(
        host=settings.chromadb.host,
        port=settings.chromadb.port,
        ssl=settings.chromadb.ssl,
        auth_token=settings.chromadb.auth_token,
    )


@lru_cache
def get_overpass_client() -> GeocodingPort:
    """Get Overpass API client for POI search"""
    settings = get_settings_instance()
    return OverpassClient(
        base_url=settings.external.overpass_url,
        rate_limit=settings.external.overpass_rate_limit,
    )


@lru_cache
def get_nominatim_client() -> GeocodingPort:
    """Get Nominatim geocoding client"""
    settings = get_settings_instance()
    return NominatimClient(
        base_url=settings.external.nominatim_url,
        rate_limit=settings.external.nominatim_rate_limit,
        user_agent="concierge/1.0",
    )


@lru_cache
def get_open_meteo_client() -> WeatherPort:
    """Get Open-Meteo weather client"""
    settings = get_settings_instance()
    return OpenMeteoClient(
        base_url=settings.external.open_meteo_url,
        rate_limit=settings.external.open_meteo_rate_limit,
    )


@lru_cache
def get_gtfs_client() -> TransitPort:
    """Get GTFS transit client"""
    settings = get_settings()
    return GTFSClient(
        static_url=settings.external.gtfs_static_url,
        realtime_url=settings.external.gtfs_realtime_url,
        api_key=settings.external.gtfs_api_key,
        rate_limit=settings.external.gtfs_rate_limit,
    )


@lru_cache
def get_open_charge_map_client() -> OpenChargeMapClient:
    """Get OpenChargeMap EV charging client"""
    settings = get_settings()
    return OpenChargeMapClient(
        api_key=settings.external.openchargemap_api_key,
        base_url=settings.external.openchargemap_url,
    )


@lru_cache
def get_event_bus() -> EventBusPort:
    """Get local event bus (Redis Streams in production)"""
    return LocalEventBus()


@lru_cache
def get_local_storage() -> StoragePort:
    """Get local file storage"""
    return LocalStorage(base_path="/app/storage")


# ==========================================
# Repository Dependencies
# ==========================================

async def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    """Get user repository"""
    return SQLAlchemyUserRepository(session)


async def get_conversation_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ConversationRepository:
    """Get conversation repository"""
    return SQLAlchemyConversationRepository(session)


async def get_poi_repository(
    session: AsyncSession = Depends(get_db_session),
) -> POIRepository:
    """Get POI repository"""
    return SQLAlchemyPOIRepository(session)


async def get_transit_repository(
    session: AsyncSession = Depends(get_db_session),
) -> TransitRepository:
    """Get transit repository"""
    return SQLAlchemyTransitRepository(session)


async def get_weather_repository(
    session: AsyncSession = Depends(get_db_session),
) -> WeatherRepository:
    """Get weather repository"""
    return SQLAlchemyWeatherRepository(session)


async def get_itinerary_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ItineraryRepository:
    """Get itinerary repository"""
    return SQLAlchemyItineraryRepository(session)


async def get_vector_repository(
    vector_store: VectorSearchPort = Depends(get_vector_store),
) -> VectorRepository:
    """Get vector repository"""
    from ....infrastructure.persistence.vector_stores.vector_repository import VectorRepositoryImpl
    return VectorRepositoryImpl(vector_store)


async def get_cache_repository() -> CachePort:
    """Get Redis cache repository"""
    return RedisCacheRepository()


async def get_session_store() -> CachePort:
    """Get Redis session store"""
    return RedisSessionStore()


# ==========================================
# Application Service Dependencies
# ==========================================

async def get_conversation_service(
    conversation_repo: ConversationRepository = Depends(get_conversation_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    vector_repo: VectorRepository = Depends(get_vector_repository),
    llm: LLMPort = Depends(get_gemini_client),
    embedding: EmbeddingPort = Depends(get_embedding_client),
    event_bus: EventBusPort = Depends(get_event_bus),
) -> ConversationService:
    """Get conversation service with all dependencies"""
    return ConversationService(
        conversation_repository=conversation_repo,
        user_repository=user_repo,
        vector_repository=vector_repo,
        llm=llm,
        embedding=embedding,
        event_bus=event_bus,
    )


async def get_itinerary_service(
    itinerary_repo: ItineraryRepository = Depends(get_itinerary_repository),
    poi_repo: POIRepository = Depends(get_poi_repository),
    transit_repo: TransitRepository = Depends(get_transit_repository),
    weather_repo: WeatherRepository = Depends(get_weather_repository),
    vector_repo: VectorRepository = Depends(get_vector_repository),
    llm: LLMPort = Depends(get_gemini_client),
    embedding: EmbeddingPort = Depends(get_embedding_client),
    event_bus: EventBusPort = Depends(get_event_bus),
) -> ItineraryService:
    """Get itinerary service with all dependencies"""
    return ItineraryService(
        itinerary_repository=itinerary_repo,
        poi_repository=poi_repo,
        transit_repository=transit_repo,
        weather_repository=weather_repo,
        vector_repository=vector_repo,
        llm=llm,
        embedding=embedding,
        event_bus=event_bus,
    )


async def get_poi_service(
    poi_repo: POIRepository = Depends(get_poi_repository),
    vector_repo: VectorRepository = Depends(get_vector_repository),
    embedding: EmbeddingPort = Depends(get_embedding_client),
    geocoding: GeocodingPort = Depends(get_nominatim_client),
    overpass: GeocodingPort = Depends(get_overpass_client),
    event_bus: EventBusPort = Depends(get_event_bus),
) -> POIService:
    """Get POI service with all dependencies"""
    return POIService(
        poi_repository=poi_repo,
        vector_repository=vector_repo,
        embedding=embedding,
        geocoding=geocoding,
        overpass=overpass,
        event_bus=event_bus,
    )


async def get_transit_service(
    transit_repo: TransitRepository = Depends(get_transit_repository),
    gtfs: TransitPort = Depends(get_gtfs_client),
    routing: RoutingPort = Depends(get_gtfs_client),  # GTFS client implements routing
    event_bus: EventBusPort = Depends(get_event_bus),
) -> TransitService:
    """Get transit service with all dependencies"""
    return TransitService(
        transit_repository=transit_repo,
        gtfs_client=gtfs,
        routing=routing,
        event_bus=event_bus,
    )


async def get_weather_service(
    weather_repo: WeatherRepository = Depends(get_weather_repository),
    open_meteo: WeatherPort = Depends(get_open_meteo_client),
    geocoding: GeocodingPort = Depends(get_nominatim_client),
    event_bus: EventBusPort = Depends(get_event_bus),
) -> WeatherService:
    """Get weather service with all dependencies"""
    return WeatherService(
        weather_repository=weather_repo,
        open_meteo=open_meteo,
        geocoding=geocoding,
        event_bus=event_bus,
    )


async def get_media_service(
    stt: STTPort = Depends(get_whisper_client),
    vision: VisionPort = Depends(get_clip_client),
    storage: StoragePort = Depends(get_local_storage),
    event_bus: EventBusPort = Depends(get_event_bus),
) -> MediaService:
    """Get media service with all dependencies"""
    return MediaService(
        stt=stt,
        vision=vision,
        storage=storage,
        event_bus=event_bus,
    )


async def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository),
    cache: CachePort = Depends(get_cache_repository),
    auth: JWTAuth = Depends(get_jwt_auth),
    event_bus: EventBusPort = Depends(get_event_bus),
) -> UserService:
    """Get user service with all dependencies"""
    return UserService(
        user_repository=user_repo,
        cache=cache,
        auth=auth,
        event_bus=event_bus,
    )


# ==========================================
# Auth Dependencies
# ==========================================

@lru_cache
def get_jwt_auth() -> JWTAuth:
    """Get JWT authentication handler"""
    settings = get_settings_instance()
    return JWTAuth(
        secret_key=settings.auth.secret_key,
        algorithm=settings.auth.algorithm,
        access_token_expire_minutes=settings.auth.access_token_expire_minutes,
        refresh_token_expire_days=settings.auth.refresh_token_expire_days,
    )


async def get_current_user(
    auth: JWTAuth = Depends(get_jwt_auth),
    session_store: CachePort = Depends(get_session_store),
    # token: str = Depends(oauth2_scheme),  # Will be implemented
) -> dict:
    """Get current authenticated user"""
    # TODO: Implement proper token extraction and validation
    # For now, return a mock user for development
    return {
        "id": "00000000-0000-0000-0000-000000000001",
        "email": "dev@local",
        "display_name": "Developer",
    }


# ==========================================
# Command/Query Handler Dependencies
# ==========================================

async def get_conversation_command_handler(
    service: ConversationService = Depends(get_conversation_service),
):
    """Get conversation command handler"""
    from ....application.commands.conversation_commands import ConversationCommandHandler
    return ConversationCommandHandler(service)


async def get_conversation_query_handler(
    service: ConversationService = Depends(get_conversation_service),
):
    """Get conversation query handler"""
    from ....application.queries.conversation_queries import ConversationQueryHandler
    return ConversationQueryHandler(service)


async def get_itinerary_command_handler(
    service: ItineraryService = Depends(get_itinerary_service),
):
    """Get itinerary command handler"""
    from ....application.commands.itinerary_commands import ItineraryCommandHandler
    return ItineraryCommandHandler(service)


async def get_itinerary_query_handler(
    service: ItineraryService = Depends(get_itinerary_service),
):
    """Get itinerary query handler"""
    from ....application.queries.itinerary_queries import ItineraryQueryHandler
    return ItineraryQueryHandler(service)


async def get_poi_command_handler(
    service: POIService = Depends(get_poi_service),
):
    """Get POI command handler"""
    from ....application.commands.poi_commands import POICommandHandler
    return POICommandHandler(service)


async def get_poi_query_handler(
    service: POIService = Depends(get_poi_service),
):
    """Get POI query handler"""
    from ....application.queries.poi_queries import POIQueryHandler
    return POIQueryHandler(service)


async def get_transit_command_handler(
    service: TransitService = Depends(get_transit_service),
):
    """Get transit command handler"""
    from ....application.commands.transit_commands import TransitCommandHandler
    return TransitCommandHandler(service)


async def get_transit_query_handler(
    service: TransitService = Depends(get_transit_service),
):
    """Get transit query handler"""
    from ....application.queries.transit_queries import TransitQueryHandler
    return TransitQueryHandler(service)


async def get_weather_query_handler(
    service: WeatherService = Depends(get_weather_service),
):
    """Get weather query handler"""
    from ....application.queries.weather_queries import WeatherQueryHandler
    return WeatherQueryHandler(service)


async def get_media_command_handler(
    service: MediaService = Depends(get_media_service),
):
    """Get media command handler"""
    from ....application.commands.media_commands import MediaCommandHandler
    return MediaCommandHandler(service)


async def get_user_command_handler(
    service: UserService = Depends(get_user_service),
):
    """Get user command handler"""
    from ....application.commands.user_commands import UserCommandHandler
    return UserCommandHandler(service)


async def get_user_query_handler(
    service: UserService = Depends(get_user_service),
):
    """Get user query handler"""
    from ....application.queries.user_queries import UserQueryHandler
    return UserQueryHandler(service)
