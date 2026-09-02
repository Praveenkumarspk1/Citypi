"""
Transit Data Sync Background Tasks

Handles synchronization of GTFS static data and GTFS-RT real-time data
from transit agencies.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime

from ai_smart_city_concierge.domain.repositories.transit_repository import TransitRepository
from ai_smart_city_concierge.infrastructure.external_apis.gtfs_client import GTFSClient

logger = logging.getLogger(__name__)


@dataclass
class TransitSyncTask:
    """Task for transit data synchronization."""
    agency_id: str
    sync_type: str  # 'static', 'realtime', 'vehicle_positions', 'trip_updates', 'service_alerts'
    priority: int = 0
    force_refresh: bool = False


class TransitSyncTask:
    """
    Background task for synchronizing transit data from GTFS feeds.
    """

    def __init__(
        self,
        gtfs_client: GTFSClient,
        transit_repository: TransitRepository,
        max_concurrent: int = 2,
        static_sync_interval_hours: int = 24,
        realtime_sync_interval_seconds: int = 30,
    ):
        self.gtfs_client = gtfs_client
        self.transit_repository = transit_repository
        self.max_concurrent = max_concurrent
        self.static_sync_interval_hours = static_sync_interval_hours
        self.realtime_sync_interval_seconds = realtime_sync_interval_seconds
        self._queue: asyncio.Queue[TransitSyncTask] = asyncio.Queue()
        self._running = False
        self._worker_tasks: list[asyncio.Task] = []
        self._scheduled_tasks: dict[str, asyncio.Task] = {}

    async def start(self) -> None:
        """Start the transit sync workers and scheduled tasks."""
        if self._running:
            return

        self._running = True
        logger.info("Starting transit sync workers")

        # Start workers
        for i in range(self.max_concurrent):
            task = asyncio.create_task(self._worker(f"transit-sync-worker-{i}"))
            self._worker_tasks.append(task)

        # Start scheduled sync tasks
        await self._start_scheduled_syncs()

    async def stop(self) -> None:
        """Stop the transit sync workers and scheduled tasks."""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping transit sync workers")

        # Cancel scheduled tasks
        for task in self._scheduled_tasks.values():
            task.cancel()
        await asyncio.gather(*self._scheduled_tasks.values(), return_exceptions=True)
        self._scheduled_tasks.clear()

        # Stop workers
        await self._queue.join()

        for task in self._worker_tasks:
            task.cancel()

        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()

    async def enqueue(self, task: TransitSyncTask) -> None:
        """Add a transit sync task to the queue."""
        await self._queue.put(task)

    async def enqueue_batch(self, tasks: list[TransitSyncTask]) -> None:
        """Add multiple transit sync tasks to the queue."""
        for task in tasks:
            await self._queue.put(task)

    async def _worker(self, worker_name: str) -> None:
        """Worker coroutine that processes transit sync tasks."""
        logger.info(f"{worker_name} started")

        while self._running:
            try:
                task = await asyncio.wait_for(self._queue.get(), timeout=1.0)

                try:
                    await self._process_task(task)
                except Exception as e:
                    logger.error(f"{worker_name} error processing task {task.agency_id}: {e}")
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

    async def _start_scheduled_syncs(self) -> None:
        """Start scheduled sync tasks for all known agencies."""
        agencies = await self.transit_repository.get_all_agencies()

        for agency in agencies:
            # Schedule static data sync
            static_task = asyncio.create_task(
                self._scheduled_static_sync(agency.id)
            )
            self._scheduled_tasks[f"static-{agency.id}"] = static_task

            # Schedule real-time data sync
            realtime_task = asyncio.create_task(
                self._scheduled_realtime_sync(agency.id)
            )
            self._scheduled_tasks[f"realtime-{agency.id}"] = realtime_task

        logger.info(f"Started scheduled syncs for {len(agencies)} agencies")

    async def _scheduled_static_sync(self, agency_id: str) -> None:
        """Periodically sync static GTFS data for an agency."""
        while self._running:
            try:
                await self.enqueue(TransitSyncTask(
                    agency_id=agency_id,
                    sync_type="static",
                    priority=0,
                ))
                logger.debug(f"Scheduled static sync for agency {agency_id}")
            except Exception as e:
                logger.error(f"Error scheduling static sync for {agency_id}: {e}")

            await asyncio.sleep(self.static_sync_interval_hours * 3600)

    async def _scheduled_realtime_sync(self, agency_id: str) -> None:
        """Periodically sync real-time GTFS data for an agency."""
        while self._running:
            try:
                await self.enqueue(TransitSyncTask(
                    agency_id=agency_id,
                    sync_type="realtime",
                    priority=1,
                ))
            except Exception as e:
                logger.error(f"Error scheduling realtime sync for {agency_id}: {e}")

            await asyncio.sleep(self.realtime_sync_interval_seconds)

    async def _process_task(self, task: TransitSyncTask) -> None:
        """Process a single transit sync task."""
        logger.debug(f"Syncing transit data for agency {task.agency_id} ({task.sync_type})")

        if task.sync_type == "static":
            await self._sync_static_data(task.agency_id, task.force_refresh)
        elif task.sync_type == "realtime":
            await self._sync_realtime_data(task.agency_id)
        elif task.sync_type == "vehicle_positions":
            await self._sync_vehicle_positions(task.agency_id)
        elif task.sync_type == "trip_updates":
            await self._sync_trip_updates(task.agency_id)
        elif task.sync_type == "service_alerts":
            await self._sync_service_alerts(task.agency_id)
        else:
            logger.warning(f"Unknown sync type: {task.sync_type}")

    async def _sync_static_data(self, agency_id: str, force_refresh: bool = False) -> None:
        """Sync static GTFS data (routes, stops, trips, calendar)."""
        try:
            # Check if sync is needed
            if not force_refresh:
                last_sync = await self.transit_repository.get_last_static_sync(agency_id)
                if last_sync and (datetime.utcnow() - last_sync).total_seconds() < self.static_sync_interval_hours * 3600:
                    logger.debug(f"Static data for {agency_id} is recent, skipping")
                    return

            # Fetch static GTFS data
            static_data = await self.gtfs_client.fetch_static_feed(agency_id)

            if not static_data:
                logger.warning(f"No static data received for agency {agency_id}")
                return

            # Process and store agencies
            if static_data.get("agency"):
                for agency_data in static_data["agency"]:
                    await self.transit_repository.upsert_agency(agency_data)

            # Process and store routes
            if static_data.get("routes"):
                for route_data in static_data["routes"]:
                    await self.transit_repository.upsert_route(route_data)

            # Process and store stops
            if static_data.get("stops"):
                for stop_data in static_data["stops"]:
                    await self.transit_repository.upsert_stop(stop_data)

            # Process and store trips
            if static_data.get("trips"):
                for trip_data in static_data["trips"]:
                    await self.transit_repository.upsert_trip(trip_data)

            # Process and store stop times
            if static_data.get("stop_times"):
                for stop_time_data in static_data["stop_times"]:
                    await self.transit_repository.upsert_stop_time(stop_time_data)

            # Process and store calendar
            if static_data.get("calendar"):
                for calendar_data in static_data["calendar"]:
                    await self.transit_repository.upsert_calendar(calendar_data)

            # Update last sync timestamp
            await self.transit_repository.update_last_static_sync(agency_id, datetime.utcnow())

            logger.info(f"Completed static sync for agency {agency_id}")

        except Exception as e:
            logger.error(f"Failed to sync static data for {agency_id}: {e}")

    async def _sync_realtime_data(self, agency_id: str) -> None:
        """Sync all real-time GTFS data for an agency."""
        await asyncio.gather(
            self._sync_vehicle_positions(agency_id),
            self._sync_trip_updates(agency_id),
            self._sync_service_alerts(agency_id),
            return_exceptions=True,
        )

    async def _sync_vehicle_positions(self, agency_id: str) -> None:
        """Sync real-time vehicle positions."""
        try:
            vehicle_positions = await self.gtfs_client.fetch_vehicle_positions(agency_id)

            if vehicle_positions:
                for vehicle in vehicle_positions:
                    await self.transit_repository.upsert_vehicle_position(vehicle)

                logger.debug(f"Synced {len(vehicle_positions)} vehicle positions for {agency_id}")

        except Exception as e:
            logger.error(f"Failed to sync vehicle positions for {agency_id}: {e}")

    async def _sync_trip_updates(self, agency_id: str) -> None:
        """Sync real-time trip updates (delays, cancellations, etc.)."""
        try:
            trip_updates = await self.gtfs_client.fetch_trip_updates(agency_id)

            if trip_updates:
                for update in trip_updates:
                    await self.transit_repository.upsert_trip_update(update)

                logger.debug(f"Synced {len(trip_updates)} trip updates for {agency_id}")

        except Exception as e:
            logger.error(f"Failed to sync trip updates for {agency_id}: {e}")

    async def _sync_service_alerts(self, agency_id: str) -> None:
        """Sync real-time service alerts."""
        try:
            alerts = await self.gtfs_client.fetch_service_alerts(agency_id)

            if alerts:
                for alert in alerts:
                    await self.transit_repository.upsert_service_alert(alert)

                logger.debug(f"Synced {len(alerts)} service alerts for {agency_id}")

        except Exception as e:
            logger.error(f"Failed to sync service alerts for {agency_id}: {e}")

    # High-level methods

    async def sync_agency(self, agency_id: str, sync_types: list[str] = None) -> None:
        """Enqueue sync tasks for a specific agency."""
        if sync_types is None:
            sync_types = ["static", "realtime"]

        tasks = [
            TransitSyncTask(agency_id=agency_id, sync_type=stype, priority=1)
            for stype in sync_types
        ]

        await self.enqueue_batch(tasks)

    async def sync_all_agencies(self, sync_types: list[str] = None) -> int:
        """Enqueue sync for all agencies. Returns count queued."""
        if sync_types is None:
            sync_types = ["static", "realtime"]

        agencies = await self.transit_repository.get_all_agencies()
        count = 0

        for agency in agencies:
            tasks = [
                TransitSyncTask(agency_id=agency.id, sync_type=stype, priority=0)
                for stype in sync_types
            ]
            await self.enqueue_batch(tasks)
            count += 1

        logger.info(f"Queued sync for {count} agencies")
        return count

    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()

    def is_running(self) -> bool:
        """Check if workers are running."""
        return self._running
