"""
Worker Service Main Entry Point

Background worker service for the AI Smart City Concierge.
Handles async background jobs, scheduled tasks, and event processing.
"""

import asyncio
import logging
import signal
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncGenerator

import redis.asyncio as redis
from ai_smart_city_concierge.domain.repositories.conversation_repository import (
    ConversationRepository,
)
from ai_smart_city_concierge.domain.repositories.itinerary_repository import ItineraryRepository
from ai_smart_city_concierge.domain.repositories.media_repository import MediaRepository
from ai_smart_city_concierge.domain.repositories.poi_repository import POIRepository
from ai_smart_city_concierge.domain.repositories.transit_repository import TransitRepository

# Repository imports
from ai_smart_city_concierge.domain.repositories.user_repository import UserRepository
from ai_smart_city_concierge.domain.repositories.weather_repository import WeatherRepository

# Service imports
from ai_smart_city_concierge.domain.services.itinerary_optimization_service import (
    ItineraryOptimizationService,
)
from ai_smart_city_concierge.domain.services.poi_service import POIService
from ai_smart_city_concierge.domain.services.transit_service import TransitService
from ai_smart_city_concierge.domain.services.weather_service import WeatherService
from ai_smart_city_concierge.infrastructure.config.settings import get_settings
from ai_smart_city_concierge.infrastructure.config.database import get_session_factory
from ai_smart_city_concierge.infrastructure.external_apis.bge_m3_client import BGEM3Client
from ai_smart_city_concierge.infrastructure.external_apis.clip_client import CLIPClient
from ai_smart_city_concierge.infrastructure.external_apis.gemini_client import GeminiClient
from ai_smart_city_concierge.infrastructure.external_apis.gtfs_client import GTFSClient
from ai_smart_city_concierge.infrastructure.external_apis.nominatim_client import NominatimClient
from ai_smart_city_concierge.infrastructure.external_apis.open_meteo_client import OpenMeteoClient
from ai_smart_city_concierge.infrastructure.external_apis.overpass_client import OverpassClient
from ai_smart_city_concierge.infrastructure.external_apis.whisper_client import WhisperClient
from ai_smart_city_concierge.infrastructure.messaging.local_event_bus import LocalEventBus
from ai_smart_city_concierge.infrastructure.storage.local_storage import LocalStorage
from ai_smart_city_concierge.infrastructure.vector_stores.chromadb_adapter import ChromaDBAdapter
from ai_smart_city_concierge.worker.consumers.event_consumers import (
    DeadLetterQueue,
    EventConsumer,
)
from ai_smart_city_concierge.worker.scheduler.cron_jobs import Scheduler, Schedules
from ai_smart_city_concierge.worker.tasks.conversation_analysis import ConversationAnalysisTask

# Task imports
from ai_smart_city_concierge.worker.tasks.embedding_generation import EmbeddingGenerationTask
from ai_smart_city_concierge.worker.tasks.itinerary_generation import ItineraryGenerationTask
from ai_smart_city_concierge.worker.tasks.media_processing import MediaProcessingTask
from ai_smart_city_concierge.worker.tasks.poi_enrichment import POIEnrichmentTask
from ai_smart_city_concierge.worker.tasks.queue import TaskQueue, TaskWorker
from ai_smart_city_concierge.worker.tasks.transit_sync import TransitSyncTask
from ai_smart_city_concierge.worker.tasks.weather_sync import WeatherSyncTask
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)


@dataclass
class RepositoryBundle:
    """Bundle of repositories sharing a single database session."""
    session: AsyncSession
    user_repository: UserRepository
    conversation_repository: ConversationRepository
    itinerary_repository: ItineraryRepository
    poi_repository: POIRepository
    transit_repository: TransitRepository
    weather_repository: WeatherRepository
    media_repository: MediaRepository


