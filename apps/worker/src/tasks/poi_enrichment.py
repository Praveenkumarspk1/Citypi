"""
POI Enrichment Background Tasks

Handles enrichment of POI data from external sources like Overpass API,
Nominatim, Google Places, etc.
"""

import asyncio
import logging
from dataclasses import dataclass

from ai_smart_city_concierge.domain.repositories.poi_repository import POIRepository
from ai_smart_city_concierge.domain.value_objects.accessibility import AccessibilityFeatures
from ai_smart_city_concierge.domain.value_objects.address import Address
from ai_smart_city_concierge.domain.value_objects.opening_hours import OpeningHours
from ai_smart_city_concierge.infrastructure.external_apis.nominatim_client import NominatimClient
from ai_smart_city_concierge.infrastructure.external_apis.overpass_client import OverpassClient

logger = logging.getLogger(__name__)


@dataclass
class POIEnrichmentTask:
    """Task for POI enrichment."""
    poi_id: str
    enrichment_type: str  # 'details', 'photos', 'reviews', 'opening_hours', 'accessibility'
    priority: int = 0
    force_refresh: bool = False


class POIEnrichmentTask:
    """
    Background task for enriching POI data from external sources.
    """

    def __init__(
        self,
        overpass_client: OverpassClient,
        nominatim_client: NominatimClient,
        poi_repository: POIRepository,
        max_concurrent: int = 4,
        rate_limit_per_second: float = 1.0,
    ):
        self.overpass_client = overpass_client
        self.nominatim_client = nominatim_client
        self.poi_repository = poi_repository
        self.max_concurrent = max_concurrent
        self.rate_limit_per_second = rate_limit_per_second
        self._queue: asyncio.Queue[POIEnrichmentTask] = asyncio.Queue()
        self._running = False
        self._worker_tasks: list[asyncio.Task] = []
        self._last_request_time = 0.0

    async def start(self) -> None:
        """Start the POI enrichment workers."""
        if self._running:
            return

        self._running = True
        logger.info("Starting POI enrichment workers")

        for i in range(self.max_concurrent):
            task = asyncio.create_task(self._worker(f"poi-enrichment-worker-{i}"))
            self._worker_tasks.append(task)

    async def stop(self) -> None:
        """Stop the POI enrichment workers."""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping POI enrichment workers")

        await self._queue.join()

        for task in self._worker_tasks:
            task.cancel()

        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()

    async def enqueue(self, task: POIEnrichmentTask) -> None:
        """Add a POI enrichment task to the queue."""
        await self._queue.put(task)

    async def enqueue_batch(self, tasks: list[POIEnrichmentTask]) -> None:
        """Add multiple POI enrichment tasks to the queue."""
        for task in tasks:
            await self._queue.put(task)

    async def _worker(self, worker_name: str) -> None:
        """Worker coroutine that processes POI enrichment tasks."""
        logger.info(f"{worker_name} started")

        while self._running:
            try:
                task = await asyncio.wait_for(self._queue.get(), timeout=1.0)

                try:
                    await self._process_task(task)
                except Exception as e:
                    logger.error(f"{worker_name} error processing task {task.poi_id}: {e}")
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

    async def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        now = asyncio.get_event_loop().time()
        min_interval = 1.0 / self.rate_limit_per_second
        elapsed = now - self._last_request_time

        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)

        self._last_request_time = asyncio.get_event_loop().time()

    async def _process_task(self, task: POIEnrichmentTask) -> None:
        """Process a single POI enrichment task."""
        logger.debug(f"Enriching POI {task.poi_id} with {task.enrichment_type}")

        poi = await self.poi_repository.get_by_id(task.poi_id)
        if not poi:
            logger.warning(f"POI not found: {task.poi_id}")
            return

        # Check if already enriched recently (unless forced)
        if not task.force_refresh and self._is_recently_enriched(poi, task.enrichment_type):
            logger.debug(f"POI {task.poi_id} already enriched recently for {task.enrichment_type}")
            return

        await self._rate_limit()

        if task.enrichment_type == "details":
            await self._enrich_details(poi)
        elif task.enrichment_type == "opening_hours":
            await self._enrich_opening_hours(poi)
        elif task.enrichment_type == "address":
            await self._enrich_address(poi)
        elif task.enrichment_type == "accessibility":
            await self._enrich_accessibility(poi)
        elif task.enrichment_type == "photos":
            await self._enrich_photos(poi)
        else:
            logger.warning(f"Unknown enrichment type: {task.enrichment_type}")

        # Update enrichment timestamp
        await self._update_enrichment_timestamp(poi, task.enrichment_type)

    def _is_recently_enriched(self, poi, enrichment_type: str, max_age_hours: int = 24) -> bool:
        """Check if POI was recently enriched for this type."""
        # This would check a metadata field on the POI
        # For now, return False to always enrich
        return False

    async def _update_enrichment_timestamp(self, poi, enrichment_type: str) -> None:
        """Update the enrichment timestamp for a POI."""
        # This would update a metadata field on the POI
        # Implementation depends on the POI model structure
        pass

    async def _enrich_details(self, poi) -> None:
        """Enrich POI with detailed information from Overpass."""
        if not poi.coordinates:
            logger.warning(f"POI {poi.id} has no coordinates for detail enrichment")
            return

        try:
            # Query Overpass for detailed POI information
            details = await self.overpass_client.get_poi_details(
                poi.coordinates.latitude,
                poi.coordinates.longitude,
                radius=50,
            )

            if details:
                # Update POI with enriched data
                updates = {}

                if details.get("name") and not poi.name:
                    updates["name"] = details["name"]

                if details.get("description") and not poi.description:
                    updates["description"] = details["description"]

                if details.get("tags"):
                    # Merge tags
                    existing_tags = set(poi.tags)
                    new_tags = set(details["tags"])
                    updates["tags"] = list(existing_tags | new_tags)

                if details.get("contact"):
                    updates["contact"] = details["contact"]

                if details.get("website") and not poi.website:
                    updates["website"] = details["website"]

                if updates:
                    await self.poi_repository.update(poi.id, updates)
                    logger.info(f"Enriched POI {poi.id} with details: {list(updates.keys())}")

        except Exception as e:
            logger.error(f"Failed to enrich POI {poi.id} details: {e}")

    async def _enrich_opening_hours(self, poi) -> None:
        """Enrich POI with opening hours from Overpass."""
        if not poi.coordinates:
            return

        try:
            opening_hours_data = await self.overpass_client.get_opening_hours(
                poi.coordinates.latitude,
                poi.coordinates.longitude,
            )

            if opening_hours_data:
                opening_hours = OpeningHours.from_osm_format(opening_hours_data)
                await self.poi_repository.update(poi.id, {"opening_hours": opening_hours})
                logger.info(f"Enriched POI {poi.id} with opening hours")

        except Exception as e:
            logger.error(f"Failed to enrich POI {poi.id} opening hours: {e}")

    async def _enrich_address(self, poi) -> None:
        """Enrich POI with detailed address from Nominatim."""
        if not poi.coordinates:
            return

        try:
            address_data = await self.nominatim_client.reverse_geocode(
                poi.coordinates.latitude,
                poi.coordinates.longitude,
            )

            if address_data:
                address = Address(
                    street=address_data.get("road"),
                    city=address_data.get("city") or address_data.get("town") or address_data.get("village"),
                    state=address_data.get("state"),
                    country=address_data.get("country"),
                    postal_code=address_data.get("postcode"),
                    neighborhood=address_data.get("neighbourhood") or address_data.get("suburb"),
                )

                await self.poi_repository.update(poi.id, {"address": address})
                logger.info(f"Enriched POI {poi.id} with address")

        except Exception as e:
            logger.error(f"Failed to enrich POI {poi.id} address: {e}")

    async def _enrich_accessibility(self, poi) -> None:
        """Enrich POI with accessibility information from Overpass."""
        if not poi.coordinates:
            return

        try:
            accessibility_data = await self.overpass_client.get_accessibility(
                poi.coordinates.latitude,
                poi.coordinates.longitude,
            )

            if accessibility_data:
                accessibility = AccessibilityFeatures(
                    wheelchair_accessible=accessibility_data.get("wheelchair", "unknown") == "yes",
                    wheelchair_description=accessibility_data.get("wheelchair:description"),
                    audio_guidance=accessibility_data.get("audio_guidance") == "yes",
                    visual_guidance=accessibility_data.get("visual_guidance") == "yes",
                    tactile_paving=accessibility_data.get("tactile_paving") == "yes",
                    braille_signage=accessibility_data.get("braille") == "yes",
                    hearing_loop=accessibility_data.get("hearing_loop") == "yes",
                    accessible_parking=accessibility_data.get("parking:accessible") == "yes",
                    accessible_toilet=accessibility_data.get("toilet:accessible") == "yes",
                    accessible_entrance=accessibility_data.get("entrance:accessible") == "yes",
                )

                await self.poi_repository.update(poi.id, {"accessibility": accessibility})
                logger.info(f"Enriched POI {poi.id} with accessibility info")

        except Exception as e:
            logger.error(f"Failed to enrich POI {poi.id} accessibility: {e}")

    async def _enrich_photos(self, poi) -> None:
        """Enrich POI with photos (placeholder for future implementation)."""
        # This would integrate with photo services like Flickr, Google Places Photos, etc.
        logger.debug(f"Photo enrichment not yet implemented for POI {poi.id}")

    # High-level methods

    async def enrich_poi(self, poi_id: str, enrichment_types: list[str] = None) -> None:
        """Enqueue enrichment tasks for a specific POI."""
        if enrichment_types is None:
            enrichment_types = ["details", "opening_hours", "address", "accessibility"]

        tasks = [
            POIEnrichmentTask(poi_id=poi_id, enrichment_type=etype, priority=1)
            for etype in enrichment_types
        ]

        await self.enqueue_batch(tasks)

    async def enrich_all_pois(
        self,
        enrichment_types: list[str] = None,
        batch_size: int = 100,
        limit: int | None = None,
    ) -> int:
        """Enqueue enrichment for all POIs. Returns count queued."""
        if enrichment_types is None:
            enrichment_types = ["details", "opening_hours", "address", "accessibility"]

        count = 0
        offset = 0

        while True:
            if limit and count >= limit:
                break

            current_batch = min(batch_size, limit - count) if limit else batch_size
            pois = await self.poi_repository.list(limit=current_batch, offset=offset)

            if not pois:
                break

            tasks = [
                POIEnrichmentTask(poi_id=poi.id, enrichment_type=etype, priority=0)
                for poi in pois
                for etype in enrichment_types
            ]

            await self.enqueue_batch(tasks)
            count += len(pois)
            offset += current_batch

            logger.info(f"Queued enrichment for {count} POIs")

        return count

    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()

    def is_running(self) -> bool:
        """Check if workers are running."""
        return self._running
