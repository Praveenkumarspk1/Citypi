"""
Event Consumers

Consumes domain events from the message bus and triggers background tasks.
"""

import asyncio
import contextlib
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

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
from ai_smart_city_concierge.infrastructure.messaging.local_event_bus import LocalEventBus
from ai_smart_city_concierge.worker.tasks.embedding_generation import EmbeddingGenerationTask
from ai_smart_city_concierge.worker.tasks.media_processing import MediaProcessingTask
from ai_smart_city_concierge.worker.tasks.conversation_analysis import ConversationAnalysisTask

logger = logging.getLogger(__name__)


@dataclass
class EventHandler:
    """Event handler registration."""
    event_type: str
    handler: Callable
    filter_func: Callable | None = None


class EventConsumer:
    """
    Consumes domain events and routes them to appropriate handlers.
    """

    def __init__(
        self,
        event_bus: LocalEventBus,
        task_handlers: dict[str, Callable],
    ):
        self.event_bus = event_bus
        self.task_handlers = task_handlers
        self._handlers: list[EventHandler] = []
        self._running = False
        self._consumer_task: asyncio.Task | None = None
        self._subscriptions: list[str] = []

    def register_handler(
        self,
        event_type: str,
        handler: Callable,
        filter_func: Callable | None = None,
    ) -> None:
        """Register an event handler."""
        self._handlers.append(EventHandler(
            event_type=event_type,
            handler=handler,
            filter_func=filter_func,
        ))
        logger.debug(f"Registered handler for {event_type}")

    async def start(self) -> None:
        """Start consuming events."""
        if self._running:
            return

        self._running = True
        logger.info("Starting event consumer")

        # Subscribe to all event types we handle
        event_types = {h.event_type for h in self._handlers}
        for event_type in event_types:
            await self.event_bus.subscribe(event_type, self._on_event)
            self._subscriptions.append(event_type)

        self._consumer_task = asyncio.create_task(self._consumer_loop())

    async def stop(self) -> None:
        """Stop consuming events."""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping event consumer")

        # Unsubscribe
        for event_type in self._subscriptions:
            await self.event_bus.unsubscribe(event_type, self._on_event)
        self._subscriptions.clear()

        if self._consumer_task:
            self._consumer_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._consumer_task

    async def _consumer_loop(self) -> None:
        """Main consumer loop (for polling-based buses)."""
        while self._running:
            try:
                # For LocalEventBus, events are pushed via callbacks
                # This loop just keeps the consumer alive
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Event consumer loop error: {e}")
                await asyncio.sleep(1)

    async def _on_event(self, event: Any) -> None:
        """Handle incoming event."""
        event_type = type(event).__name__
        logger.debug(f"Received event: {event_type}")

        # Find matching handlers
        for handler_reg in self._handlers:
            if handler_reg.event_type == event_type:
                # Apply filter if provided
                if handler_reg.filter_func and not handler_reg.filter_func(event):
                    continue

                try:
                    await handler_reg.handler(event)
                except Exception as e:
                    logger.error(f"Handler for {event_type} failed: {e}")


# Default event handlers that map to background tasks

