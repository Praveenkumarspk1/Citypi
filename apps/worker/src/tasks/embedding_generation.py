"""
Embedding Generation Background Tasks

Handles generation of embeddings for POIs, conversations, itineraries, and user preferences
using the BGE-M3 embedding model.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime

from ai_smart_city_concierge.domain.repositories.conversation_repository import (
    ConversationRepository,
)
from ai_smart_city_concierge.domain.repositories.itinerary_repository import ItineraryRepository
from ai_smart_city_concierge.domain.repositories.poi_repository import POIRepository
from ai_smart_city_concierge.domain.repositories.user_repository import UserRepository
from ai_smart_city_concierge.infrastructure.external_apis.bge_m3_client import BGEM3Client
from ai_smart_city_concierge.infrastructure.vector_stores.base_vector_store import BaseVectorStore

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingTask:
    """Task for embedding generation."""
    entity_type: str  # 'poi', 'conversation', 'itinerary', 'user_preference'
    entity_id: str
    text_content: str
    metadata: dict
    priority: int = 0  # Higher = more urgent


class EmbeddingGenerationTask:
    """
    Background task for generating and storing embeddings.

    Processes embedding tasks from a queue, generates embeddings using BGE-M3,
    and stores them in the vector database.
    """

    def __init__(
        self,
        embedding_client: BGEM3Client,
        vector_store: BaseVectorStore,
        poi_repository: POIRepository,
        conversation_repository: ConversationRepository,
        itinerary_repository: ItineraryRepository,
        user_repository: UserRepository,
        batch_size: int = 32,
        max_concurrent: int = 4,
    ):
        self.embedding_client = embedding_client
        self.vector_store = vector_store
        self.poi_repository = poi_repository
        self.conversation_repository = conversation_repository
        self.itinerary_repository = itinerary_repository
        self.user_repository = user_repository
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self._queue: asyncio.Queue[EmbeddingTask] = asyncio.Queue()
        self._running = False
        self._worker_tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        """Start the embedding generation workers."""
        if self._running:
            return

        self._running = True
        logger.info("Starting embedding generation workers")

        for i in range(self.max_concurrent):
            task = asyncio.create_task(self._worker(f"embedding-worker-{i}"))
            self._worker_tasks.append(task)

    async def stop(self) -> None:
        """Stop the embedding generation workers."""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping embedding generation workers")

        # Wait for queue to empty
        await self._queue.join()

        # Cancel workers
        for task in self._worker_tasks:
            task.cancel()

        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()

    async def enqueue(self, task: EmbeddingTask) -> None:
        """Add an embedding task to the queue."""
        await self._queue.put(task)

    async def enqueue_batch(self, tasks: list[EmbeddingTask]) -> None:
        """Add multiple embedding tasks to the queue."""
        for task in tasks:
            await self._queue.put(task)

    async def _worker(self, worker_name: str) -> None:
        """Worker coroutine that processes embedding tasks."""
        logger.info(f"{worker_name} started")

        while self._running:
            try:
                # Get task with timeout to allow checking _running flag
                task = await asyncio.wait_for(self._queue.get(), timeout=1.0)

                try:
                    await self._process_task(task)
                except Exception as e:
                    logger.error(f"{worker_name} error processing task {task.entity_id}: {e}")
                finally:
                    self._queue.task_done()

            except TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"{worker_name} unexpected error: {e}")
                await asyncio.sleep(1)

        logger.info(f"{worker_name} stopped")

    async def _process_task(self, task: EmbeddingTask) -> None:
        """Process a single embedding task."""
        logger.debug(f"Generating embedding for {task.entity_type}:{task.entity_id}")

        # Generate embedding
        embedding = await self.embedding_client.embed_text(task.text_content)

        if not embedding:
            logger.warning(f"Failed to generate embedding for {task.entity_type}:{task.entity_id}")
            return

        # Prepare metadata
        metadata = {
            "entity_type": task.entity_type,
            "entity_id": task.entity_id,
            "text_content": task.text_content[:500],  # Truncate for storage
            "created_at": datetime.utcnow().isoformat(),
            **task.metadata,
        }

        # Store in vector database
        vector_id = f"{task.entity_type}:{task.entity_id}"
        await self.vector_store.upsert(
            collection_name=self._get_collection_name(task.entity_type),
            vectors=[{
                "id": vector_id,
                "vector": embedding,
                "metadata": metadata,
            }]
        )

        logger.debug(f"Stored embedding for {task.entity_type}:{task.entity_id}")

    def _get_collection_name(self, entity_type: str) -> str:
        """Get vector collection name for entity type."""
        collection_map = {
            "poi": "pois",
            "conversation": "conversations",
            "itinerary": "itineraries",
            "user_preference": "user_preferences",
        }
        return collection_map.get(entity_type, "default")

    # High-level methods for common embedding tasks

    async def generate_poi_embedding(self, poi_id: str) -> None:
        """Generate embedding for a POI."""
        poi = await self.poi_repository.get_by_id(poi_id)
        if not poi:
            logger.warning(f"POI not found: {poi_id}")
            return

        # Combine POI information for embedding
        text_parts = [
            poi.name,
            poi.description or "",
            poi.category,
            poi.subcategory or "",
            " ".join(poi.tags),
        ]
        text_content = " ".join(filter(None, text_parts))

        await self.enqueue(EmbeddingTask(
            entity_type="poi",
            entity_id=poi_id,
            text_content=text_content,
            metadata={
                "category": poi.category,
                "subcategory": poi.subcategory,
                "tags": poi.tags,
                "coordinates": {
                    "lat": poi.coordinates.latitude,
                    "lng": poi.coordinates.longitude,
                } if poi.coordinates else None,
            },
            priority=1,
        ))

    async def generate_conversation_embedding(self, conversation_id: str) -> None:
        """Generate embedding for a conversation."""
        conversation = await self.conversation_repository.get_by_id(conversation_id)
        if not conversation:
            logger.warning(f"Conversation not found: {conversation_id}")
            return

        # Use conversation title and recent messages
        text_parts = [conversation.title or ""]

        # Get recent messages (last 10)
        messages = await self.conversation_repository.get_messages(
            conversation_id, limit=10
        )
        for msg in messages:
            text_parts.append(msg.content)

        text_content = " ".join(filter(None, text_parts))

        await self.enqueue(EmbeddingTask(
            entity_type="conversation",
            entity_id=conversation_id,
            text_content=text_content,
            metadata={
                "user_id": conversation.user_id,
                "language": conversation.language,
                "message_count": conversation.message_count,
            },
            priority=2,
        ))

    async def generate_itinerary_embedding(self, itinerary_id: str) -> None:
        """Generate embedding for an itinerary."""
        itinerary = await self.itinerary_repository.get_by_id(itinerary_id)
        if not itinerary:
            logger.warning(f"Itinerary not found: {itinerary_id}")
            return

        # Combine itinerary information
        text_parts = [
            itinerary.title,
            itinerary.description or "",
            " ".join(itinerary.interests),
            " ".join(itinerary.tags),
        ]

        # Add day titles and POI names
        for day in itinerary.days:
            if day.title:
                text_parts.append(day.title)
            for item in day.items:
                text_parts.append(item.title)

        text_content = " ".join(filter(None, text_parts))

        await self.enqueue(EmbeddingTask(
            entity_type="itinerary",
            entity_id=itinerary_id,
            text_content=text_content,
            metadata={
                "user_id": itinerary.user_id,
                "status": itinerary.status,
                "start_date": itinerary.start_date,
                "end_date": itinerary.end_date,
                "city": itinerary.city,
                "country": itinerary.country,
                "interests": itinerary.interests,
            },
            priority=1,
        ))

    async def generate_user_preference_embedding(self, user_id: str) -> None:
        """Generate embedding for user preferences."""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            logger.warning(f"User not found: {user_id}")
            return

        # Combine user preferences
        text_parts = [
            " ".join(user.interests),
            " ".join(user.accessibility_needs),
            " ".join(user.dietary_restrictions),
            " ".join(user.preferred_transport_modes),
            user.budget_level,
        ]

        text_content = " ".join(filter(None, text_parts))

        if not text_content.strip():
            logger.debug(f"No preference content for user {user_id}")
            return

        await self.enqueue(EmbeddingTask(
            entity_type="user_preference",
            entity_id=user_id,
            text_content=text_content,
            metadata={
                "locale": user.locale,
                "timezone": user.timezone,
                "budget_level": user.budget_level,
            },
            priority=0,
        ))

    async def regenerate_all_poi_embeddings(self, batch_size: int = 100) -> int:
        """Regenerate embeddings for all POIs. Returns count processed."""
        count = 0
        offset = 0

        while True:
            pois = await self.poi_repository.list(limit=batch_size, offset=offset)
            if not pois:
                break

            tasks = [
                EmbeddingTask(
                    entity_type="poi",
                    entity_id=poi.id,
                    text_content=" ".join(filter(None, [
                        poi.name,
                        poi.description or "",
                        poi.category,
                        poi.subcategory or "",
                        " ".join(poi.tags),
                    ])),
                    metadata={
                        "category": poi.category,
                        "subcategory": poi.subcategory,
                        "tags": poi.tags,
                        "coordinates": {
                            "lat": poi.coordinates.latitude,
                            "lng": poi.coordinates.longitude,
                        } if poi.coordinates else None,
                    },
                    priority=0,
                )
                for poi in pois
            ]

            await self.enqueue_batch(tasks)
            count += len(pois)
            offset += batch_size

            logger.info(f"Queued {count} POI embeddings for regeneration")

        return count

    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()

    def is_running(self) -> bool:
        """Check if workers are running."""
        return self._running