class WorkerService:
    """
    Main worker service that coordinates all background tasks.
    """

    def __init__(self, settings):
        self.settings = settings
        self._running = False

        # Core infrastructure
        self.redis: Redis | None = None
        self.event_bus: LocalEventBus | None = None

        # External API clients
        self.gemini_client: GeminiClient | None = None
        self.embedding_client: BGEM3Client | None = None
        self.whisper_client: WhisperClient | None = None
        self.clip_client: CLIPClient | None = None
        self.overpass_client: OverpassClient | None = None
        self.nominatim_client: NominatimClient | None = None
        self.weather_client: OpenMeteoClient | None = None
        self.gtfs_client: GTFSClient | None = None

        # Vector store
        self.vector_store: ChromaDBAdapter | None = None

        # Storage
        self.storage: LocalStorage | None = None

        # Session factory for creating fresh sessions per operation
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

        # Domain services (stateless, can be reused)
        self.itinerary_optimization_service: ItineraryOptimizationService | None = None
        self.poi_service: POIService | None = None
        self.transit_service: TransitService | None = None
        self.weather_service: WeatherService | None = None

        # Task running state (lightweight tracking)
        self._task_running: dict[str, bool] = {
            "embedding": False,
            "poi_enrichment": False,
            "transit_sync": False,
            "weather_sync": False,
            "itinerary_generation": False,
            "media_processing": False,
            "conversation_analysis": False,
        }

        # Infrastructure
        self.task_queue: TaskQueue | None = None
        self.task_worker: TaskWorker | None = None
        self.scheduler: Scheduler | None = None
        self.event_consumer: EventConsumer | None = None
        self.dead_letter_queue: DeadLetterQueue | None = None

    @asynccontextmanager
    async def _repositories(self) -> AsyncGenerator[RepositoryBundle, None]:
        """Create a new session and repository bundle for a single operation."""
        if self._session_factory is None:
            raise RuntimeError("Session factory not initialized. Call initialize() first.")

        async with self._session_factory() as session:
            from ai_smart_city_concierge.infrastructure.persistence.sqlalchemy.repositories import (
                SQLAlchemyConversationRepository,
                SQLAlchemyItineraryRepository,
                SQLAlchemyMediaRepository,
                SQLAlchemyPOIRepository,
                SQLAlchemyTransitRepository,
                SQLAlchemyUserRepository,
                SQLAlchemyWeatherRepository,
            )

            bundle = RepositoryBundle(
                session=session,
                user_repository=SQLAlchemyUserRepository(session),
                conversation_repository=SQLAlchemyConversationRepository(session),
                itinerary_repository=SQLAlchemyItineraryRepository(session),
                poi_repository=SQLAlchemyPOIRepository(session),
                transit_repository=SQLAlchemyTransitRepository(session),
                weather_repository=SQLAlchemyWeatherRepository(session),
                media_repository=SQLAlchemyMediaRepository(session),
            )
            try:
                yield bundle
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def initialize(self) -> None:
        """Initialize all components."""
        logger.info("Initializing worker service...")

        # Initialize Redis
        self.redis = redis.from_url(
            self.settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        await self.redis.ping()
        logger.info("Connected to Redis")

        # Initialize event bus
        self.event_bus = LocalEventBus()
        logger.info("Initialized event bus")

        # Initialize external API clients
        self.gemini_client = GeminiClient(api_key=self.settings.gemini_api_key)
        self.embedding_client = BGEM3Client(model_name=self.settings.embedding_model)
        self.whisper_client = WhisperClient(model_size=self.settings.whisper_model)
        self.clip_client = CLIPClient(model_name=self.settings.clip_model)
        self.overpass_client = OverpassClient()
        self.nominatim_client = NominatimClient()
        self.weather_client = OpenMeteoClient()
        self.gtfs_client = GTFSClient()
        logger.info("Initialized external API clients")

        # Initialize vector store
        self.vector_store = ChromaDBAdapter(
            host=self.settings.chromadb_host,
            port=self.settings.chromadb_port,
        )
        await self.vector_store.initialize()
        logger.info("Initialized vector store")

        # Initialize storage
        self.storage = LocalStorage(base_path=self.settings.storage_path)
        logger.info("Initialized storage")

        # Initialize session factory for per-operation sessions
        self._session_factory = get_session_factory()
        logger.info("Initialized session factory")

        # Initialize domain services (stateless - they don't hold sessions)
        self.itinerary_optimization_service = ItineraryOptimizationService()

        # Initialize background tasks with fresh repositories
        # We create a temporary repository bundle for initial task setup
        async with self._repositories() as repos:
            self.poi_service = POIService(
                poi_repository=repos.poi_repository,
                vector_store=self.vector_store,
                embedding_client=self.embedding_client,
            )
            self.transit_service = TransitService(
                transit_repository=repos.transit_repository,
                gtfs_client=self.gtfs_client,
            )
            self.weather_service = WeatherService(
                weather_repository=repos.weather_repository,
                weather_client=self.weather_client,
            )
            logger.info("Initialized domain services")

            await self._create_tasks_with_repos(repos)
            logger.info("Initialized background tasks")

        # Initialize task queue
        self.task_queue = TaskQueue(
            redis_client=self.redis,
            queue_name="worker",
            max_concurrent=self.settings.worker_max_concurrent,
        )

        # Register task handlers
        task_handlers = {
            "generate_embedding": self._handle_generate_embedding,
            "enrich_poi": self._handle_enrich_poi,
            "sync_transit": self._handle_sync_transit,
            "sync_weather": self._handle_sync_weather,
            "generate_itinerary": self._handle_generate_itinerary,
            "process_media": self._handle_process_media,
            "analyze_conversation": self._handle_analyze_conversation,
        }

        self.task_worker = TaskWorker(
            queue=self.task_queue,
            worker_id="worker-main",
            handlers=task_handlers,
            max_concurrent=self.settings.worker_max_concurrent,
        )

        logger.info("Initialized task queue and worker")

        # Initialize scheduler
        self.scheduler = Scheduler(check_interval_seconds=60)
        await self._setup_scheduled_jobs()
        logger.info("Initialized scheduler")

        # Initialize event consumer
        handlers = await create_default_handlers(self)

        self.event_consumer = EventConsumer(
            event_bus=self.event_bus,
            task_handlers=handlers,
        )

        # Initialize dead letter queue
        self.dead_letter_queue = DeadLetterQueue(
            event_bus=self.event_bus,
            max_retries=3,
            retry_delay_seconds=60,
        )

        logger.info("Initialized event consumer and DLQ")

    async def _setup_scheduled_jobs(self) -> None:
        """Set up scheduled jobs."""
        # Embedding regeneration - daily at 2 AM
        self.scheduler.add_job(
            name="regenerate_poi_embeddings",
            func=self._scheduled_regenerate_poi_embeddings,
            cron=Schedules.DAILY_6AM,  # 6 AM UTC
            kwargs={"batch_size": 100},
        )

        # POI enrichment - daily at 3 AM
        self.scheduler.add_job(
            name="enrich_all_pois",
            func=self._scheduled_enrich_all_pois,
            cron=Schedules.DAILY_6AM,
            kwargs={"enrichment_types": ["details", "opening_hours", "address", "accessibility"]},
        )

        # Transit static sync - daily at 4 AM
        self.scheduler.add_job(
            name="sync_transit_static",
            func=self._scheduled_sync_transit_static,
            cron=Schedules.DAILY_6AM,
            kwargs={"sync_types": ["static"]},
        )

        # Weather forecast sync - every 6 hours
        self.scheduler.add_job(
            name="sync_weather_forecasts",
            func=self._scheduled_sync_weather_forecasts,
            cron=Schedules.EVERY_6_HOURS,
            kwargs={"sync_types": ["current", "forecast", "alerts"]},
        )

        # Conversation analysis - every hour
        self.scheduler.add_job(
            name="analyze_recent_conversations",
            func=self._scheduled_analyze_recent_conversations,
            cron=Schedules.HOURLY,
            kwargs={"hours": 1, "analysis_types": ["sentiment", "topics", "intent"]},
        )

        # Queue cleanup - daily at midnight
        self.scheduler.add_job(
            name="cleanup_task_queue",
            func=self.task_queue.cleanup_old_tasks,
            cron=Schedules.DAILY_MIDNIGHT,
            kwargs={"max_age_hours": 24},
        )

        logger.info("Configured scheduled jobs")

    # Scheduled job wrappers that use fresh repositories

    async def _scheduled_regenerate_poi_embeddings(self, batch_size: int = 100) -> int:
        """Regenerate embeddings for all POIs with fresh repositories."""
        async with self._repositories() as repos:
            embedding_task = EmbeddingGenerationTask(
                embedding_client=self.embedding_client,
                vector_store=self.vector_store,
                poi_repository=repos.poi_repository,
                conversation_repository=repos.conversation_repository,
                itinerary_repository=repos.itinerary_repository,
                user_repository=repos.user_repository,
                max_concurrent=self.settings.worker_embedding_concurrency,
            )
            return await embedding_task.regenerate_all_poi_embeddings(batch_size)

    async def _scheduled_enrich_all_pois(self, enrichment_types: list[str]) -> int:
        """Enrich all POIs with fresh repositories."""
        async with self._repositories() as repos:
            poi_enrichment_task = POIEnrichmentTask(
                overpass_client=self.overpass_client,
                nominatim_client=self.nominatim_client,
                poi_repository=repos.poi_repository,
                max_concurrent=self.settings.worker_poi_enrichment_concurrency,
            )
            return await poi_enrichment_task.enrich_all_pois(enrichment_types)

    async def _scheduled_sync_transit_static(self, sync_types: list[str]) -> int:
        """Sync all transit agencies with fresh repositories."""
        async with self._repositories() as repos:
            transit_sync_task = TransitSyncTask(
                gtfs_client=self.gtfs_client,
                transit_repository=repos.transit_repository,
                max_concurrent=self.settings.worker_transit_sync_concurrency,
            )
            return await transit_sync_task.sync_all_agencies(sync_types)

    async def _scheduled_sync_weather_forecasts(self, sync_types: list[str]) -> int:
        """Sync weather for all locations with fresh repositories."""
        async with self._repositories() as repos:
            weather_sync_task = WeatherSyncTask(
                weather_client=self.weather_client,
                weather_repository=repos.weather_repository,
                max_concurrent=self.settings.worker_weather_sync_concurrency,
            )
            return await weather_sync_task.sync_all_locations(sync_types)

    async def _scheduled_analyze_recent_conversations(self, hours: int, analysis_types: list[str]) -> int:
        """Analyze recent conversations with fresh repositories."""
        async with self._repositories() as repos:
            conversation_analysis_task = ConversationAnalysisTask(
                gemini_client=self.gemini_client,
                embedding_client=self.embedding_client,
                vector_store=self.vector_store,
                conversation_repository=repos.conversation_repository,
                user_repository=repos.user_repository,
                max_concurrent=self.settings.worker_conversation_concurrency,
            )
            return await conversation_analysis_task.analyze_recent_conversations(hours, analysis_types)

    # Task handlers for the queue

    async def _handle_generate_embedding(self, payload: dict) -> dict:
        """Handle embedding generation task."""
        entity_type = payload.get("entity_type")
        entity_id = payload.get("entity_id")

        async with self._repositories() as repos:
            embedding_task = EmbeddingGenerationTask(
                embedding_client=self.embedding_client,
                vector_store=self.vector_store,
                poi_repository=repos.poi_repository,
                conversation_repository=repos.conversation_repository,
                itinerary_repository=repos.itinerary_repository,
                user_repository=repos.user_repository,
                max_concurrent=self.settings.worker_embedding_concurrency,
            )

            if entity_type == "poi":
                await embedding_task.generate_poi_embedding(entity_id)
            elif entity_type == "conversation":
                await embedding_task.generate_conversation_embedding(entity_id)
            elif entity_type == "itinerary":
                await embedding_task.generate_itinerary_embedding(entity_id)
            elif entity_type == "user_preference":
                await embedding_task.generate_user_preference_embedding(entity_id)

        return {"status": "completed", "entity_type": entity_type, "entity_id": entity_id}

    async def _handle_enrich_poi(self, payload: dict) -> dict:
        """Handle POI enrichment task."""
        poi_id = payload.get("poi_id")
        enrichment_types = payload.get("enrichment_types", ["details", "opening_hours", "address", "accessibility"])

        async with self._repositories() as repos:
            poi_enrichment_task = POIEnrichmentTask(
                overpass_client=self.overpass_client,
                nominatim_client=self.nominatim_client,
                poi_repository=repos.poi_repository,
                max_concurrent=self.settings.worker_poi_enrichment_concurrency,
            )
            await poi_enrichment_task.enrich_poi(poi_id, enrichment_types)

        return {"status": "completed", "poi_id": poi_id}

    async def _handle_sync_transit(self, payload: dict) -> dict:
        """Handle transit sync task."""
        agency_id = payload.get("agency_id")
        sync_types = payload.get("sync_types", ["static", "realtime"])

        async with self._repositories() as repos:
            transit_sync_task = TransitSyncTask(
                gtfs_client=self.gtfs_client,
                transit_repository=repos.transit_repository,
                max_concurrent=self.settings.worker_transit_sync_concurrency,
            )
            await transit_sync_task.sync_agency(agency_id, sync_types)

        return {"status": "completed", "agency_id": agency_id}

    async def _handle_sync_weather(self, payload: dict) -> dict:
        """Handle weather sync task."""
        location_id = payload.get("location_id")
        lat = payload.get("latitude")
        lng = payload.get("longitude")
        sync_types = payload.get("sync_types", ["current", "forecast", "alerts"])

        from ai_smart_city_concierge.domain.value_objects.coordinates import Coordinates
        coordinates = Coordinates(latitude=lat, longitude=lng)

        async with self._repositories() as repos:
            weather_sync_task = WeatherSyncTask(
                weather_client=self.weather_client,
                weather_repository=repos.weather_repository,
                max_concurrent=self.settings.worker_weather_sync_concurrency,
            )
            await weather_sync_task.sync_location(location_id, coordinates, sync_types)

        return {"status": "completed", "location_id": location_id}

    async def _handle_generate_itinerary(self, payload: dict) -> dict:
        """Handle itinerary generation task."""
        request_id = payload.get("request_id")

        async with self._repositories() as repos:
            from ai_smart_city_concierge.worker.tasks.itinerary_generation import (
                ItineraryGenerationTask as IGT,
            )

            gen_task = IGT(
                user_id=payload["user_id"],
                request_id=request_id,
                title=payload["title"],
                description=payload["description"],
                start_date=payload["start_date"],
                end_date=payload["end_date"],
                base_location=payload["base_location"],
                base_address=payload["base_address"],
                city=payload["city"],
                country=payload["country"],
                interests=payload["interests"],
                budget_level=payload["budget_level"],
                pace=payload["pace"],
                accessibility_needs=payload["accessibility_needs"],
                dietary_restrictions=payload["dietary_restrictions"],
                transport_preferences=payload["transport_preferences"],
            )

            itinerary_generation_task = ItineraryGenerationTask(
                gemini_client=self.gemini_client,
                itinerary_optimization_service=self.itinerary_optimization_service,
                poi_service=self.poi_service,
                transit_service=self.transit_service,
                weather_service=self.weather_service,
                itinerary_repository=repos.itinerary_repository,
                poi_repository=repos.poi_repository,
                max_concurrent=self.settings.worker_itinerary_concurrency,
            )

            await itinerary_generation_task.enqueue(gen_task)

        return {"status": "queued", "request_id": request_id}

    async def _handle_process_media(self, payload: dict) -> dict:
        """Handle media processing task."""
        media_id = payload.get("media_id")
        processing_types = payload.get("processing_types")

        async with self._repositories() as repos:
            media_processing_task = MediaProcessingTask(
                whisper_client=self.whisper_client,
                clip_client=self.clip_client,
                storage=self.storage,
                media_repository=repos.media_repository,
                max_concurrent=self.settings.worker_media_concurrency,
            )
            await media_processing_task.process_media(media_id, processing_types)

        return {"status": "completed", "media_id": media_id}

    async def _create_event_handlers(self) -> dict:
        """Create event handlers that use fresh repositories per event."""
        from ai_smart_city_concierge.domain.events import (
            ConversationStarted,
            FeedbackSubmitted,
            ItineraryCreated,
            ItineraryUpdated,
            MediaUploaded,
            MessageSent,
            POIRated,
            POIReviewed,
            POIVisited,
            RecommendationFeedbackGiven,
            RecommendationGenerated,
            TransitRouteViewed,
            TransitTripPlanned,
            UserProfileUpdated,
            UserRegistered,
            WeatherAlertTriggered,
        )

        handlers = {}

        # User events
        async def handle_user_registered(event: UserRegistered) -> None:
            logger.info(f"User registered: {event.user_id}")
            async with self._repositories() as repos:
                embedding_task = EmbeddingGenerationTask(
                    embedding_client=self.embedding_client,
                    vector_store=self.vector_store,
                    poi_repository=repos.poi_repository,
                    conversation_repository=repos.conversation_repository,
                    itinerary_repository=repos.itinerary_repository,
                    user_repository=repos.user_repository,
                    max_concurrent=self.settings.worker_embedding_concurrency,
                )
                await embedding_task.generate_user_preference_embedding(event.user_id)

        async def handle_user_profile_updated(event: UserProfileUpdated) -> None:
            logger.info(f"User profile updated: {event.user_id}")
            async with self._repositories() as repos:
                embedding_task = EmbeddingGenerationTask(
                    embedding_client=self.embedding_client,
                    vector_store=self.vector_store,
                    poi_repository=repos.poi_repository,
                    conversation_repository=repos.conversation_repository,
                    itinerary_repository=repos.itinerary_repository,
                    user_repository=repos.user_repository,
                    max_concurrent=self.settings.worker_embedding_concurrency,
                )
                await embedding_task.generate_user_preference_embedding(event.user_id)

        handlers["UserRegistered"] = handle_user_registered
        handlers["UserProfileUpdated"] = handle_user_profile_updated

        # Conversation events
        async def handle_conversation_started(event: ConversationStarted) -> None:
            logger.info(f"Conversation started: {event.conversation_id}")

        async def handle_message_sent(event: MessageSent) -> None:
            logger.debug(f"Message sent in conversation: {event.conversation_id}")
            async with self._repositories() as repos:
                conversation_analysis_task = ConversationAnalysisTask(
                    gemini_client=self.gemini_client,
                    embedding_client=self.embedding_client,
                    vector_store=self.vector_store,
                    conversation_repository=repos.conversation_repository,
                    user_repository=repos.user_repository,
                    max_concurrent=self.settings.worker_conversation_concurrency,
                )
                await conversation_analysis_task.analyze_conversation(
                    event.conversation_id,
                    ["intent", "sentiment"]
                )

        handlers["ConversationStarted"] = handle_conversation_started
        handlers["MessageSent"] = handle_message_sent

        # Itinerary events
        async def handle_itinerary_created(event: ItineraryCreated) -> None:
            logger.info(f"Itinerary created: {event.itinerary_id}")
            async with self._repositories() as repos:
                embedding_task = EmbeddingGenerationTask(
                    embedding_client=self.embedding_client,
                    vector_store=self.vector_store,
                    poi_repository=repos.poi_repository,
                    conversation_repository=repos.conversation_repository,
                    itinerary_repository=repos.itinerary_repository,
                    user_repository=repos.user_repository,
                    max_concurrent=self.settings.worker_embedding_concurrency,
                )
                await embedding_task.generate_itinerary_embedding(event.itinerary_id)

        async def handle_itinerary_updated(event: ItineraryUpdated) -> None:
            logger.info(f"Itinerary updated: {event.itinerary_id}")
            async with self._repositories() as repos:
                embedding_task = EmbeddingGenerationTask(
                    embedding_client=self.embedding_client,
                    vector_store=self.vector_store,
                    poi_repository=repos.poi_repository,
                    conversation_repository=repos.conversation_repository,
                    itinerary_repository=repos.itinerary_repository,
                    user_repository=repos.user_repository,
                    max_concurrent=self.settings.worker_embedding_concurrency,
                )
                await embedding_task.generate_itinerary_embedding(event.itinerary_id)

        handlers["ItineraryCreated"] = handle_itinerary_created
        handlers["ItineraryUpdated"] = handle_itinerary_updated

        # POI events
        async def handle_poi_visited(event: POIVisited) -> None:
            logger.info(f"POI visited: {event.poi_id} by user {event.user_id}")

        async def handle_poi_rated(event: POIRated) -> None:
            logger.info(f"POI rated: {event.poi_id} - {event.rating}/5")
            async with self._repositories() as repos:
                embedding_task = EmbeddingGenerationTask(
                    embedding_client=self.embedding_client,
                    vector_store=self.vector_store,
                    poi_repository=repos.poi_repository,
                    conversation_repository=repos.conversation_repository,
                    itinerary_repository=repos.itinerary_repository,
                    user_repository=repos.user_repository,
                    max_concurrent=self.settings.worker_embedding_concurrency,
                )
                await embedding_task.generate_poi_embedding(event.poi_id)

        async def handle_poi_reviewed(event: POIReviewed) -> None:
            logger.info(f"POI reviewed: {event.poi_id}")
            async with self._repositories() as repos:
                embedding_task = EmbeddingGenerationTask(
                    embedding_client=self.embedding_client,
                    vector_store=self.vector_store,
                    poi_repository=repos.poi_repository,
                    conversation_repository=repos.conversation_repository,
                    itinerary_repository=repos.itinerary_repository,
                    user_repository=repos.user_repository,
                    max_concurrent=self.settings.worker_embedding_concurrency,
                )
                await embedding_task.generate_poi_embedding(event.poi_id)

        handlers["POIVisited"] = handle_poi_visited
        handlers["POIRated"] = handle_poi_rated
        handlers["POIReviewed"] = handle_poi_reviewed

        # Transit events
        async def handle_transit_route_viewed(event: TransitRouteViewed) -> None:
            logger.debug(f"Transit route viewed: {event.route_id}")

        async def handle_transit_trip_planned(event: TransitTripPlanned) -> None:
            logger.info(f"Transit trip planned: {event.trip_id}")

        handlers["TransitRouteViewed"] = handle_transit_route_viewed
        handlers["TransitTripPlanned"] = handle_transit_trip_planned

        # Weather events
        async def handle_weather_alert_triggered(event: WeatherAlertTriggered) -> None:
            logger.warning(f"Weather alert: {event.alert_type} for {event.location}")

        handlers["WeatherAlertTriggered"] = handle_weather_alert_triggered

        # Media events
        async def handle_media_uploaded(event: MediaUploaded) -> None:
            logger.info(f"Media uploaded: {event.media_id} ({event.media_type})")
            async with self._repositories() as repos:
                media_processing_task = MediaProcessingTask(
                    whisper_client=self.whisper_client,
                    clip_client=self.clip_client,
                    storage=self.storage,
                    media_repository=repos.media_repository,
                    max_concurrent=self.settings.worker_media_concurrency,
                )
                await media_processing_task.process_media(event.media_id)

        handlers["MediaUploaded"] = handle_media_uploaded

        # Feedback events
        async def handle_feedback_submitted(event: FeedbackSubmitted) -> None:
            logger.info(f"Feedback submitted: {event.feedback_id} - {event.rating}/5")

        handlers["FeedbackSubmitted"] = handle_feedback_submitted

        # Recommendation events
        async def handle_recommendation_generated(event: RecommendationGenerated) -> None:
            logger.info(f"Recommendation generated: {event.recommendation_id}")

        async def handle_recommendation_feedback(event: RecommendationFeedbackGiven) -> None:
            logger.info(f"Recommendation feedback: {event.recommendation_id} - {event.feedback}")

        handlers["RecommendationGenerated"] = handle_recommendation_generated
        handlers["RecommendationFeedbackGiven"] = handle_recommendation_feedback

        return handlers

    async def start(self) -> None:
        """Start all background tasks."""
        if self._running:
            return

        self._running = True
        logger.info("Starting worker service...")

        # Mark tasks as running (they're created on-demand with fresh repositories)
        for key in self._task_running:
            self._task_running[key] = True

        # Start task queue worker
        await self.task_worker.start()

        # Start scheduler
        await self.scheduler.start()

        # Start event consumer
        await self.event_consumer.start()

        # Start dead letter queue
        await self.dead_letter_queue.start()

        logger.info("Worker service started successfully")

    async def stop(self) -> None:
        """Stop all background tasks."""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping worker service...")

        # Mark tasks as stopped
        for key in self._task_running:
            self._task_running[key] = False

        # Stop in reverse order
        await self.dead_letter_queue.stop()
        await self.event_consumer.stop()
        await self.scheduler.stop()
        await self.task_worker.stop()

        # Close connections
        if self.redis:
            await self.redis.close()

        logger.info("Worker service stopped")

    def is_running(self) -> bool:
        """Check if service is running."""
        return self._running

    async def get_status(self) -> dict:
        """Get service status."""
        queue_stats = await self.task_queue.get_queue_stats() if self.task_queue else {}

        return {
            "running": self._running,
            "tasks": self._task_running.copy(),
            "queue": queue_stats,
            "scheduler": {
                "jobs": len(self.scheduler.list_jobs()) if self.scheduler else 0,
                "next_runs": self.scheduler.get_next_runs(5) if self.scheduler else [],
            },
            "dlq_size": self.dead_letter_queue.get_dlq_size() if self.dead_letter_queue else 0,
        }


# Global worker service instance
_worker_service: WorkerService | None = None


async def get_worker_service() -> WorkerService:
    """Get or create the worker service instance."""
    global _worker_service
    if _worker_service is None:
        settings = get_settings()
        _worker_service = WorkerService(settings)
        await _worker_service.initialize()
    return _worker_service


async def shutdown_worker_service() -> None:
    """Shutdown the worker service."""
    global _worker_service
    if _worker_service:
        await _worker_service.stop()
        _worker_service = None


@asynccontextmanager
async def worker_lifespan():
    """Context manager for worker service lifespan."""
    service = await get_worker_service()
    await service.start()
    try:
        yield service
    finally:
        await service.stop()


async def main() -> None:
    """Main entry point for the worker service."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("Starting AI Smart City Concierge Worker Service")

    # Get settings
    settings = get_settings()

    # Create and initialize worker service
    worker = WorkerService(settings)
    await worker.initialize()

    # Set up signal handlers
    loop = asyncio.get_event_loop()

    def signal_handler(sig):
        logger.info(f"Received signal {sig}, shutting down...")
        asyncio.create_task(worker.stop())

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))

    # Start worker
    await worker.start()

    logger.info("Worker service is running. Press Ctrl+C to stop.")

    # Keep running until stopped
    try:
        while worker.is_running():
            await asyncio.sleep(10)
            # Log status periodically
            status = await worker.get_status()
            logger.debug(f"Worker status: {status}")
    except asyncio.CancelledError:
        pass
    finally:
        await worker.stop()
        logger.info("Worker service stopped")


if __name__ == "__main__":
    asyncio.run(main())