async def create_default_handlers(worker_service) -> dict[str, Callable]:
    """Create default event handlers mapping to background tasks with fresh repositories."""

    handlers = {}

    # User events
    async def handle_user_registered(event: UserRegistered) -> None:
        logger.info(f"User registered: {event.user_id}")
        # Generate initial preference embedding
        async with worker_service._repositories() as repos:
            embedding_task = EmbeddingGenerationTask(
                embedding_client=worker_service.embedding_client,
                vector_store=worker_service.vector_store,
                poi_repository=repos.poi_repository,
                conversation_repository=repos.conversation_repository,
                itinerary_repository=repos.itinerary_repository,
                user_repository=repos.user_repository,
                max_concurrent=worker_service.settings.worker_embedding_concurrency,
            )
            await embedding_task.generate_user_preference_embedding(event.user_id)

    async def handle_user_profile_updated(event: UserProfileUpdated) -> None:
        logger.info(f"User profile updated: {event.user_id}")
        # Regenerate preference embedding
        async with worker_service._repositories() as repos:
            embedding_task = EmbeddingGenerationTask(
                embedding_client=worker_service.embedding_client,
                vector_store=worker_service.vector_store,
                poi_repository=repos.poi_repository,
                conversation_repository=repos.conversation_repository,
                itinerary_repository=repos.itinerary_repository,
                user_repository=repos.user_repository,
                max_concurrent=worker_service.settings.worker_embedding_concurrency,
            )
            await embedding_task.generate_user_preference_embedding(event.user_id)

    handlers["UserRegistered"] = handle_user_registered
    handlers["UserProfileUpdated"] = handle_user_profile_updated

    # Conversation events
    async def handle_conversation_started(event: ConversationStarted) -> None:
        logger.info(f"Conversation started: {event.conversation_id}")

    async def handle_message_sent(event: MessageSent) -> None:
        logger.debug(f"Message sent in conversation: {event.conversation_id}")
        # Trigger conversation analysis (debounced)
        async with worker_service._repositories() as repos:
            conversation_analysis_task = ConversationAnalysisTask(
                gemini_client=worker_service.gemini_client,
                embedding_client=worker_service.embedding_client,
                vector_store=worker_service.vector_store,
                conversation_repository=repos.conversation_repository,
                user_repository=repos.user_repository,
                max_concurrent=worker_service.settings.worker_conversation_concurrency,
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
        # Generate embedding for the new itinerary
        async with worker_service._repositories() as repos:
            embedding_task = EmbeddingGenerationTask(
                embedding_client=worker_service.embedding_client,
                vector_store=worker_service.vector_store,
                poi_repository=repos.poi_repository,
                conversation_repository=repos.conversation_repository,
                itinerary_repository=repos.itinerary_repository,
                user_repository=repos.user_repository,
                max_concurrent=worker_service.settings.worker_embedding_concurrency,
            )
            await embedding_task.generate_itinerary_embedding(event.itinerary_id)

    async def handle_itinerary_updated(event: ItineraryUpdated) -> None:
        logger.info(f"Itinerary updated: {event.itinerary_id}")
        # Regenerate embedding
        async with worker_service._repositories() as repos:
            embedding_task = EmbeddingGenerationTask(
                embedding_client=worker_service.embedding_client,
                vector_store=worker_service.vector_store,
                poi_repository=repos.poi_repository,
                conversation_repository=repos.conversation_repository,
                itinerary_repository=repos.itinerary_repository,
                user_repository=repos.user_repository,
                max_concurrent=worker_service.settings.worker_embedding_concurrency,
            )
            await embedding_task.generate_itinerary_embedding(event.itinerary_id)

    handlers["ItineraryCreated"] = handle_itinerary_created
    handlers["ItineraryUpdated"] = handle_itinerary_updated

    # POI events
    async def handle_poi_visited(event: POIVisited) -> None:
        logger.info(f"POI visited: {event.poi_id} by user {event.user_id}")

    async def handle_poi_rated(event: POIRated) -> None:
        logger.info(f"POI rated: {event.poi_id} - {event.rating}/5")
        # Regenerate POI embedding with new rating
        async with worker_service._repositories() as repos:
            embedding_task = EmbeddingGenerationTask(
                embedding_client=worker_service.embedding_client,
                vector_store=worker_service.vector_store,
                poi_repository=repos.poi_repository,
                conversation_repository=repos.conversation_repository,
                itinerary_repository=repos.itinerary_repository,
                user_repository=repos.user_repository,
                max_concurrent=worker_service.settings.worker_embedding_concurrency,
            )
            await embedding_task.generate_poi_embedding(event.poi_id)

    async def handle_poi_reviewed(event: POIReviewed) -> None:
        logger.info(f"POI reviewed: {event.poi_id}")
        # Regenerate POI embedding with new review
        async with worker_service._repositories() as repos:
            embedding_task = EmbeddingGenerationTask(
                embedding_client=worker_service.embedding_client,
                vector_store=worker_service.vector_store,
                poi_repository=repos.poi_repository,
                conversation_repository=repos.conversation_repository,
                itinerary_repository=repos.itinerary_repository,
                user_repository=repos.user_repository,
                max_concurrent=worker_service.settings.worker_embedding_concurrency,
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
        # Process media (transcribe, analyze, thumbnail)
        async with worker_service._repositories() as repos:
            media_processing_task = MediaProcessingTask(
                whisper_client=worker_service.whisper_client,
                clip_client=worker_service.clip_client,
                storage=worker_service.storage,
                media_repository=repos.media_repository,
                max_concurrent=worker_service.settings.worker_media_concurrency,
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


class DeadLetterQueue:
    """
    Handles failed event processing with dead letter queue.
    """

    def __init__(
        self,
        event_bus: LocalEventBus,
        max_retries: int = 3,
        retry_delay_seconds: int = 60,
    ):
        self.event_bus = event_bus
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self._dlq: list[dict[str, Any]] = []
        self._running = False
        self._processor_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the DLQ processor."""
        if self._running:
            return

        self._running = True
        logger.info("Starting dead letter queue processor")
        self._processor_task = asyncio.create_task(self._process_dlq())

    async def stop(self) -> None:
        """Stop the DLQ processor."""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping dead letter queue processor")

        if self._processor_task:
            self._processor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._processor_task

    def add_failed_event(
        self,
        event: Any,
        error: str,
        handler_name: str,
        retry_count: int = 0,
    ) -> None:
        """Add a failed event to the DLQ."""
        self._dlq.append({
            "event": event,
            "event_type": type(event).__name__,
            "error": error,
            "handler_name": handler_name,
            "retry_count": retry_count,
            "failed_at": datetime.utcnow().isoformat(),
        })
        logger.warning(f"Added to DLQ: {type(event).__name__} (retry {retry_count}/{self.max_retries})")

    async def _process_dlq(self) -> None:
        """Process dead letter queue."""
        while self._running:
            try:
                if not self._dlq:
                    await asyncio.sleep(60)
                    continue

                # Process items
                items_to_process = self._dlq[:10]
                self._dlq = self._dlq[10:]

                for item in items_to_process:
                    await self._retry_event(item)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"DLQ processor error: {e}")
                await asyncio.sleep(60)

    async def _retry_event(self, item: dict[str, Any]) -> None:
        """Retry a failed event."""
        if item["retry_count"] >= self.max_retries:
            logger.error(f"Max retries exceeded for {item['event_type']}, giving up")
            # Could persist to permanent storage for manual review
            return

        # Wait before retry
        await asyncio.sleep(self.retry_delay_seconds * (item["retry_count"] + 1))

        # Re-publish event
        try:
            await self.event_bus.publish(item["event"])
            logger.info(f"Retried event {item['event_type']} (attempt {item['retry_count'] + 1})")
        except Exception as e:
            logger.error(f"Retry failed for {item['event_type']}: {e}")
            # Re-add to DLQ with incremented count
            item["retry_count"] += 1
            self._dlq.append(item)

    def get_dlq_size(self) -> int:
        """Get current DLQ size."""
        return len(self._dlq)

    def get_dlq_items(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get DLQ items for inspection."""
        return self._dlq[:limit]
